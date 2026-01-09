import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.error import TelegramError

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration - Replace with your values
API_ID = "20288994"  # Get from my.telegram.org
API_HASH = "d702614912f1ad370a0d18786002adbf"  # Get from my.telegram.org
BOT_TOKEN = "8527463483:AAE4_hX5OrG3Jcu0uijZ0t41F8k6_btPAGg"  # Get from @BotFather

# Force subscription channels
FORCE_SUB_CHANNEL_1 = "@zerodev2"  # Your channel
FORCE_SUB_CHANNEL_2 = "@mvxyoffcail"  # Your movie group
FORCE_SUB_IMAGE = "https://i.ibb.co/pr2H8cwT/img-8312532076.jpg"

# Admin user IDs (optional)
ADMIN_IDS = []  # Add admin user IDs here

async def check_user_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> tuple[bool, list]:
    """Check if user is subscribed to required channels"""
    not_subscribed = []
    
    channels = [FORCE_SUB_CHANNEL_1, FORCE_SUB_CHANNEL_2]
    
    for channel in channels:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                not_subscribed.append(channel)
        except TelegramError as e:
            logger.error(f"Error checking subscription for {channel}: {e}")
            not_subscribed.append(channel)
    
    return len(not_subscribed) == 0, not_subscribed

async def send_force_sub_message(update: Update, not_subscribed: list):
    """Send force subscription message with image"""
    keyboard = []
    
    # Add subscription buttons
    for channel in not_subscribed:
        channel_name = channel.replace("@", "")
        keyboard.append([InlineKeyboardButton(f"Join {channel_name}", url=f"https://t.me/{channel_name}")])
    
    # Add check subscription button
    keyboard.append([InlineKeyboardButton("✅ Check Subscription", callback_data="check_sub")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = (
        "⚠️ **Access Denied!**\n\n"
        "You must join our channels to use this bot:\n\n"
        "📢 Join the channels below and click 'Check Subscription' button."
    )
    
    try:
        await update.message.reply_photo(
            photo=FORCE_SUB_IMAGE,
            caption=message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except:
        # If image fails, send text only
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = update.effective_user.id
    
    # Check subscription
    is_subscribed, not_subscribed = await check_user_subscription(user_id, context)
    
    if not is_subscribed:
        await send_force_sub_message(update, not_subscribed)
        return
    
    welcome_message = (
        "👋 **Welcome to UserInfo Bot!**\n\n"
        "This bot provides full information about users, groups, and channels.\n\n"
        "**Features:**\n"
        "• User, group, and channel IDs\n"
        "• Real account registration date\n"
        "• Full object information\n\n"
        "**How to use:**\n"
        "1. Forward a message from any user\n"
        "2. Send a username (e.g., @username)\n"
        "3. Send a user ID\n"
        "4. Add me to a group to get group info\n\n"
        "Start by forwarding a message or sending a username!"
    )
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def get_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages to get user information"""
    user_id = update.effective_user.id
    
    # Check subscription
    is_subscribed, not_subscribed = await check_user_subscription(user_id, context)
    
    if not is_subscribed:
        await send_force_sub_message(update, not_subscribed)
        return
    
    message = update.message
    target_user = None
    
    # Get user from forwarded message
    if message.forward_from:
        target_user = message.forward_from
    # Get user from reply
    elif message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
    # Get user from username or ID
    elif message.text:
        text = message.text.strip()
        try:
            # Try to get by username
            if text.startswith('@'):
                target_user = await context.bot.get_chat(text)
            # Try to get by ID
            elif text.isdigit():
                target_user = await context.bot.get_chat(int(text))
        except TelegramError as e:
            await message.reply_text(f"❌ Could not find user: {e}")
            return
    
    if target_user:
        # Format user information
        user_info = format_user_info(target_user)
        await message.reply_text(user_info, parse_mode='Markdown')
    else:
        await message.reply_text(
            "ℹ️ Please forward a message from a user or send their @username or ID."
        )

def format_user_info(user) -> str:
    """Format user information into a readable message"""
    info_parts = []
    
    # Username
    if hasattr(user, 'username') and user.username:
        info_parts.append(f"@{user.username}")
    
    # User ID
    info_parts.append(f"Id: {user.id}")
    
    # First name
    if hasattr(user, 'first_name') and user.first_name:
        info_parts.append(f"First: {user.first_name}")
    
    # Last name
    if hasattr(user, 'last_name') and user.last_name:
        info_parts.append(f"Last: {user.last_name}")
    
    # Language code
    if hasattr(user, 'language_code') and user.language_code:
        info_parts.append(f"Lang: {user.language_code}")
    
    # Registration date (approximate based on user ID)
    # Note: Actual registration date requires MTProto API
    if user.id < 1000000:
        reg_info = "Early User (2013-2014)"
    elif user.id < 10000000:
        reg_info = "Registered: 2014-2015"
    elif user.id < 100000000:
        reg_info = "Registered: 2015-2016"
    elif user.id < 500000000:
        reg_info = "Registered: 2016-2018"
    else:
        reg_info = "Registered: 2018+"
    
    info_parts.append(f"Registered: {reg_info}")
    
    # User type
    if hasattr(user, 'is_bot') and user.is_bot:
        info_parts.append("Type: 🤖 Bot")
    elif hasattr(user, 'is_premium') and user.is_premium:
        info_parts.append("Type: ⭐ Premium User")
    else:
        info_parts.append("Type: 👤 Regular User")
    
    return "\n".join(info_parts)

async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle check subscription button callback"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Check subscription
    is_subscribed, not_subscribed = await check_user_subscription(user_id, context)
    
    if is_subscribed:
        await query.message.reply_text(
            "✅ **Subscription Verified!**\n\n"
            "You can now use the bot. Send /start to begin!",
            parse_mode='Markdown'
        )
        await query.message.delete()
    else:
        await query.answer(
            "❌ You still haven't joined all channels. Please join and try again.",
            show_alert=True
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(check_subscription_callback, pattern="^check_sub$"))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, get_user_info))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
