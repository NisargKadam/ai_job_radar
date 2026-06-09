from app.agent.nodes import log_event
from app.agent.state import AgentState
from app.db.models import Candidate, Run, Sent
from app.db.session import SessionLocal
from app.delivery.base import get_channel
from app.delivery.formatting import format_digest, format_individual
from app.schemas import CandidateOut, SendResultOut
from app.settings_service import get_settings_dict


def _build_units(cands: list[CandidateOut], individual: bool):
    """Returns a list of (label, message, candidate_id|None) to send per group."""
    if individual:
        return [(c.permalink, format_individual(c), c.id) for c in cands]
    return [("digest", format_digest(cands), None)]


def _dispatch(cands, ids, settings, dry, run_id) -> SendResultOut:
    group_ids = [str(g) for g in settings.get("group_ids", [])]
    if not cands:
        return SendResultOut(sent=0, failed=0, dry_run=dry, details=["no candidates to send"])

    units = _build_units(cands, bool(settings.get("send_individual")))
    details: list[str] = []

    if dry:
        for g in group_ids or ["<no groups configured>"]:
            for label, _msg, _cid in units:
                details.append(f"[dry-run] would send [{label}] -> {g}")
        details.append("----- message preview -----")
        details.append(units[0][1])
        log_event(run_id, f"[dry-run] would send {len(units)} message(s) to {len(group_ids)} group(s)")
        return SendResultOut(sent=0, failed=0, dry_run=True, details=details)

    if not group_ids:
        return SendResultOut(sent=0, failed=0, dry_run=False, details=["no group_ids configured"])

    channel = get_channel(settings)
    sent = failed = 0
    with SessionLocal() as s:
        for g in group_ids:
            for label, msg, cid in units:
                res = channel.send(g, msg)
                if res.ok:
                    sent += 1
                    s.add(Sent(candidate_id=cid, channel=channel.name, group_id=g, message=msg))
                    details.append(f"sent [{label}] -> {g}")
                else:
                    failed += 1
                    details.append(f"FAILED [{label}] -> {g}: {res.error}")
        if sent > 0:
            for cid in ids:
                row = s.get(Candidate, cid)
                if row:
                    row.status = "sent"
        s.commit()
    log_event(run_id, f"delivered: sent={sent} failed={failed}")
    return SendResultOut(sent=sent, failed=failed, dry_run=False, details=details)


def deliver(state: AgentState) -> dict:
    """Graph node for the auto_send path. Candidates were just persisted as
    pending by review_gate; load them by permalink and send."""
    selected = state.get("selected", [])
    settings = state.get("settings", {})
    run_id = state.get("run_id")
    dry = state.get("dry_run", True)

    permalinks = [c["post"].permalink for c in selected]
    with SessionLocal() as s:
        rows = (
            s.query(Candidate).filter(Candidate.permalink.in_(permalinks)).all()
            if permalinks
            else []
        )
        cands = [CandidateOut.model_validate(r) for r in rows]
        ids = [r.id for r in rows]

    result = _dispatch(cands, ids, settings, dry, run_id)

    if run_id is not None:
        with SessionLocal() as s:
            run = s.get(Run, run_id)
            if run:
                # count jobs delivered, not raw (group × message) send operations
                run.sent_count = len(ids) if result.sent > 0 else 0
                s.commit()
    return {}


def deliver_approved() -> SendResultOut:
    """Standalone /send path: send all approved candidates now."""
    settings = get_settings_dict()
    with SessionLocal() as s:
        rows = s.query(Candidate).filter_by(status="approved").all()
        cands = [CandidateOut.model_validate(r) for r in rows]
        ids = [r.id for r in rows]
    return _dispatch(cands, ids, settings, settings["dry_run"], run_id=None)
