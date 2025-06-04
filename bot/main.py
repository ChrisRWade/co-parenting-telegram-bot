"""Main entry point for the co-parent filter bot."""

from __future__ import annotations

import asyncio
import logging
import logging.config
import signal
import sys
from pathlib import Path
from typing import NoReturn

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from config import config
from bot.handlers import (
    COMMAND_HANDLERS,
    handle_error,
    handle_message,
)

# Global application instance for graceful shutdown
app: Application | None = None


def setup_logging() -> None:
    """Configure logging for the application."""
    logging_config_path = Path(__file__).parent / "logging.cfg"
    
    if logging_config_path.exists():
        logging.config.fileConfig(logging_config_path)
    else:
        # Fallback logging configuration
        logging.basicConfig(
            level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully")


def setup_signal_handlers() -> None:
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(sig: int, frame) -> None:
        logger = logging.getLogger(__name__)
        logger.info(f"Received signal {sig}, shutting down gracefully...")
        
        if app:
            # Stop the application
            asyncio.create_task(app.stop())
            asyncio.create_task(app.shutdown())
        
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def create_application() -> Application:
    """Create and configure the Telegram bot application."""
    logger = logging.getLogger(__name__)
    
    # Validate configuration
    try:
        config.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    
    # Create application
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Add message handler for all text messages
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    
    # Add command handlers
    for command, handler in COMMAND_HANDLERS.items():
        application.add_handler(CommandHandler(command, handler))
    
    # Add error handler
    application.add_error_handler(handle_error)
    
    logger.info("Bot application configured successfully")
    logger.info(f"Monitoring user: @{config.get_target_username_normalized()}")
    
    return application


async def main() -> None:
    """Main function to run the bot."""
    global app
    
    logger = logging.getLogger(__name__)
    
    try:
        # Setup logging and signal handlers
        setup_logging()
        setup_signal_handlers()
        
        logger.info("Starting Co-Parent Filter Bot...")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Target user: @{config.get_target_username_normalized()}")
        
        # Create and run the application
        app = await create_application()
        
        # Initialize the bot (get info, set up webhooks if needed)
        await app.initialize()
        
        # Start the bot
        logger.info("Bot starting up...")
        await app.start()
        
        # Get bot info
        bot_info = await app.bot.get_me()
        logger.info(f"Bot started successfully: @{bot_info.username} ({bot_info.first_name})")
        print(f"🤖 Bot @{bot_info.username} is now running and monitoring @{config.get_target_username_normalized()}")
        print("Press Ctrl+C to stop the bot")
        
        # Start polling for updates
        await app.updater.start_polling(
            poll_interval=1.0,  # Poll every second
            timeout=30,         # 30 second timeout for long polling
            bootstrap_retries=-1,  # Retry indefinitely on bootstrap errors
            read_timeout=30,    # 30 second read timeout
            write_timeout=30,   # 30 second write timeout
            connect_timeout=30, # 30 second connection timeout
        )
        
        # Keep the bot running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise
    finally:
        if app:
            logger.info("Stopping bot...")
            await app.stop()
            await app.shutdown()
        logger.info("Bot stopped")


def run_bot() -> NoReturn:
    """Run the bot with proper async handling."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"🚨 Fatal error: {e}")
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    run_bot() 