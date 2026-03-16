import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════
BOT_TOKEN      = os.getenv("BOT_TOKEN", "8748100924:AAHUgkCAdpESkklbvc-oEO01OOiYkjK6VlQ")
ADMIN_ID       = int(os.getenv("ADMIN_ID", "7062818847"))
BOT_USERNAME   = os.getenv("BOT_USERNAME", "Kuttyx_bot")
PUBLIC_CHANNEL = os.getenv("PUBLIC_CHANNEL", "@KuttyWebcc")

# ── Fix Store Channel ID ──
# Always ensure it starts with -100
_raw = os.getenv("STORE_CHANNEL", "-1003873345148").strip()
if _raw.lstrip('-').isdigit():
    _num = int(_raw)
    # If positive number given, make it negative with -100 prefix
    if _num > 0:
        STORE_CHANNEL = int("-100" + str(_num))
    else:
        STORE_CHANNEL = _num
else:
    STORE_CHANNEL = -1003873345148

logger.info(f"Store Channel ID: {STORE_CHANNEL}")
logger.info(f"Public Channel: {PUBLIC_CHANNEL}")
logger.info(f"Admin ID: {ADMIN_ID}")

def is_admin(user_id): return user_id == ADMIN_ID

# ═══════════════════════════════════════
# /start
# ═══════════════════════════════════════
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    if args and args[0].startswith("file_"):
        msg_id = int(args[0].replace("file_", ""))
        await send_file(update, ctx, msg_id)
        return
    await update.message.reply_text(
        "👋 Welcome to *KuttyWeb Movies Bot!*\n\n"
        "🎬 Get Tamil movies directly here!\n"
        "📢 Join: @KuttyWebcc\n"
        "🌐 Website: kuttyweb.online",
        parse_mode="Markdown"
    )

# ═══════════════════════════════════════
# Send file to user
# ═══════════════════════════════════════
async def send_file(update: Update, ctx: ContextTypes.DEFAULT_TYPE, msg_id: int):
    try:
        await update.message.reply_text("⏳ Fetching your movie...")
        await ctx.bot.copy_message(
            chat_id=update.effective_chat.id,
            from_chat_id=STORE_CHANNEL,
            message_id=msg_id
        )
        await update.message.reply_text(
            "✅ *Enjoy your movie!*\n\n"
            "📢 @KuttyWebcc for more!\n"
            "🌐 kuttyweb.online",
            parse_mode="Markdown"
        )
    except TelegramError as e:
        logger.error(f"Send file error: {e}")
        await update.message.reply_text("❌ File expired! Visit @KuttyWebcc for latest links.")

