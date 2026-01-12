import os
import datetime
import base64
import random # <--- Nuevo import para la aleatoriedad
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
import config
from utils import check_auth_telegram, finish_task

# Definimos los estados (Añadido nuevo estado intermedio)
GYM_SELECT_MODE, GYM_ASK_NAME, GYM_INPUT_URLS = range(3)

# Constante: 90 minutos en milisegundos
MIN_DURATION_MS = 90 * 60 * 1000 

async def enter_gym_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Paso 1: Menú con Comandos Clicables"""
    if not await check_auth_telegram(update): return ConversationHandler.END
    
    txt = (
        "💪 **ENTRENADOR PERSONAL SPOTIBOT**\n\n"
        "Voy a crear una sesión de **+90 minutos** única y variada.\n"
        "Pulsa sobre el comando del modo que prefieras:\n\n"
        "⚡ **Modo Energía** -> Pulsa /energy\n"
        "   *Filtro:* Las más potentes y rápidas.\n\n"
        "🔥 **Modo Hype** -> Pulsa /hype\n"
        "   *Filtro:* Hits famosos con ritmo.\n\n"
        "⭐ **Modo Favoritas** -> Pulsa /bangers\n"
        "   *Filtro:* Tus top tracks + energía.\n\n"
        "❌ Cancelar -> /cancel"
    )
    
    # Eliminamos teclados antiguos si los hubiera
    await update.message.reply_markdown(txt, reply_markup=ReplyKeyboardRemove())
    return GYM_SELECT_MODE

async def gym_save_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Paso 2: Guardar modo y pedir NOMBRE personalizado"""
    text = update.message.text.lower()
    
    # Configuración de mapeo según el comando pulsado
    mode_config = {}
    
    if "/energy" in text: 
        mode_config = {"code": "energy", "base_title": "Gym Energy", "img": "Gym Energy.jpg"}
    elif "/hype" in text: 
        mode_config = {"code": "hype", "base_title": "Gym Hype Popular", "img": "Gym Hype Popular.jpg"}
    elif "/bangers" in text: 
        mode_config = {"code": "favorites", "base_title": "Gym Bangers Favoritos", "img": "Gym Bangers Favoritos.jpg"}
    else:
        await update.message.reply_text("⚠️ Comando no reconocido. Por favor pulsa /energy, /hype o /bangers.")
        return GYM_SELECT_MODE
        
    context.user_data['gym_config'] = mode_config
    
    await update.message.reply_text(
        f"✅ Modo seleccionado: **{mode_config['base_title']}**\n\n"
        "✍️ **¿Qué nombre le ponemos a esta sesión?**\n"
        "Escribe una etiqueta corta (ej: *Verano*, *Hardcore*, *Mañanero*).\n"
        "La playlist se llamará: `Gym Energy <TuEtiqueta> 2026`"
    )
    return GYM_ASK_NAME

