import asyncio
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config.settings import get_settings
from memory.manager import MemoryManager
from tools.registry import build_registry
from backend.services.ai_service import AIService
from backend.services.voice_service import VoiceManager
from backend.services.memory_service import MemoryService
from backend.services.tool_service import ToolService
from backend.services.system_service import SystemService
from backend.services.automation_service import AutomationService
from backend.services.notification_service import NotificationService
from backend.services.ws_manager import ws_manager
from backend.services.persona_service import persona_service
from voice.tts_manager import TTSManager
from backend.api.chat import router as chat_router
from backend.api.voice import router as voice_router
from backend.api.system import router as system_router
from backend.api.memory import router as memory_router
from backend.api.settings import router as settings_router
from backend.api.tools import router as tools_router
from backend.api.automation import router as automation_router
from backend.api.persona import router as persona_router

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
ai_service = AIService(memory_manager, tts_manager, tool_registry)
voice_service = VoiceManager(memory_manager, ai_service)
memory_service = MemoryService(memory_manager)
tool_service = ToolService(tool_registry)
system_service = SystemService()
notification_service = NotificationService()


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


tts_manager.on_event(_tts_broadcast)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("JARVIS 2.0 starting up...")
    await persona_service.apply_persona_on_startup()
    await tts_manager.start()
    await voice_service.start()
    await automation_service.start()
    await notification_service.push("JARVIS is online and ready.", "success")
    logger.info("JARVIS 2.0 ready.")
    yield
    logger.info("JARVIS 2.0 shutting down...")
    await automation_service.stop()
    await voice_service.stop()
    await tts_manager.stop()


app = FastAPI(title="JARVIS 2.0", version="2.0.0", lifespan=lifespan)

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
app.include_router(persona_router, prefix="/api")


# ---------------------------------------------------------------- health
@app.get("/api/health")
async def health():
    provider_status = await ai_service.health()
    return {
        "status": "ok",
        "assistant": settings.assistant_name,
        "providers": provider_status,
        "database": await system_service.check_database(settings.db_path),
        "websocket": system_service.check_websocket(ws_manager),
        "tts": {
            "status": "available" if tts_manager.is_available() else "unavailable",
            "backend": tts_manager.backend,
            "engine": tts_manager.engine,
        },
        "voice": {
            "status": "available" if voice_service.is_available() else "unavailable",
            "mic": voice_service.mic_available,
        },
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


# ---------------------------------------------------------------- diagnostics
@app.get("/api/system/diagnostics")
async def system_diagnostics():
    from brain.provider_registry import create_providers

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
            elif event == "ping":
                await ws_manager.send(websocket, "pong", {"t": __import__("time").time()})
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
