import os
import asyncio
import logging
from apps.api.app.core.config import settings
from apps.worker.transport import MockMediaTransport
from apps.worker.pipeline import VoicePipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("asistline-worker")


async def main():
    logger.info("Starting AsistLine AI Voice Worker...")
    logger.info(f"LiveKit URL: {settings.LIVEKIT_URL}")
    
    # Simple loop keeping worker running
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