async def gym_save_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Paso 3: Guardar nombre y pedir URLs"""
    custom_name = update.message.text.strip()
    
    # Guardamos el nombre en la configuración
    context.user_data['gym_config']['custom_name'] = custom_name
    
    img_name = context.user_data['gym_config']['img']
    
    await update.message.reply_text(
        f"📝 Etiqueta guardada: **{custom_name}**\n"
        f"🖼️ Buscando imagen: `{img_name}`\n\n"
        "🔗 **Último paso:** Envíame los enlaces de las playlists origen (separados por espacio).",
        parse_mode="Markdown"
    )
    return GYM_INPUT_URLS

async def gym_process_urls(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Paso 4: Procesamiento con Aleatoriedad y Round Robin"""
    text = update.message.text.strip()
    sp = context.bot_data['sp_client']
    user_id = context.bot_data['user_id']
    
    # Recuperamos configuración
    config_data = context.user_data.get('gym_config')
    mode = config_data['code']
    base_title = config_data['base_title']
    custom_name = config_data['custom_name']
    image_filename = config_data['img']
    
    # --- 1. LIMPIEZA DE IDS ---
    clean_text = text.replace(",", " ").replace("\n", " ")
    parts = clean_text.split()
    valid_pids = []
    for part in parts:
        if "playlist/" in part:
            try:
                pid = part.split("playlist/")[1].split("?")[0].strip()
                if pid not in valid_pids: valid_pids.append(pid)
            except: pass
            
    if not valid_pids:
        await update.message.reply_text("⚠️ No vi enlaces válidos.")
        return GYM_INPUT_URLS

    await update.message.reply_text(f"🎲 Aplicando factor aleatorio a {len(valid_pids)} playlists...")

    try:
        # --- 2. RECOLECTAR CANCIONES ---
        playlists_data = {pid: [] for pid in valid_pids}
        total_tracks = 0

        for pid in valid_pids:
            seen = set()
            try:
                res = sp.playlist_items(pid)
                while res:
                    for item in res['items']:
                        if item.get('track') and item['track'].get('id'):
                            t = item['track']
                            if t['id'] not in seen:
                                playlists_data[pid].append({
                                    'id': t['id'], 
                                    'uri': t['uri'], 
                                    'duration': t['duration_ms'], 
                                    'popularity': t['popularity']
                                })
                                seen.add(t['id'])
                    res = sp.next(res) if res['next'] else None
                total_tracks += len(playlists_data[pid])
            except Exception as e: print(f"Err {pid}: {e}")

        if total_tracks == 0:
            await update.message.reply_text("❌ Listas vacías.")
            return ConversationHandler.END

        # --- 3. AUDIO FEATURES ---
        all_ids = []
        for tracks in playlists_data.values():
            all_ids.extend([t['id'] for t in tracks])
        
        feat_map = {}
        for i in range(0, len(all_ids), 100):
            try:
                feats = sp.audio_features(all_ids[i:i+100])
                for f in feats:
                    if f: feat_map[f['id']] = f['energy']
            except: pass

        for tracks in playlists_data.values():
            for t in tracks:
                t['energy'] = feat_map.get(t['id'], 0)

        # --- 4. PREPARAR ORDENACIÓN (CON ALEATORIEDAD) ---
        # Definimos una función de puntuación con "Jitter" (Ruido aleatorio)
        # Esto hace que el orden cambie ligeramente cada vez
        
        def get_score(track, mode, is_fav=False):
            # El jitter es un número pequeño entre -0.05 y 0.05
            jitter = random.uniform(-0.05, 0.05) 
            
            if mode == "energy":
                return track['energy'] + jitter
            elif mode == "hype":
                # Si tiene poca energía penaliza mucho, si no, ordena por popularidad + azar
                if track['energy'] < 0.55: return -1 
                return track['popularity'] + (jitter * 100) # Jitter escala a popularidad
            elif mode == "favorites":
                # Favoritas tienen prioridad máxima (100), resto por energía
                base = 100 if is_fav else track['energy']
                return base + jitter
            return 0

        # Identificar favoritas si hace falta
        my_fav_ids = set()
        if mode == "favorites":
            try:
                for r in ['short_term', 'medium_term']:
                    top = sp.current_user_top_tracks(limit=50, time_range=r)
                    for i in top['items']: my_fav_ids.add(i['id'])
            except: pass

        # ORDENAR CADA LISTA INTERNAMENTE
        for pid, tracks in playlists_data.items():
            tracks.sort(key=lambda x: get_score(x, mode, x['id'] in my_fav_ids), reverse=True)

        # --- 5. ALGORITMO CREMALLERA (ROUND ROBIN) ---
        final_uris = []
        current_ms = 0
        origins_count = {pid: 0 for pid in valid_pids}
        max_len = max(len(t) for t in playlists_data.values()) if playlists_data else 0

        for i in range(max_len):
            if current_ms >= MIN_DURATION_MS: break
            for pid in valid_pids:
                if current_ms >= MIN_DURATION_MS: break
                if i < len(playlists_data[pid]):
                    track = playlists_data[pid][i]
                    if track['uri'] not in final_uris:
                        final_uris.append(track['uri'])
                        current_ms += track['duration']
                        origins_count[pid] += 1

        total_min = int(current_ms / 60000)

        # --- 6. CREAR / ACTUALIZAR PLAYLIST ---
        year = datetime.date.today().year
        # NOMBRE: Gym Energy Matutino 2026
        final_pl_name = f"{base_title} {custom_name} {year}"
        
        pl_id = None
        created_new = False

        # Buscar si existe
        try:
            user_pls = sp.current_user_playlists(limit=50)
            for pl in user_pls['items']:
                if pl['name'] == final_pl_name:
                    pl_id = pl['id']
                    break
        except: pass

        if not pl_id:
            new_pl = sp.user_playlist_create(user_id, final_pl_name, public=False, description=f"SpotiBOT Session ({custom_name}) - {total_min} min")
            pl_id = new_pl['id']
            created_new = True
        else:
            sp.playlist_replace_items(pl_id, [])

        # Subir Imagen (.jpg)
        img_path = f"images/{image_filename}"
        if os.path.exists(img_path):
            try:
                with open(img_path, "rb") as img_file:
                    sp.playlist_upload_cover_image(pl_id, base64.b64encode(img_file.read()))
            except Exception as e: print(f"Error imagen: {e}")

        # Llenar
        for i in range(0, len(final_uris), 100):
            sp.playlist_add_items(pl_id, final_uris[i:i+100])

        action = "CREADA" if created_new else "ACTUALIZADA"
        
        await update.message.reply_text(
            f"🏋️‍♂️ **¡SESIÓN {action}!**\n\n"
            f"🏷️ Nombre: **{final_pl_name}**\n"
            f"⏱ Duración: **{total_min} min**\n"
            f"🎲 Aleatoriedad: Aplicada ✅\n"
            f"🎵 Tracks: {len(final_uris)}\n\n"
            "¡A entrenar! 🔥"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        print(f"ERROR: {e}")

    await finish_task(update)
    return ConversationHandler.END
