from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
import config
from utils import get_all_tracks_from_playlist, finish_task

async def enter_rank_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 **MODO RANKING**\nEnvíame el enlace de la playlist.")
    return config.RANK_URL

async def rank_handle_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if "spotify.com" not in url and len(url) < 10:
        await update.message.reply_text("❌ Enlace no válido.")
        return config.RANK_URL
    context.user_data["rank_url"] = url
    await update.message.reply_text("🔢 ¿Cuántas canciones? (Número o 'all')")
    return config.RANK_NUMBER

async def rank_handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        sp = context.bot_data['sp_client'] # Recuperamos cliente SP
        url = context.user_data.get("rank_url")
        n_str = update.message.text.strip().lower()
        
        await update.message.reply_text("⏳ Analizando...")
        tracks = get_all_tracks_from_playlist(sp, url)
        tracks.sort(key=lambda x: x['popularity'], reverse=True)
        
        n = len(tracks) if n_str == 'all' else int(n_str)
        top = tracks[:n]
        
        msg = [f"🏆 **Top {n} Popularidad**"]
        for i, t in enumerate(top):
            msg.append(f"{i+1}. {t['name']} - {t['artists'][0]['name']} ({t['popularity']})")
            
        text = "\n".join(msg)
        for i in range(0, len(text), 4000):
            await update.message.reply_text(text[i:i+4000])
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

    await finish_task(update)
    return ConversationHandler.END