# ═══════════════════════════════════════
# Admin upload handler
# ═══════════════════════════════════════
async def handle_upload(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Not authorized!")
        return

    msg = update.message
    if not (msg.document or msg.video or msg.audio):
        await update.message.reply_text(
            "📤 Send me a movie file with caption!\n"
            "_Example caption: Vettaiyan 2024 Tamil HD_",
            parse_mode="Markdown"
        )
        return

    # Clean caption
    caption = msg.caption or "🎬 New Movie"
    caption = caption.replace("@KuttyWebIn", "").replace("Join Our Main Channel -", "").strip(" -\n")
    if not caption:
        caption = "🎬 New Movie"

    await msg.reply_text("⏳ Storing movie... please wait!")

    try:
        # Step 1: Store in private channel
        logger.info(f"Copying to store channel: {STORE_CHANNEL}")
        stored = await ctx.bot.copy_message(
            chat_id=STORE_CHANNEL,
            from_chat_id=msg.chat_id,
            message_id=msg.message_id,
            caption=f"🎬 {caption}"
        )
        store_msg_id = stored.message_id
        file_link = f"https://t.me/{BOT_USERNAME}?start=file_{store_msg_id}"
        logger.info(f"Stored! Message ID: {store_msg_id}")

        # Step 2: Post to public channel
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬇️ Get Movie", url=file_link)],
            [InlineKeyboardButton("🌐 Website", url="https://kuttyweb.online")]
        ])
        await ctx.bot.send_message(
            chat_id=PUBLIC_CHANNEL,
            text=f"🎬 *{caption}*\n\n"
                 f"👆 Tap *Get Movie* button to receive file!\n\n"
                 f"🌐 kuttyweb.online",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        logger.info(f"Posted to {PUBLIC_CHANNEL}")

        # Step 3: Reply to admin with link
        await msg.reply_text(
            f"✅ *Stored & Posted Successfully!*\n\n"
            f"🎬 *{caption}*\n\n"
            f"🔗 *Direct Link:*\n`{file_link}`\n\n"
            f"📢 Posted to @KuttyWebcc ✅\n"
            f"💾 Store ID: `{store_msg_id}`\n\n"
            f"_Copy the link for your website!_",
            parse_mode="Markdown"
        )

    except TelegramError as e:
        logger.error(f"Upload error: {e}")
        await msg.reply_text(
            f"❌ *Error:* `{str(e)}`\n\n"
            f"*Checklist:*\n"
            f"1. @{BOT_USERNAME} is admin in store channel ✓\n"
            f"2. @{BOT_USERNAME} is admin in @KuttyWebcc ✓\n"
            f"3. Store Channel ID: `{STORE_CHANNEL}`\n\n"
            f"Use /fixid to update store channel ID",
            parse_mode="Markdown"
        )

# ═══════════════════════════════════════
# /fixid — fix store channel ID
# ═══════════════════════════════════════
async def fixid(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not ctx.args:
        await update.message.reply_text(
            "📌 *How to get correct Store Channel ID:*\n\n"
            "1. Go to your private store channel\n"
            "2. Forward any message to @userinfobot\n"
            "3. Copy the ID (starts with -100)\n\n"
            "Then send: `/fixid -100xxxxxxxxx`",
            parse_mode="Markdown"
        )
        return
    global STORE_CHANNEL
    try:
        new_id = int(ctx.args[0])
        STORE_CHANNEL = new_id
        await update.message.reply_text(
            f"✅ Store channel updated!\n`{STORE_CHANNEL}`",
            parse_mode="Markdown"
        )
        logger.info(f"Store channel updated to: {STORE_CHANNEL}")
    except:
        await update.message.reply_text("❌ Invalid ID! Use format: -100xxxxxxxxx")

# ═══════════════════════════════════════
# /stats
# ═══════════════════════════════════════
async def stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    # Test channel access
    store_ok = "❓"
    public_ok = "❓"
    try:
        chat = await ctx.bot.get_chat(STORE_CHANNEL)
        store_ok = f"✅ {chat.title}"
    except Exception as e:
        store_ok = f"❌ {str(e)[:40]}"
    try:
        chat = await ctx.bot.get_chat(PUBLIC_CHANNEL)
        public_ok = f"✅ {chat.title}"
    except Exception as e:
        public_ok = f"❌ {str(e)[:40]}"

    await update.message.reply_text(
        f"📊 *KuttyWeb Bot Stats*\n\n"
        f"🤖 Bot: @{BOT_USERNAME}\n"
        f"👤 Admin: `{ADMIN_ID}`\n\n"
        f"📦 Store: `{STORE_CHANNEL}`\n"
        f"Status: {store_ok}\n\n"
        f"📢 Public: `{PUBLIC_CHANNEL}`\n"
        f"Status: {public_ok}\n\n"
        f"_Use /fixid if store shows ❌_",
        parse_mode="Markdown"
    )

async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if is_admin(update.effective_user.id):
        await update.message.reply_text(
            "🛠 *Admin Commands:*\n\n"
            "📤 Send movie file → auto stores & posts\n"
            "/stats → check bot & channel status\n"
            "/fixid -100xxx → update store channel ID\n"
            "/help → this message",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "🎬 *KuttyWeb Movies Bot*\n\n"
            "📢 Join @KuttyWebcc for movies!\n"
            "🌐 kuttyweb.online",
            parse_mode="Markdown"
        )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("fixid", fixid))
    app.add_handler(MessageHandler(
        filters.Document.ALL | filters.VIDEO | filters.AUDIO,
        handle_upload
    ))
    logger.info("🚀 KuttyX Bot started!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
