from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
import config
from utils import get_all_tracks_from_playlist, finish_task, check_auth_telegram, verify_spotify_ownership

async def enter_top_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth_telegram(update): return ConversationHandler.END
    await update.message.reply_text("✂️ **MODO TOP FILTER**\nEnvíame el enlace para dejar solo las mejores.")
    return config.TOP_URL

async def process_top_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["top_url"] = update.message.text.strip()
    await update.message.reply_text("🔢 ¿Con cuántas canciones te quedas? (Ej: 50)")
    return config.TOP_NUMBER

async def process_top_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sp = context.bot_data['sp_client']
    user_id = context.bot_data['user_id']
    try:
        n = int(update.message.text.strip())
        url = context.user_data["top_url"]
        pid = url.split("playlist/")[1].split("?")[0]
        
        is_owner, err = verify_spotify_ownership(sp, pid, user_id)
        if not is_owner:
            await update.message.reply_text(err)
            return ConversationHandler.END

        await update.message.reply_text(f"⏳ Filtrando Top {n}...")
        tracks = get_all_tracks_from_playlist(sp, pid)
        tracks.sort(key=lambda x: x['popularity'], reverse=True)
        
        top_uris = [t['uri'] for t in tracks[:n]]
        
        sp.playlist_replace_items(pid, top_uris[:100])
        for i in range(100, len(top_uris), 100):
            sp.playlist_add_items(pid, top_uris[i:i+100])
            
        await update.message.reply_text(f"✅ Listo: Playlist reducida a {len(top_uris)} canciones.")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        
    await finish_task(update)
    return ConversationHandler.END
