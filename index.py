import telebot
from telebot import types
from flask import Flask, request
import os

# --- CONFIGURATION ---
TOKEN = '8527463483:AAE4_hX5OrG3Jcu0uijZ0t41F8k6_btPAGg'  # <--- PUT YOUR TOKEN HERE
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# Channels for Force Subscription (Must be public or bot must be admin)
CHANNELS = [
    {'username': '@zerodev2', 'url': 'https://t.me/zerodev2'},
    {'username': '@mvxyoffcail', 'url': 'https://t.me/mvxyoffcail'}
]

# The Image to show during Force Sub
FORCE_SUB_IMAGE = "https://i.ibb.co/pr2H8cwT/img-8312532076.jpg"

# --- HELPER FUNCTIONS ---

def check_subscription(user_id):
    """
    Checks if the user is a member of the required channels.
    Returns True if subscribed to all, False otherwise.
    """
    for channel in CHANNELS:
        try:
            chat_member = bot.get_chat_member(channel['username'], user_id)
            if chat_member.status not in ['creator', 'administrator', 'member']:
                return False
        except Exception as e:
            # If bot is not admin or channel is invalid, we might get an error.
            # Usually implies bot can't check, so we assume False or log error.
            print(f"Error checking channel {channel['username']}: {e}")
            return False
    return True

def get_subscription_markup():
    """Creates the inline keyboard buttons for joining channels."""
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton(text="Join Channel 1", url=CHANNELS[0]['url'])
    btn2 = types.InlineKeyboardButton(text="Join Movie Group", url=CHANNELS[1]['url'])
    btn_check = types.InlineKeyboardButton(text="✅ Joined", callback_data="check_sub")
    markup.add(btn1, btn2, btn_check)
    return markup

# --- BOT HANDLERS ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    # 1. Force Subscribe Check
    if not check_subscription(user_id):
        bot.send_photo(
            chat_id=message.chat.id,
            photo=FORCE_SUB_IMAGE,
            caption="⚠️ **Access Denied**\n\nPlease join our channels to use this bot!",
            parse_mode='Markdown',
            reply_markup=get_subscription_markup()
        )
        return

    # 2. Gather User Info (Matching the Screenshot style)
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name if message.from_user.last_name else "None"
    username = message.from_user.username
    language = message.from_user.language_code
    
    # Formatting the Username to look like the screenshot (clickable)
    user_link = f"@{username}" if username else "None"
    
    # 3. Construct the Message
    # Note: "Registered: Check Date" is hardcoded text as per your request 
    # (Real reg date requires complex API calls or estimation).
    text = (
        f"{user_link}\n"
        f"Id: `{user_id}`\n"
        f"First: {first_name}\n"
        f"Last: {last_name}\n"
        f"Lang: {language}\n"
        f"Registered: [Check Date](tg://user?id={user_id})" 
    )

    # 4. Send the Info
    bot.send_message(
        message.chat.id, 
        text, 
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def callback_check_sub(call):
    """Handles the 'Joined' button click."""
    if check_subscription(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "Thanks for joining!")
        # Trigger the start command manually or ask them to click start
        bot.send_message(call.message.chat.id, "Subscription verified! Click /start to view your info.")
    else:
        bot.answer_callback_query(call.id, "You haven't joined both channels yet!", show_alert=True)

# --- FLASK SERVER (VERCEL WEBHOOK) ---

@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    # Replace 'YOUR_VERCEL_DOMAIN' with your actual Vercel project domain after deployment
    # Example: https://my-telegram-bot.vercel.app
    s = bot.set_webhook(url=os.environ.get('VERCEL_URL') + '/' + TOKEN)
    if s:
        return "Webhook setup ok"
    else:
        return "Webhook setup failed"

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
