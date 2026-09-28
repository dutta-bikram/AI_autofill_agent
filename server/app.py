import os
import base64
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import settings
from memory.profile_store import ProfileStore, UserProfile
from memory.vector_store import RAGMemoryStore
from memory.document_loader import DocumentLoader
from browser.controller import BrowserController
from agent.autofill_engine import AutofillEngine, AutofillPlan, FormFillDecision
from agent.llm_provider import get_llm_provider
from server.test_forms import JOB_APPLICATION_HTML

# Initialize shared instances
app = FastAPI(title="AI Autofill Agent", version="1.0.0")

profile_store = ProfileStore()
vector_store = RAGMemoryStore()
doc_loader = DocumentLoader(vector_store)

# Load existing sample documents on startup
if settings.DOCUMENTS_DIR.exists():
    doc_loader.load_directory(settings.DOCUMENTS_DIR)

# Shared browser controller and engine
browser_controller: Optional[BrowserController] = None
autofill_engine: Optional[AutofillEngine] = None
active_plan: Optional[AutofillPlan] = None

def get_engine() -> AutofillEngine:
    global browser_controller, autofill_engine
    if browser_controller is None:
        browser_controller = BrowserController(headless=settings.HEADLESS_BROWSER)
    if autofill_engine is None:
        autofill_engine = AutofillEngine(
            profile_store=profile_store,
            vector_store=vector_store,
            llm_provider=get_llm_provider(),
            browser_controller=browser_controller
        )
    return autofill_engine

# Request Models
class ScanRequest(BaseModel):
    url: str

class FillRequest(BaseModel):
    plan: AutofillPlan

class DocumentAddRequest(BaseModel):
    title: str
    content: str

class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = 3

# Static files setup
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "css").mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "js").mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>AI Autofill Agent Dashboard loading...</h1>")

@app.get("/demo-form", response_class=HTMLResponse)
async def serve_demo_form():
    return HTMLResponse(JOB_APPLICATION_HTML)

# Profile Endpoints
@app.get("/api/profile")
async def get_profile():
    return profile_store.profile.model_dump()

@app.post("/api/profile")
async def update_profile(updates: Dict[str, Any]):
    updated = profile_store.update(updates)
    return {"status": "success", "profile": updated.model_dump()}

# RAG & Document Endpoints
@app.get("/api/documents")
async def get_documents():
    docs = []
    if settings.DOCUMENTS_DIR.exists():
        for p in settings.DOCUMENTS_DIR.glob("*"):
            if p.is_file():
                docs.append({
                    "filename": p.name,
                    "size_kb": round(p.stat().st_size / 1024, 1),
                    "path": str(p)
                })
    return {
        "documents": docs,
        "total_indexed_chunks": len(vector_store.chunks)
    }

@app.post("/api/documents")
async def add_document(req: DocumentAddRequest):
    doc_path = settings.DOCUMENTS_DIR / f"{req.title.replace(' ', '_').lower()}.md"
    doc_path.write_text(req.content, encoding="utf-8")
    count = doc_loader.load_file(doc_path)
    return {"status": "success", "filename": doc_path.name, "chunks_added": count}

@app.post("/api/rag/query")
async def query_rag(req: RAGQueryRequest):
    results = vector_store.query(req.query, top_k=req.top_k)
    return {"query": req.query, "results": results}

# Agent Form Automation Endpoints
@app.post("/api/agent/scan")
async def agent_scan(req: ScanRequest):
    global active_plan
    engine = get_engine()
    try:
        active_plan = await engine.analyze_and_plan(url=req.url)
        return {
            "status": "success",
            "plan": active_plan.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agent/fill")
async def agent_fill(req: FillRequest):
    global active_plan
    engine = get_engine()
    try:
        active_plan = req.plan
        result = await engine.execute_plan(req.plan)
        return {
            "status": "success",
            "execution_result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agent/submit")
async def agent_submit():
    engine = get_engine()
    try:
        success = await engine.submit_page()
        return {"status": "success", "submitted": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agent/screenshot")
async def get_screenshot():
    engine = get_engine()
    if not engine.browser_controller.page:
        return {"status": "error", "message": "Browser page not active"}
    try:
        temp_img = settings.DATA_DIR / "temp_screenshot.png"
        await engine.browser_controller.take_screenshot(str(temp_img))
        with open(temp_img, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return {"status": "success", "screenshot_base64": f"data:image/png;base64,{encoded}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/agent/close")
async def close_browser():
    global browser_controller, autofill_engine
    if browser_controller:
        await browser_controller.close()
        browser_controller = None
        autofill_engine = None
    return {"status": "success", "message": "Browser closed"}
