"""Background worker entrypoint for evaluations and aggregates."""

import asyncio
import logging
import signal

from agentpulse.core.settings import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("agentpulse.worker")


async def run_worker() -> None:
    """Run worker loop handling streams and tasks."""
    settings = get_settings()
    logger.info("Starting AgentPulse worker (environment: %s)", settings.environment)

    stop_event = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except (NotImplementedError, AttributeError):
            # Windows does not support add_signal_handler for some loops
            pass

    logger.info("Worker initialized and listening for stream jobs.")
    try:
        while not stop_event.is_set():
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info("Worker cancellation received.")
    finally:
        logger.info("AgentPulse worker stopped gracefully.")


def main() -> None:
    """Synchronous entrypoint for worker command."""
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user.")


if __name__ == "__main__":
    main()
