from datetime import datetime, timezone
from sqlalchemy.orm import Session
from .models import WorkflowRun
from .services import classify_enquiry, notify_webhook

async def execute_enquiry(db: Session, run: WorkflowRun) -> WorkflowRun:
    run.status = "running"
    db.commit()
    steps = []
    try:
        text = str(run.payload.get("message", ""))
        steps.append({"name": "receive_enquiry", "status": "completed"})
        result = classify_enquiry(text)
        run.category = result["category"]
        run.priority = result["priority"]
        run.email = run.email or result["email"]
        run.summary = result["summary"]
        steps.append({"name": "classify_enquiry", "status": "completed", "output": result})
        route = "priority_queue" if run.priority == "high" else f"{run.category}_queue"
        steps.append({"name": "route_request", "status": "completed", "output": {"queue": route}})
        try:
            delivery = await notify_webhook({
                "event": "enquiry.processed", "run_id": run.id,
                "category": run.category, "priority": run.priority,
                "queue": route, "email": run.email, "summary": run.summary,
            })
            steps.append({"name": "notify_webhook", "status": "completed" if delivery.get("sent") else "skipped", "output": delivery})
        except Exception as exc:
            steps.append({"name": "notify_webhook", "status": "failed", "error": str(exc)})
        run.steps = steps
        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
    except Exception as exc:
        run.steps = steps + [{"name": "workflow", "status": "failed", "error": str(exc)}]
        run.status = "failed"
        run.error = str(exc)
        run.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(run)
    return run
