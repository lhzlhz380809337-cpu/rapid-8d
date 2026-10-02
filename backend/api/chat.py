"""Chat API — core conversation endpoint + step management + output generation."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Literal
Step = Literal["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]
from backend.config import get_config
from backend.conversation.engine import ConversationEngine, get_step_focus
from backend.api.session import get_user_project_manager

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    project_id: str
    message: str = Field(min_length=1, max_length=16000)
    step: Step | None = None


class ChatResponse(BaseModel):
    reply: str
    current_step: str
    step_status: str
    project_id: str


class SwitchStepRequest(BaseModel):
    project_id: str
    step: Step


class ContextNotesRequest(BaseModel):
    project_id: str
    step: Step
    notes: str = Field(max_length=50000)


class GenerateOutputRequest(BaseModel):
    project_id: str
    step: Step


class GenerateOutputResponse(BaseModel):
    output: str = Field(max_length=100000)
    suggestions: list[str]


class ConfirmOutputRequest(BaseModel):
    project_id: str
    step: Step
    output: str = Field(max_length=100000)


class FocusResponse(BaseModel):
    step: Step
    focus: str


# ─── Chat ──────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, request: Request):
    config = get_config()
    pm = get_user_project_manager(request)
    engine = ConversationEngine(config, pm=pm)

    try:
        result = engine.process_message(req.project_id, req.message, step=req.step)
    except HTTPException:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=502, detail="LLM call failed")

    return ChatResponse(**result)


# ─── Step navigation ───────────────────────────────────────────────

@router.put("/chat/switch-step")
def switch_step(req: SwitchStepRequest, request: Request):
    config = get_config()
    pm = get_user_project_manager(request)
    engine = ConversationEngine(config, pm=pm)
    engine.jump_to_step(req.project_id, req.step)
    return {"status": "ok", "current_step": req.step}


# ─── Context notes ─────────────────────────────────────────────────

@router.put("/project/{project_id}/context/{step}")
def save_context_notes(project_id: str, step: Step, req: ContextNotesRequest, request: Request):
    config = get_config()
    pm = get_user_project_manager(request)
    engine = ConversationEngine(config, pm=pm)
    engine.update_context_notes(project_id, step, req.notes)
    return {"status": "ok"}


@router.get("/project/{project_id}/context/{step}")
def get_context_notes(project_id: str, step: Step, request: Request):
    config = get_config()
    pm = get_user_project_manager(request)
    engine = ConversationEngine(config, pm=pm)
    notes = engine.get_context_notes(project_id, step)
    return {"notes": notes}


# ─── Review context ──────────────────────────────────────────────────

class ReviewContextResponse(BaseModel):
    findings: list[dict]


@router.post("/project/{project_id}/review-context/{step}", response_model=ReviewContextResponse)
def review_context(project_id: str, step: Step, request: Request):
    config = get_config()
    pm = get_user_project_manager(request)
    engine = ConversationEngine(config, pm=pm)

    try:
        result = engine.review_context(project_id, step)
    except HTTPException:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=502, detail="Review context failed")

    return ReviewContextResponse(**result)


# ─── Output generation ─────────────────────────────────────────────

@router.post("/project/{project_id}/generate-output/{step}", response_model=GenerateOutputResponse)
def generate_output(project_id: str, step: Step, request: Request):
    config = get_config()
    pm = get_user_project_manager(request)
    engine = ConversationEngine(config, pm=pm)

    try:
        result = engine.generate_step_output(project_id, step)
    except HTTPException:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=502, detail="Output generation failed")

    return GenerateOutputResponse(**result)


@router.put("/project/{project_id}/confirm-output/{step}")
def confirm_output(project_id: str, step: Step, req: ConfirmOutputRequest, request: Request):
    config = get_config()
    pm = get_user_project_manager(request)
    engine = ConversationEngine(config, pm=pm)
    engine.confirm_output(project_id, step, req.output)
    return {"status": "ok"}


# ─── Focus questions ───────────────────────────────────────────────

@router.get("/project/{project_id}/focus/{step}", response_model=FocusResponse)
def get_focus(project_id: str, step: Step):
    return FocusResponse(step=step, focus=get_step_focus(step))


# ─── WebSocket ─────────────────────────────────────────────────────

@router.websocket("/ws/{project_id}")
async def chat_websocket(websocket: WebSocket, project_id: str):
    await websocket.close(code=1008, reason="Use authenticated HTTP API")
