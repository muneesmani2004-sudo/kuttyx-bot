import os
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import TelegramError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════
BOT_TOKEN      = os.getenv("BOT_TOKEN", "8748100924:AAHUgkCAdpESkklbvc-oEO01OOiYkjK6VlQ")
ADMIN_ID       = int(os.getenv("ADMIN_ID", "7062818847"))
STORE_CHANNEL  = int(os.getenv("STORE_CHANNEL", "-1003873345148"))   # Private store
PUBLIC_CHANNEL = int(os.getenv("PUBLIC_CHANNEL", "-1003706592571"))  # @KuttyWebcc
BOT_USERNAME   = os.getenv("BOT_USERNAME", "Kuttyx_bot")

# ═══════════════════════════════════════
# HELPER — is admin?
# ═══════════════════════════════════════
def is_admin(user_id):
    return user_id == ADMIN_ID

# ═══════════════════════════════════════
# /start — handle file requests
# ═══════════════════════════════════════
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    user = update.effective_user

    # If user came from a file link: /start file_MESSAGEID
    if args and args[0].startswith("file_"):
        msg_id = int(args[0].replace("file_", ""))
        await send_file_to_user(update, ctx, msg_id)
        return

    # Normal start
    await update.message.reply_text(
        f"👋 Welcome to *KuttyWeb Movies Bot!*\n\n"
        f"🎬 Get Tamil movies directly here!\n\n"
        f"📢 Join our channel: @KuttyWebcc\n"
        f"🌐 Website: kuttyweb.online\n\n"
        f"_Tap any movie link from our channel to get the file!_",
        parse_mode="Markdown"
    )

# ═══════════════════════════════════════
# Send file from store channel to user
# ═══════════════════════════════════════
async def send_file_to_user(update: Update, ctx: ContextTypes.DEFAULT_TYPE, msg_id: int):
    user = update.effective_user
    try:
        await update.message.reply_text("⏳ Fetching your movie... please wait!")

        # Copy message from private store to user
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
            "❌ File not found or expired!\n"
            "Please visit @KuttyWebcc for the latest links."
        )

# ═══════════════════════════════════════
# Admin uploads file to STORE channel
# ═══════════════════════════════════════
async def handle_admin_upload(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_admin(user.id):
        await update.message.reply_text("❌ You are not authorized!")
        return

    msg = update.message

    # Must have a file
    if not (msg.document or msg.video or msg.audio):
        await update.message.reply_text(
            "📤 *How to upload a movie:*\n\n"
            "1. Send the movie file to me (as document/video)\n"
            "2. Add caption with movie name\n"
            "3. I'll store it and post to @KuttyWebcc automatically!\n\n"
            "_Example caption:_ `Vettaiyan (2024) Tamil HD`",
            parse_mode="Markdown"
        )
        return

    caption = msg.caption or "🎬 New Movie"

    await msg.reply_text("⏳ Storing movie... please wait!")

    try:
        # Step 1: Forward to private store channel
        stored = await ctx.bot.copy_message(
            chat_id=STORE_CHANNEL,
            from_chat_id=msg.chat_id,
            message_id=msg.message_id,
            caption=f"🎬 {caption}\n\n📦 Stored by @{BOT_USERNAME}"
        )

        store_msg_id = stored.message_id
        file_link = f"https://t.me/{BOT_USERNAME}?start=file_{store_msg_id}"

        # Step 2: Post to public channel @KuttyWebcc
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬇️ Get Movie", url=file_link)],
            [InlineKeyboardButton("🌐 Website", url="https://kuttyweb.online")]
        ])

        await ctx.bot.send_message(
            chat_id=PUBLIC_CHANNEL,
            text=f"🎬 *{caption}*\n\n"
                 f"✅ Now available on KuttyWeb!\n\n"
                 f"👆 Tap *Get Movie* to receive the file directly!\n\n"
                 f"🌐 kuttyweb.online",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

        # Step 3: Reply to admin with link
        await msg.reply_text(
            f"✅ *Movie stored & posted successfully!*\n\n"
            f"🎬 *{caption}*\n\n"
            f"🔗 *Direct Link:*\n`{file_link}`\n\n"
            f"📢 Posted to @KuttyWebcc\n"
            f"💾 Store ID: `{store_msg_id}`\n\n"
            f"_Copy the link above for your website!_",
            parse_mode="Markdown"
        )

    except TelegramError as e:
        logger.error(f"Upload error: {e}")
        await msg.reply_text(f"❌ Error: {str(e)}\n\nMake sure bot is admin in both channels!")

# ═══════════════════════════════════════
# /stats — admin stats
# ═══════════════════════════════════════
async def stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(
        "📊 *KuttyWeb Bot Stats*\n\n"
        f"🤖 Bot: @{BOT_USERNAME}\n"
        f"📦 Store: `{STORE_CHANNEL}`\n"
        f"📢 Public: @KuttyWebcc\n"
        f"👤 Admin: `{ADMIN_ID}`\n\n"
        f"✅ Bot is running!",
        parse_mode="Markdown"
    )

# ═══════════════════════════════════════
# /help
# ═══════════════════════════════════════
async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if is_admin(update.effective_user.id):
        await update.message.reply_text(
            "🛠 *Admin Commands:*\n\n"
            "📤 Send any movie file → auto stores & posts\n"
            "/stats → bot statistics\n"
            "/help → this message\n\n"
            "*How it works:*\n"
            "1. Send movie file with caption\n"
            "2. Bot stores in private channel\n"
            "3. Bot posts link to @KuttyWebcc\n"
            "4. Users tap link → bot sends file\n"
            "5. Copy link for kuttyweb.online ✅",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "ℹ️ *KuttyWeb Movies Bot*\n\n"
            "🎬 Get Tamil movies directly!\n"
            "📢 Join @KuttyWebcc for latest movies\n"
            "🌐 Visit kuttyweb.online",
            parse_mode="Markdown"
        )

# ═══════════════════════════════════════
# MAIN
# ═══════════════════════════════════════
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(
        filters.Document.ALL | filters.VIDEO | filters.AUDIO,
        handle_admin_upload
    ))

    logger.info("🚀 KuttyX Bot started!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
