"""Telegram bot message handlers for co-parenting filter."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from telegram import Bot, Message, Update
from telegram.ext import ContextTypes

from config import config
from bot.filters import classify, ModerationResponse

logger = logging.getLogger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle incoming messages and filter based on co-parenting topics.
    
    Args:
        update: Telegram update object containing the message
        context: Bot context for handling the update
    """
    if not update.message or not update.message.text:
        return
    
    message = update.message
    username = message.from_user.username if message.from_user else None
    target_username = config.get_target_username_normalized()
    
    # Only monitor messages from the target username
    if not username or username.lower() != target_username.lower():
        return
    
    text = message.text.strip()
    if not text:
        return
    
    # Log the message being processed
    timestamp = datetime.now().isoformat()
    logger.info(f"Processing message from @{username} at {timestamp}")
    
    try:
        # Classify the message using AI
        moderation_result = classify(text)
        
        # Log the decision with detailed information
        preview = text[:50] + "..." if len(text) > 50 else text
        
        log_message = (
            f"[{timestamp}] @{username}: '{preview}' -> "
            f"{'ALLOW' if moderation_result.allow else 'BLOCK'} "
            f"({moderation_result.category}): {moderation_result.reason}"
        )
        
        if moderation_result.allow:
            logger.info(f"ALLOWED: {log_message}")
            print(f"✅ ALLOWED: {log_message}")
        else:
            logger.warning(f"BLOCKED: {log_message}")
            print(f"❌ BLOCKED: {log_message}")
            
            # Delete the message and send specific warning
            await _delete_message_and_warn(message, context.bot, moderation_result)
            
    except Exception as e:
        logger.error(f"Error processing message from @{username}: {e}")
        # Log the error but don't crash the bot
        error_log = (
            f"[{timestamp}] @{username}: '{text[:50]}...' -> ERROR: {e}"
        )
        print(f"⚠️ ERROR: {error_log}")


async def _delete_message_and_warn(message: Message, bot: Bot, moderation_result: ModerationResponse) -> None:
    """
    Delete a message and send a specific warning to the user.
    
    Args:
        message: The message to delete
        bot: Bot instance for sending messages
        moderation_result: The detailed moderation response with reasoning
    """
    try:
        # Delete the original message
        await bot.delete_message(
            chat_id=message.chat_id,
            message_id=message.message_id
        )
        logger.info(f"Deleted message {message.message_id} from chat {message.chat_id}")
        
        # Create targeted warning message
        warning_text = _build_warning_message(moderation_result)
        
        # Send specific warning to the user
        warning_msg = await bot.send_message(
            chat_id=message.chat_id,
            text=warning_text,
            reply_to_message_id=None  # Don't reply to deleted message
        )
        
        logger.info(f"Sent targeted warning message {warning_msg.message_id}: {moderation_result.reason}")
        
    except Exception as e:
        logger.error(f"Failed to delete message or send warning: {e}")
        # Don't raise the exception to avoid crashing the bot


def _build_warning_message(moderation_result: ModerationResponse) -> str:
    """
    Build a specific warning message based on the moderation result.
    
    Args:
        moderation_result: The detailed moderation response
        
    Returns:
        Formatted warning message
    """
    base_message = "This group is for co-parenting logistics only (health, education, scheduling, logistics)."
    
    # Map categories to more user-friendly explanations
    category_messages = {
        "performative": "Your message appeared to be performative posturing rather than actionable co-parenting communication.",
        "manipulation": "Your message seemed to deflect from logistics to emotional manipulation.",
        "narrative": "Your message appeared to craft a narrative rather than address children's needs.",
        "grandstanding": "Your message seemed to be grandstanding without substance about children's welfare.",
        "off_topic": "Your message was off-topic for this co-parenting logistics group.",
        "emotional_pressure": "Your message used emotional pressure instead of focusing on factual logistics.",
        "deflection": "Your message deflected from actual logistics to other topics.",
    }
    
    # Use the specific reason from AI, or fall back to category mapping
    specific_reason = moderation_result.reason
    
    # If the AI reason is generic, try to use category-specific messaging
    if (specific_reason in ["No reason provided", "Message could not be properly evaluated"] 
        and moderation_result.category in category_messages):
        specific_reason = category_messages[moderation_result.category]
    
    return f"{base_message} {specific_reason}"


async def handle_error(update: Optional[Update], context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle errors that occur during message processing.
    
    Args:
        update: The update that caused the error (may be None)
        context: Bot context containing error information
    """
    error = context.error
    logger.error(f"Update {update} caused error: {error}")
    
    # Log additional context if available
    if update and update.message:
        username = update.message.from_user.username if update.message.from_user else "unknown"
        text_preview = update.message.text[:50] if update.message.text else "no text"
        logger.error(f"Error context - User: @{username}, Text: '{text_preview}...'")
    
    print(f"🚨 Bot error: {error}")


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command.
    
    Args:
        update: Telegram update object
        context: Bot context
    """
    if not update.message:
        return
    
    profile = config.get_moderation_profile()
    
    response = (
        "🤖 Co-Parent Filter Bot is running!\n\n"
        f"📍 Monitoring messages from: @{config.get_target_username_normalized()}\n"
        f"🎯 Moderation Profile: {profile['name']}\n"
        f"📋 Filtering for co-parenting topics: health, education, scheduling, logistics\n"
        f"🔍 Mode: {'Permissive (only blocks obviously problematic content)' if profile.get('permissive_mode') else 'Strict'}\n\n"
        "Bot is ready and actively monitoring with detailed feedback."
    )
    
    await update.message.reply_text(response)
    logger.info("Bot start command received")


async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /status command to show bot status.
    
    Args:
        update: Telegram update object
        context: Bot context
    """
    if not update.message:
        return
    
    profile = config.get_moderation_profile()
    user_id = update.message.from_user.id if update.message.from_user else None
    
    status = (
        "📊 Bot Status:\n"
        f"✅ Active and monitoring @{config.get_target_username_normalized()}\n"
        f"🎯 Profile: {profile['name']}\n"
        f"🔍 Filtering: health, education, scheduling, logistics\n"
        f"🤖 AI Model: GPT-4o with detailed reasoning\n"
        f"⚙️ Mode: {'Permissive' if profile.get('permissive_mode') else 'Strict'}\n"
        f"🆔 Bot ID: {context.bot.id}\n"
        f"💬 Chat ID: {update.message.chat_id}"
    )
    
    await update.message.reply_text(status)
    logger.info(f"Status requested by user {user_id}")


async def handle_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /profile command to show current moderation profile details.
    
    Args:
        update: Telegram update object
        context: Bot context
    """
    if not update.message:
        return
    
    profile = config.get_moderation_profile()
    
    profile_info = (
        f"🎯 Current Moderation Profile: {profile['name']}\n\n"
        f"📝 Description: {profile['description']}\n\n"
    )
    
    if profile['behaviors']:
        behaviors_text = "\n".join(f"• {behavior}" for behavior in profile['behaviors'])
        profile_info += f"🔍 Watching for these patterns:\n{behaviors_text}\n\n"
    
    profile_info += f"⚙️ Mode: {'Permissive (only blocks obvious violations)' if profile.get('permissive_mode') else 'Strict (blocks any violations)'}"
    
    await update.message.reply_text(profile_info)
    logger.info("Profile info requested")


# Command handlers mapping
COMMAND_HANDLERS = {
    "start": handle_start,
    "status": handle_status,
    "profile": handle_profile,
} 