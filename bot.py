import os
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import TelegramError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════
# CONFIG — use @username for public, ID for private
# ═══════════════════════════════════════
BOT_TOKEN      = os.getenv("BOT_TOKEN", "8748100924:AAHUgkCAdpESkklbvc-oEO01OOiYkjK6VlQ")
ADMIN_ID       = int(os.getenv("ADMIN_ID", "7062818847"))
STORE_CHANNEL  = os.getenv("STORE_CHANNEL", "-1003873345148")   # Private store ID
PUBLIC_CHANNEL = os.getenv("PUBLIC_CHANNEL", "@KuttyWebcc")     # Public channel username
BOT_USERNAME   = os.getenv("BOT_USERNAME", "Kuttyx_bot")

def is_admin(user_id):
    return user_id == ADMIN_ID

# ═══════════════════════════════════════
# /start
# ═══════════════════════════════════════
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    if args and args[0].startswith("file_"):
        msg_id = int(args[0].replace("file_", ""))
        await send_file_to_user(update, ctx, msg_id)
        return

    await update.message.reply_text(
        f"👋 Welcome to *KuttyWeb Movies Bot!*\n\n"
        f"🎬 Get Tamil movies directly here!\n\n"
        f"📢 Join our channel: @KuttyWebcc\n"
        f"🌐 Website: kuttyweb.online\n\n"
        f"_Tap any movie link from our channel to get the file!_",
        parse_mode="Markdown"
    )

# ═══════════════════════════════════════
# Send file to user
# ═══════════════════════════════════════
async def send_file_to_user(update: Update, ctx: ContextTypes.DEFAULT_TYPE, msg_id: int):
    try:
        await update.message.reply_text("⏳ Fetching your movie... please wait!")
        await ctx.bot.copy_message(
            chat_id=update.effective_chat.id,
            from_chat_id=STORE_CHANNEL,
            message_id=msg_id
        )
        await update.message.reply_text(
            "✅ *Enjoy your movie!*\n\n"
            "📢 Join @KuttyWebcc for more movies!\n"
            "🌐 kuttyweb.online",
            parse_mode="Markdown"
        )
    except TelegramError as e:
        logger.error(f"Error sending file: {e}")
        await update.message.reply_text(
            "❌ File not found!\n"
            "Join @KuttyWebcc for latest links."
        )

# ═══════════════════════════════════════
# Admin uploads file
# ═══════════════════════════════════════
async def handle_admin_upload(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Not authorized!")
        return

    msg = update.message
    if not (msg.document or msg.video or msg.audio):
        await update.message.reply_text(
            "📤 Send me a movie file with caption!\n"
            "_Example: Vettaiyan 2024 Tamil HD_",
            parse_mode="Markdown"
        )
        return

    caption = msg.caption or "🎬 New Movie"
    caption = caption.replace("@KuttyWebIn", "").replace("Join Our Main Channel -", "").strip(" -\n")

    await msg.reply_text("⏳ Storing movie... please wait!")

    try:
        # Step 1: Store in private channel
        stored = await ctx.bot.copy_message(
            chat_id=int(STORE_CHANNEL),
            from_chat_id=msg.chat_id,
            message_id=msg.message_id,
            caption=f"🎬 {caption}"
        )
        store_msg_id = stored.message_id
        file_link = f"https://t.me/{BOT_USERNAME}?start=file_{store_msg_id}"

        # Step 2: Post to @KuttyWebcc
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬇️ Get Movie", url=file_link)],
            [InlineKeyboardButton("🌐 Website", url="https://kuttyweb.online")]
        ])

        await ctx.bot.send_message(
            chat_id=PUBLIC_CHANNEL,
            text=f"🎬 *{caption}*\n\n"
                 f"👆 Tap *Get Movie* to receive the file!\n\n"
                 f"🌐 kuttyweb.online",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

        # Step 3: Reply to admin
        await msg.reply_text(
            f"✅ *Stored & Posted!*\n\n"
            f"🎬 *{caption}*\n\n"
            f"🔗 Direct Link:\n`{file_link}`\n\n"
            f"📢 Posted to @KuttyWebcc ✅\n"
            f"💾 Store ID: `{store_msg_id}`",
            parse_mode="Markdown"
        )

    except TelegramError as e:
        logger.error(f"Upload error: {e}")
        await msg.reply_text(
            f"❌ *Error:* `{str(e)}`\n\n"
            f"*Check these:*\n"
            f"1. Bot is admin in private store channel\n"
            f"2. Bot is admin in @KuttyWebcc\n"
            f"3. Store Channel ID is correct: `{STORE_CHANNEL}`",
            parse_mode="Markdown"
        )

# ═══════════════════════════════════════
# /setstore — update store channel ID
# ═══════════════════════════════════════
async def setstore(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text(
            "Usage: /setstore -100xxxxxxxxx\n\n"
            "To get channel ID:\n"
            "Forward any message from private channel to @userinfobot"
        )
        return
    global STORE_CHANNEL
    STORE_CHANNEL = ctx.args[0]
    await update.message.reply_text(f"✅ Store channel updated to: `{STORE_CHANNEL}`", parse_mode="Markdown")

# ═══════════════════════════════════════
# /stats
# ═══════════════════════════════════════
async def stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(
        f"📊 *KuttyWeb Bot Stats*\n\n"
        f"🤖 Bot: @{BOT_USERNAME}\n"
        f"📦 Store ID: `{STORE_CHANNEL}`\n"
        f"📢 Public: {PUBLIC_CHANNEL}\n"
        f"👤 Admin: `{ADMIN_ID}`\n\n"
        f"✅ Bot is running!\n\n"
        f"_If Chat not found error:_\n"
        f"Use /setstore with correct ID",
        parse_mode="Markdown"
    )

async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if is_admin(update.effective_user.id):
        await update.message.reply_text(
            "🛠 *Admin Commands:*\n\n"
            "📤 Send movie file → auto stores & posts\n"
            "/stats → show bot info\n"
            "/setstore -100xxx → update store channel ID\n"
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
    app.add_handler(CommandHandler("setstore", setstore))
    app.add_handler(MessageHandler(
        filters.Document.ALL | filters.VIDEO | filters.AUDIO,
        handle_admin_upload
    ))
    logger.info("🚀 KuttyX Bot started!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
