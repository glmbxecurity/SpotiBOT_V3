from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
import config
from utils import get_all_tracks_from_playlist, finish_task, check_auth_telegram

async def enter_mixer_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth_telegram(update): return ConversationHandler.END
    context.user_data["mixer_mode"] = "normal"
    await update.message.reply_markdown("🍹 **MODO MIXER**\nEnvía enlaces separados por espacio.\nComandos extra: `/modo mix` o `/modo normal`.")
    return config.MIXER_INPUT

async def mixer_set_mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    mode = "mix" if "mix" in text else "normal"
    context.user_data["mixer_mode"] = mode
    await update.message.reply_text(f"🔀 Modo {mode.upper()} activado.")
    return config.MIXER_INPUT

async def mixer_process_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.lower().startswith("/modo"):
        return await mixer_set_mode_command(update, context)

    pids = [p.split("playlist/")[1].split("?")[0] for p in text.split() if "playlist/" in p]
    if len(pids) < 2:
        await update.message.reply_text("⚠️ Necesito al menos 2 enlaces.")
        return config.MIXER_INPUT

    context.user_data["mixer_pids"] = pids
    await update.message.reply_text("📝 ¿Nombre de la nueva playlist?")
    return config.MIXER_NAME

async def mixer_process_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sp = context.bot_data['sp_client']
    user_id = context.bot_data['user_id']
    
    playlist_name = update.message.text.strip()
    pids = context.user_data.get("mixer_pids", [])
    mode = context.user_data.get("mixer_mode", "normal")

    await update.message.reply_text(f"🍹 Creando mix '{playlist_name}'...")

    try:
        tracks_lists = []
        for pid in pids:
            tracks = get_all_tracks_from_playlist(sp, pid)
            tracks_lists.append([t['uri'] for t in tracks])
            
        final_uris = []
        if mode == 'mix':
            max_len = max(len(l) for l in tracks_lists)
            for i in range(max_len):
                for l in tracks_lists:
                    if i < len(l) and l[i] not in final_uris: final_uris.append(l[i])
        else:
            seen = set()
            for l in tracks_lists:
                for u in l:
                    if u not in seen:
                        final_uris.append(u)
                        seen.add(u)
        
        if not final_uris:
            await update.message.reply_text("❌ Sin canciones válidas.")
            return ConversationHandler.END

        new_pl = sp.user_playlist_create(user_id, playlist_name, public=False, description=f"Mixer {mode}")
        for i in range(0, len(final_uris), 100):
            sp.playlist_add_items(new_pl['id'], final_uris[i:i+100])
            
        await update.message.reply_text(f"✅ Playlist creada: {new_pl['external_urls']['spotify']}")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

    await finish_task(update)
    return ConversationHandler.END
