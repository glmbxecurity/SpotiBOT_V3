from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
import config
from utils import get_all_tracks_from_playlist, finish_task, check_auth_telegram, verify_spotify_ownership

async def enter_sort_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth_telegram(update): return ConversationHandler.END
    await update.message.reply_text("⚠️ **MODO ORDENAR**\nEnvíame el enlace de TU playlist para ordenarla por fama.")
    return config.SORT_URL

async def process_sort_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sp = context.bot_data['sp_client']
    user_id = context.bot_data['user_id']
    url = update.message.text.strip()
    
    try:
        pid = url.split("playlist/")[1].split("?")[0]
        is_owner, err = verify_spotify_ownership(sp, pid, user_id)
        if not is_owner:
            await update.message.reply_text(err)
            return ConversationHandler.END

        await update.message.reply_text("⏳ Ordenando...")
        tracks = get_all_tracks_from_playlist(sp, pid)
        tracks.sort(key=lambda x: x['popularity'], reverse=True)
        sorted_uris = [t['uri'] for t in tracks]

        sp.playlist_replace_items(pid, sorted_uris[:100])
        for i in range(100, len(sorted_uris), 100):
            sp.playlist_add_items(pid, sorted_uris[i:i+100])
            
        await update.message.reply_text(f"✅ Hecho: {len(sorted_uris)} canciones reordenadas.")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
    
    await finish_task(update)
    return ConversationHandler.END
