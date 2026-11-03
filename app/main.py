from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from .config import settings
from .database import Base, engine, get_db
from .models import WorkflowRun
from .services import extract_document_text
from .workflow import execute_enquiry

Base.metadata.create_all(bind=engine)
app = FastAPI(title=settings.app_name, version="1.0.0", description="API-driven business enquiry automation with execution tracking.")

class EnquiryRequest(BaseModel):
    message: str = Field(min_length=3, max_length=10000)
    customer_name: str = Field(default="", max_length=200)
    email: str = Field(default="", max_length=320)
    source: str = Field(default="api", max_length=100)

def serialize(run: WorkflowRun):
    return {
        "id": run.id, "status": run.status, "source": run.source,
        "customer_name": run.customer_name, "email": run.email,
        "category": run.category, "priority": run.priority,
        "summary": run.summary, "steps": run.steps,
        "error": run.error, "created_at": run.created_at,
        "completed_at": run.completed_at,
    }

@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name}

@app.post("/webhooks/enquiry")
async def receive_enquiry(request: EnquiryRequest, db: Session = Depends(get_db)):
    run = WorkflowRun(source=request.source, customer_name=request.customer_name,
                      email=request.email, payload={"message": request.message})
    db.add(run)
    db.commit()
    db.refresh(run)
    return serialize(await execute_enquiry(db, run))

@app.post("/documents/process")
async def process_document(file: UploadFile = File(...), customer_name: str = Form(default=""),
                           db: Session = Depends(get_db)):
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds 10 MB limit")
    try:
        extracted = extract_document_text(file.filename or "document.txt", content)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not extracted:
        raise HTTPException(status_code=422, detail="No extractable text found in document")
    run = WorkflowRun(source="document_upload", customer_name=customer_name,
                      payload={"message": extracted, "filename": file.filename})
    db.add(run)
    db.commit()
    db.refresh(run)
    return serialize(await execute_enquiry(db, run))

@app.get("/runs")
def list_runs(limit: int = 20, db: Session = Depends(get_db)):
    if not 1 <= limit <= 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")
    return [serialize(run) for run in db.query(WorkflowRun).order_by(WorkflowRun.id.desc()).limit(limit).all()]

@app.get("/runs/{run_id}")
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.get(WorkflowRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    return serialize(run)
