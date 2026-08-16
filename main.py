import asyncio
import logging
import sys
from pathlib import Path

from config.settings import get_settings
from backend.main import app
from backend.services.ai_service import AIService
from backend.services.voice_service import VoiceManager
from memory.manager import MemoryManager
from tools.registry import ToolRegistry
from voice.tts import TTS

import uvicorn


def setup_directories():
    settings = get_settings()
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(parents=True, exist_ok=True)


def main():
    setup_directories()
    settings = get_settings()
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler("logs/jarvis.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logger = logging.getLogger("jarvis")
    logger.info(f"Starting {settings.assistant_name} 2.0...")
    logger.info(f"Model: {settings.groq_model}")
    logger.info(f"Backend: http://{settings.backend_host}:{settings.backend_port}")
    uvicorn.run(
        app,
        host=settings.backend_host,
        port=settings.backend_port,
        log_level=settings.log_level.lower(),
        ws_ping_interval=60,
        ws_ping_timeout=30,
    )


if __name__ == "__main__":
    main()
