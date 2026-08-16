import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.api.activity import router as activity_router
from backend.api.automation import router as automation_router
from backend.api.chat import router as chat_router
from backend.api.memory import router as memory_router
from backend.api.permissions import router as permissions_router
from backend.api.persona import router as persona_router
from backend.api.reminders import router as reminders_router
from backend.api.settings import router as settings_router
from backend.api.skills import router as skills_router
from backend.api.system import router as system_router
from backend.api.tasks import router as tasks_router
from backend.api.tools import router as tools_router
from backend.api.vision import router as vision_router
from backend.api.voice import router as voice_router
from backend.api.agent import router as agent_router
from backend.api.git import router as git_router
from backend.api.research import router as research_router
from backend.services.ai_service import AIService
from backend.services.automation_service import AutomationService
from backend.services.memory_service import MemoryService
from backend.services.notification_service import NotificationService
from backend.services.persona_service import persona_service
from backend.services.system_service import SystemService
from backend.services.tool_service import ToolService
from backend.services.voice_service import VoiceManager
from backend.services.ws_manager import ws_manager
from communications.calls.manager import CallManager
from config.settings import get_settings
from generation.image.manager import ImageGenerationManager
from generation.video.manager import VideoGenerationManager
from memory.manager import MemoryManager
from permissions.manager import PermissionManager
from safety import SafetyCategory, classify_request, get_confirmation_manager
from safety.activity import get_activity_logger
from skills.executor import SkillExecutor
from skills.manager import SkillManager
from skills.registry import SkillRegistry
from tools.registry import build_registry
from vision.gesture.detector import GestureDetector
from vision.manager import vision_manager
from voice.tts_manager import TTSManager

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(f"{settings.logs_dir}/jarvis.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("jarvis")

Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
Path(settings.logs_dir).mkdir(parents=True, exist_ok=True)

vector_dir = Path(settings.data_dir) / "vector_store" if settings.vector_memory_enabled else None
memory_manager = MemoryManager(settings.db_path, vector_dir=vector_dir)
settings.apply_db_overrides(memory_manager.store.get_all_settings())
tool_registry = build_registry(settings.db_path)
tts_manager = TTSManager(settings)
skill_registry = SkillRegistry()
skill_registry.load()
skill_manager = SkillManager(skill_registry)
permission_manager = PermissionManager(Path(settings.data_dir) / "permissions.json")
activity_logger = get_activity_logger(Path(settings.logs_dir) / "activity.jsonl")
skill_executor = SkillExecutor(skill_registry, permission_manager)
ai_service = AIService(
    memory_manager,
    tts_manager,
    tool_registry,
    skill_registry=skill_registry,
    permission_manager=permission_manager,
)
voice_service = VoiceManager(memory_manager, ai_service)
memory_service = MemoryService(memory_manager)
tool_service = ToolService(tool_registry)
system_service = SystemService()
notification_service = NotificationService()
image_mgr = ImageGenerationManager(settings)
video_mgr = VideoGenerationManager(settings)
call_mgr = CallManager(settings)
gesture_detector = GestureDetector(settings)

research_manager = None


def get_research_manager_instance():
    global research_manager
    if research_manager is None:
        from research.manager import ResearchManager
        research_manager = ResearchManager(
            ai_provider=ai_service,
            max_sources=getattr(settings, "research_max_sources", 20),
            on_event=ws_manager.broadcast,
        )
    return research_manager

_agent_manager = None


def get_agent_manager_instance():
    global _agent_manager
    if _agent_manager is None:
        from agent.manager import get_agent_manager
        _agent_manager = get_agent_manager(
            tool_execute=lambda name, confirmed=False, **kwargs: tool_registry.execute(name, confirmed=confirmed, **kwargs),
            memory=memory_manager,
            permission_manager=permission_manager,
        )
    return _agent_manager


async def _automation_command(cmd: str) -> dict:
    try:
        result = await tool_registry.execute("terminal", arguments={"command": cmd})
        if hasattr(result, "_data"):
            return result._data
        return {"success": True, "result": str(result)}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


automation_service = AutomationService(
    memory_manager,
    speak_callback=lambda text: voice_service.speak(text) if voice_service._started else voice_service.test_voice(text),
    command_callback=_automation_command,
)

task_manager = None


def get_task_manager_instance():
    global task_manager
    if task_manager is None:
        from automation.manager import TaskManager
        task_manager = TaskManager(
            memory_manager=memory_manager,
            tool_execute=lambda name, confirmed=False, **kwargs: tool_registry.execute(name, confirmed=confirmed, **kwargs),
            ai_service=ai_service,
            tts_callback=lambda text: voice_service.speak(text) if voice_service._started else None,
        )
    return task_manager


async def _execute_automation_handler(automation_id: str):
    for automation in memory_manager.store.get_automations():
        if automation.get("id") == automation_id:
            await automation_service._fire(automation)
            return {"success": True, "message": f"Automation '{automation.get('name')}' executed."}
    return {"success": False, "error": "Automation not found."}


tool_registry.register_handler(
    "execute_automation",
    "Manually trigger an automation by its ID.",
    {
        "type": "object",
        "properties": {"automation_id": {"type": "string"}},
        "required": ["automation_id"],
    },
    _execute_automation_handler,
)


async def _tts_broadcast(event: str, text: str):
    await ws_manager.broadcast(event, {"text": text})


async def _tts_first_audio():
    await ws_manager.broadcast("tts_first_audio", {})


tts_manager.on_event(_tts_broadcast)
tts_manager.on_first_audio(_tts_first_audio)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("JARVIS 2.0 starting up...")
    await persona_service.apply_persona_on_startup()
    await tts_manager.start()
    await voice_service.start()
    await automation_service.start()
    _task_mgr = get_task_manager_instance()
    await _task_mgr.start()
    _research_mgr = get_research_manager_instance()
    vision_manager.enabled = settings.vision_enabled
    vision_manager.set_broadcast(ws_manager.broadcast)
    if settings.vision_provider:
        try:
            from vision.providers.base import VisionProvider
            provider_mod = __import__(f"vision.providers.{settings.vision_provider}", fromlist=["VisionProvider"])
            provider = getattr(provider_mod, "VisionProvider", None)
            if provider:
                vision_manager.register_provider(provider())
        except Exception as exc:
            logger.warning("Failed to load vision provider %s: %s", settings.vision_provider, exc)
    notification_service.push("JARVIS is online and ready.", "success")
    logger.info("JARVIS 2.0 ready.")
    yield
    logger.info("JARVIS 2.0 shutting down...")
    await _task_mgr.stop()
    await automation_service.stop()
    await voice_service.stop()
    await tts_manager.stop()


app = FastAPI(title="JARVIS 2.0", version="2.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?|tauri://localhost|app://localhost",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")
app.include_router(voice_router, prefix="/api")
app.include_router(system_router, prefix="/api")
app.include_router(memory_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(tools_router, prefix="/api")
app.include_router(automation_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
app.include_router(reminders_router, prefix="/api")
app.include_router(persona_router, prefix="/api")
app.include_router(skills_router, prefix="/api")
app.include_router(permissions_router, prefix="/api")
app.include_router(activity_router, prefix="/api")
app.include_router(agent_router, prefix="/api")
app.include_router(git_router, prefix="/api")
app.include_router(vision_router, prefix="/api")
app.include_router(research_router, prefix="/api")


# ---------------------------------------------------------------- health
@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "assistant": settings.assistant_name,
        "providers": {
            "groq": await ai_service.providers["groq"].health_check(),
            "local_llm": await ai_service.providers["local_llm"].health_check(),
            "gemini": await ai_service.providers["gemini"].health_check(),
            "openrouter": await ai_service.providers["openrouter"].health_check(),
        },
        "database": {"status": "online"},
        "websocket": {"status": "online", "connections": ws_manager.count},
        "tts": {"status": "available" if tts_manager.is_available() else "unavailable", "backend": tts_manager.backend, "engine": tts_manager.engine},
        "voice": {"status": "available" if voice_service.is_available() else "unavailable", "mic": voice_service.mic_available},
        "image": await image_mgr.health(),
        "video": await video_mgr.health(),
        "gestures": {"status": "active" if gesture_detector.active else "inactive"},
        "calls": {"status": "available" if call_mgr.is_available() else "unavailable"},
        "vision": vision_manager.status(),
    }


# ---------------------------------------------------------------- history
@app.get("/api/history")
async def get_history(conversation_id: str = None):
    if conversation_id:
        return memory_manager.get_history(conversation_id)
    convs = memory_manager.get_conversations(limit=1)
    if convs:
        return memory_manager.get_history(convs[0]["id"])
    return []


@app.delete("/api/history")
async def clear_history():
    conv_id = memory_manager.reset_conversation()
    ai_service._current_conv = conv_id
    return {"status": "cleared", "conversation_id": conv_id}


# ---------------------------------------------------------------- notifications
@app.get("/api/notifications")
async def get_notifications(limit: int = 20):
    return notification_service.recent(limit)


# ---------------------------------------------------------------- safety
class SafetyCheckRequest(BaseModel):
    message: str


class SafetyCheckResponse(BaseModel):
    category: str
    confidence: float
    safe: bool
    subcategory: str | None = None
    severity: str = "low"
    is_exception: bool = False


class ConfirmationResponse(BaseModel):
    request_id: str
    confirmed: bool
    message: str


@app.post("/api/safety/check", response_model=SafetyCheckResponse)
async def safety_check(request: SafetyCheckRequest):
    classification = classify_request(request.message)
    return SafetyCheckResponse(
        category=classification.category.value,
        confidence=classification.confidence,
        safe=classification.category == SafetyCategory.SAFE,
        subcategory=classification.subcategory,
        severity=classification.severity.value,
        is_exception=classification.is_exception,
    )


@app.post("/api/safety/confirm", response_model=ConfirmationResponse)
async def safety_confirm(request: ConfirmationResponse):
    manager = get_confirmation_manager()
    success = manager.confirm(request.request_id, request.confirmed)
    message = "Confirmation recorded." if success else "Confirmation request not found."
    return ConfirmationResponse(
        request_id=request.request_id,
        confirmed=request.confirmed,
        message=message,
    )


@app.get("/api/safety/pending")
async def safety_pending():
    manager = get_confirmation_manager()
    pending = manager.get_pending_requests()
    return {
        "requests": [
            {
                "id": r.id,
                "tool": r.tool_name,
                "arguments": r.arguments,
                "summary": r.summary,
                "risk_level": r.risk_level,
                "timestamp": r.timestamp.isoformat(),
            }
            for r in pending
        ]
    }


# ---------------------------------------------------------------- diagnostics
@app.get("/api/system/diagnostics")
async def system_diagnostics():

    provider_status = await ai_service.health()
    active = ai_service._select_provider()
    return {
        "version": app.version,
        "assistant": settings.assistant_name,
        "user": settings.user_name,
        "uptime_seconds": await system_service.system_uptime_seconds(),
        "os": {
            "name": await system_service.os_name(),
            "kernel": await system_service.kernel_release(),
            "hostname": await system_service.hostname(),
        },
        "providers": provider_status,
        "active_provider": active.name if active else None,
        "provider_count": len(provider_status),
        "tools": len(tool_registry.names()),
        "database": await system_service.check_database(settings.db_path),
        "websocket_clients": ws_manager.count,
        "websocket": system_service.check_websocket(ws_manager),
        "tts": {
            "available": tts_manager.is_available(),
            "backend": tts_manager.backend,
            "engine": tts_manager.engine,
            "voice": settings.tts_voice,
            "voices": len(tts_manager.voice_catalog()),
        },
        "pipewire": await system_service.check_pipewire(),
        "voice": {
            "initialized": voice_service.initialized,
            "mic_available": voice_service.mic_available,
            "tts_available": voice_service.tts_available,
        },
        "memory": {"conversations": len(memory_manager.get_conversations(limit=1000))},
        "image": await image_mgr.health(),
        "video": await video_mgr.health(),
        "gestures": {"active": gesture_detector.active, "available": gesture_detector.is_available()},
        "calls": {"available": call_mgr.is_available()},
        "vision": vision_manager.status(),
        "python": __import__("sys").version.split()[0],
    }


# ---------------------------------------------------------------- websocket
@app.websocket("/ws/jarvis")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
            except (json.JSONDecodeError, AttributeError):
                payload = {"event": "chat", "data": {"message": raw}}

            event = payload.get("event", "") if isinstance(payload, dict) else ""
            data = payload.get("data", {}) if isinstance(payload, dict) else {}

            if event == "chat":
                message = data.get("message", "")
                if not message.strip():
                    continue
                gen = ai_service.process_message(message, conversation_id=data.get("conversation_id"))
                async for ev in gen:
                    if ev["event"].startswith("_"):
                        continue
                    await ws_manager.broadcast(ev["event"], ev["data"])
            elif event == "stop":
                await ws_manager.send(websocket, "stop_ack")
            elif event == "clear_history":
                conv_id = memory_manager.reset_conversation()
                ai_service._current_conv = conv_id
                await ws_manager.broadcast("history_cleared", {"conversation_id": conv_id})
            elif event == "tool_confirm":
                ai_service.confirm_tool(bool(data.get("confirmed", False)))
            elif event == "new_conversation":
                conv_id = memory_manager.ensure_conversation(None)
                ai_service._current_conv = conv_id
                await ws_manager.send(websocket, "conversation_created", {"conversation_id": conv_id})
            elif event == "get_system_stats":
                await ws_manager.send(websocket, "system_stats", system_service.full_stats())
            elif event == "task_create":
                mgr = get_task_manager_instance()
                task = await mgr.create_task(
                    description=data.get("description", ""),
                    task_type=data.get("task_type", "general"),
                    auto_execute=data.get("auto_execute", False),
                    context=data.get("context"),
                )
                await ws_manager.send(websocket, "task_created", task)
            elif event == "task_start":
                mgr = get_task_manager_instance()
                result = await mgr.start_task(data.get("task_id", ""))
                await ws_manager.send(websocket, "task_started", result)
            elif event == "task_pause":
                mgr = get_task_manager_instance()
                result = await mgr.pause_task(data.get("task_id", ""))
                await ws_manager.send(websocket, "task_paused", result)
            elif event == "task_resume":
                mgr = get_task_manager_instance()
                result = await mgr.resume_task(data.get("task_id", ""))
                await ws_manager.send(websocket, "task_resumed", result)
            elif event == "task_cancel":
                mgr = get_task_manager_instance()
                result = await mgr.cancel_task(data.get("task_id", ""))
                await ws_manager.send(websocket, "task_cancelled", result)
            elif event == "task_approve":
                mgr = get_task_manager_instance()
                result = await mgr.approve_plan(data.get("task_id", ""))
                await ws_manager.send(websocket, "task_approved", result)
            elif event == "task_deny":
                mgr = get_task_manager_instance()
                result = await mgr.deny_plan(data.get("task_id", ""))
                await ws_manager.send(websocket, "task_denied", result)
            elif event == "ping":
                await ws_manager.send(websocket, "pong", {"t": __import__("time").time()})
            elif event == "serious_mode_start":
                await ws_manager.broadcast("serious_mode_started", {"persona": settings.persona, "assistant_name": settings.assistant_name})
            elif event == "serious_mode_stop":
                await ws_manager.broadcast("serious_mode_stopped", {"persona": settings.persona, "assistant_name": settings.assistant_name})
            elif event == "research_start":
                mgr = get_research_manager_instance()
                topic = data.get("topic", "")
                if not topic:
                    await ws_manager.send(websocket, "research_failed", {"error": "empty_topic"})
                else:
                    job = await mgr.start_research(topic)
                    await ws_manager.send(websocket, "research_started", {"job_id": job.id, "topic": job.topic, "status": job.status.value})
            elif event == "research_cancel":
                mgr = get_research_manager_instance()
                ok = await mgr.cancel_research(data.get("job_id", ""))
                await ws_manager.send(websocket, "research_cancelled" if ok else "research_failed", {"job_id": data.get("job_id", "")})
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error("WebSocket error: %s", e)
        await ws_manager.disconnect(websocket)


# ---------------------------------------------------------------- frontend
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(frontend_dist / "index.html")

    @app.get("/{full_path:path}")
    async def serve_frontend_catchall(request: Request, full_path: str):
        if full_path:
            file_path = frontend_dist / full_path
            if file_path.exists() and file_path.is_file():
                return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
