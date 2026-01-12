import os
import datetime
import base64
import yaml  # Necesitas 'pip install PyYAML'
from datetime import timedelta
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

# Importamos las configuraciones y utilidades de tus otros archivos
import config
from utils import load_txt_set, save_txt_set, finish_task, check_auth_telegram

async def enter_creator_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth_telegram(update): return ConversationHandler.END
    
    # VERIFICACIÓN DE ARCHIVO YAML
    if not os.path.exists("playlists.yaml"):
        await update.message.reply_text("⚠️ ERROR: No encuentro el archivo 'playlists.yaml'.\nAsegúrate de que está en la misma carpeta que el bot.")
        return ConversationHandler.END
        
    await update.message.reply_text("🆕 **MODO ACTUALIZADOR (YAML)**\nIntroduce antigüedad en días (ej: 7).")
    return config.CREATOR_DAYS

async def creator_process_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sp = context.bot_data['sp_client']
    user_id = context.bot_data['user_id']
    
    try:
        days = int(update.message.text.strip())
    except: days = 7
    
    await update.message.reply_text(f"🚀 Leyendo playlists.yaml ({days} días)...")
    msg_log = ""
    
    try:
        # --- 1. CARGA DE CONFIGURACIÓN YAML ---
        playlists_map = {}
        total_found_in_yaml = 0
        
        try:
            with open("playlists.yaml", "r", encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f)
                
            if not yaml_data:
                await update.message.reply_text("⚠️ El archivo playlists.yaml está vacío o mal formateado.")
                return ConversationHandler.END

            print("\n--- INICIANDO LECTURA DEL YAML ---")
            for item in yaml_data:
                url = item.get('url', '')
                genre = item.get('genre', '')
                name = item.get('name', 'Sin nombre')
                
                # VALIDACIONES DE URL
                if "playlist/" not in url:
                    print(f"❌ SALTADO: {name} -> La URL no parece válida (Falta '/playlist/'): {url}")
                    continue
                
                if not genre:
                    print(f"❌ SALTADO: {name} -> Falta el género.")
                    continue

                try:
                    # Extraer ID: soporta URLs con ?si=... y sin él
                    pid = url.split("playlist/")[1].split("?")[0]
                    clean_genre = genre.strip()
                    
                    if clean_genre not in playlists_map: 
                        playlists_map[clean_genre] = []
                    
                    playlists_map[clean_genre].append(pid)
                    total_found_in_yaml += 1
                    print(f"✅ CARGADO: {name} ({clean_genre}) -> ID: {pid}")

                except Exception as e:
                    print(f"❌ ERROR parseando URL de {name}: {e}")

            if total_found_in_yaml == 0:
                await update.message.reply_text("⚠️ Leí el archivo YAML pero no encontré ninguna playlist válida.\nRevisa la consola para ver los errores de las URLs.")
                return ConversationHandler.END

        except Exception as e:
            await update.message.reply_text(f"❌ Error leyendo archivo YAML: {str(e)}")
            return ConversationHandler.END
        
        # --- 2. PROCESAMIENTO ---
        global_tracks = load_txt_set("global_tracks.txt")
        cutoff = datetime.datetime.now(datetime.timezone.utc) - timedelta(days=days)

        for genre, pids in playlists_map.items():
            target_name = f"{genre} {datetime.date.today().year}"
            target_id = None
            
            # Buscar/Crear playlist destino
            try:
                user_pls = sp.current_user_playlists(limit=50)
                for pl in user_pls['items']:
                    if pl['name'] == target_name:
                        target_id = pl['id']
                        break
            except: pass
            
            if not target_id:
                new_pl = sp.user_playlist_create(user_id, target_name, public=False, description=f"SpotiBOT Auto: {genre}")
                target_id = new_pl['id']
                
                # --- LOGICA DE IMAGEN MEJORADA (FALLBACK) ---
                specific_img = f"images/{genre}.jpg"
                generic_img = "images/Generic Playlist.jpg"
                final_img_path = None

                # 1. Buscamos la específica del género
                if os.path.exists(specific_img):
                    final_img_path = specific_img
                    print(f"📸 Usando imagen específica para {genre}")
                # 2. Si no, buscamos la genérica
                elif os.path.exists(generic_img):
                    final_img_path = generic_img
                    print(f"⚠️ No hay imagen para '{genre}'. Usando Genérica.")
                
                # 3. Subimos la que hayamos encontrado
                if final_img_path:
                    try:
                        with open(final_img_path, "rb") as img:
                            sp.playlist_upload_cover_image(target_id, base64.b64encode(img.read()))
                    except Exception as e:
                        print(f"❌ Error subiendo imagen: {e}")
                # ---------------------------------------------

            tracks_to_add = []
            
            # Procesar orígenes
            for pid in pids:
                local_hist_path = f"data/{pid}_tracks.txt"
                local_hist = load_txt_set(local_hist_path)
                new_local = []
                
                try:
                    res = sp.playlist_items(pid)
                    while res:
                        for item in res['items']:
                            if not item.get('track'): continue
                            tid = item['track']['id']
                            turi = item['track']['uri']
                            try:
                                added = datetime.datetime.strptime(item['added_at'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc)
                                if added >= cutoff:
                                    if tid not in local_hist and tid not in global_tracks:
                                        tracks_to_add.append(turi)
                                        global_tracks.add(tid)
                                        new_local.append(tid)
                            except: pass
                        res = sp.next(res) if res['next'] else None
                    if new_local: save_txt_set(local_hist_path, new_local)
                except Exception as e:
                    print(f"Err {pid}: {e}")

            if tracks_to_add:
                unique = list(set(tracks_to_add))
                # Añadir en lotes de 100
                for i in range(0, len(unique), 100):
                    sp.playlist_add_items(target_id, unique[i:i+100])
                save_txt_set("global_tracks.txt", list(global_tracks)) 
                msg_log += f"✅ {genre}: +{len(unique)}\n"
            else:
                msg_log += f"💤 {genre}: 0\n"

        await update.message.reply_text(f"🏁 **Resumen:**\n{msg_log}")

    except Exception as e:
        await update.message.reply_text(f"❌ Error crítico: {str(e)}")

    await finish_task(update)
    return ConversationHandler.END
