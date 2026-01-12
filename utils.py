import os
from telegram import Update
import config

def load_txt_set(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_txt_set(path, new_items):
    dirname = os.path.dirname(path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for item in new_items:
            f.write(f"{item}\n")

def get_all_tracks_from_playlist(sp_client, playlist_id):
    """Descarga tracks completos de una lista usando el cliente pasado."""
    tracks = []
    try:
        results = sp_client.playlist_items(playlist_id)
        while results:
            for item in results['items']:
                if item.get('track'):
                    tracks.append(item['track'])
            results = sp_client.next(results) if results['next'] else None
    except Exception as e:
        print(f"Error obteniendo tracks: {e}")
    return tracks

async def check_auth_telegram(update: Update):
    """Verifica permisos de Telegram."""
    user_id = update.message.from_user.id
    if user_id not in config.AUTHORIZED_USER_IDS:
        return False
    return True

def verify_spotify_ownership(sp_client, playlist_id, user_id):
    """Verifica si la playlist es del usuario."""
    try:
        pl_details = sp_client.playlist(playlist_id)
        owner_id = pl_details['owner']['id']
        if owner_id != user_id:
            return False, f"⛔ Error: Esta playlist es de `{owner_id}`, no tuya."
        return True, None
    except Exception as e:
        return False, f"❌ Error al verificar playlist: {str(e)}"

async def finish_task(update: Update):
    await update.message.reply_text("✨ **¡Hecho!**\n👉 /start para reiniciar", parse_mode="Markdown")
