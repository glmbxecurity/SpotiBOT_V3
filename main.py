import logging
import nest_asyncio
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler, ContextTypes, filters
)

import config

# --- IMPORTACIÓN DE FUNCIONES ---
# Funciones estándar
from funcion_rank import enter_rank_mode, rank_handle_playlist, rank_handle_number
from funcion_mixer import enter_mixer_mode, mixer_set_mode_command, mixer_process_input, mixer_process_name
from funcion_updater import enter_creator_mode, creator_process_days
from funcion_sort import enter_sort_mode, process_sort_url
from funcion_top import enter_top_mode, process_top_url, process_top_number

# Funciones GYM (Actualizadas)
from funcion_gym import (
    enter_gym_mode, 
    gym_save_mode, 
    gym_save_name,      # <--- Nueva función para el nombre
    gym_process_urls, 
    GYM_SELECT_MODE, 
    GYM_ASK_NAME,       # <--- Nuevo estado intermedio
    GYM_INPUT_URLS
)

# Función HELP (Nueva)
from funcion_help import help_command

# Logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# --- MENÚ PRINCIPAL ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (
        "🎧 **Ultimate SpotiBOT v3**\n\n"
        "1️⃣ **Analizar Popularidad** (/rank)\n"
        "2️⃣ **Mezclador de Fiestas** (/mixer)\n"
        "3️⃣ **Escanear Novedades** (/updater) (YAML)\n"
        "4️⃣ **Reordenar mis Listas** (/sort)\n"
        "5️⃣ **Filtrar Mejores Canciones** (/top)\n"
        "6️⃣ **Entrenador Personal** (/gym) 🆕\n"
        "❓ **Ayuda y Configuración** (/help)\n\n"
        "❌ Cancelar operación (/cancel)"
    )
    await update.message.reply_markdown(txt)
    return config.CHOOSING_MODE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Operación cancelada. Pulsa /start para volver al menú.")
    return ConversationHandler.END

# --- INICIALIZACIÓN ---
def main():
    print("🔄 Iniciando SpotiBOT...")
    
    # 1. Autenticación Spotify
    auth_manager = SpotifyOAuth(
        client_id=config.SPOTIPY_CLIENT_ID,
        client_secret=config.SPOTIPY_CLIENT_SECRET,
        redirect_uri=config.SPOTIPY_REDIRECT_URI,
        scope=config.SCOPE,
        cache_path="token_cache.json",
        open_browser=False 
    )
    
    sp = spotipy.Spotify(auth_manager=auth_manager)
    
    # Verificación de Login
    try:
        user = sp.current_user()
        print(f"✅ Conectado a Spotify como: {user['display_name']}")
    except Exception:
        print("⚠️ ALERTA DE SEGURIDAD: Necesitas autorizar la app.")
        auth_url = auth_manager.get_authorize_url()
        print(f"🔗 Abre esta URL en tu navegador: {auth_url}")
        res = input("Pega aquí la URL a la que fuiste redirigido (localhost...): ")
        auth_manager.get_access_token(auth_manager.parse_response_code(res))
        sp = spotipy.Spotify(auth_manager=auth_manager)
        user = sp.current_user()

    # 2. Configuración Telegram
    nest_asyncio.apply()
    application = Application.builder().token(config.TELEGRAM_TOKEN).build()

    # Inyectamos cliente Spotify
    application.bot_data['sp_client'] = sp
    application.bot_data['user_id'] = user['id']

    # ---------------------------------------------------------
    # HANDLER A: MODO GYM (Prioritario)
    # ---------------------------------------------------------
    gym_handler = ConversationHandler(
        entry_points=[CommandHandler('gym', enter_gym_mode)],
        states={
            # Paso 1: Elegir modo (Ahora acepta COMANDOS como /energy o texto)
            GYM_SELECT_MODE: [
                MessageHandler(filters.COMMAND | filters.TEXT, gym_save_mode)
            ],
            # Paso 2: Pedir Nombre (Nuevo estado)
            GYM_ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, gym_save_name)],
            # Paso 3: Pedir URLs
            GYM_INPUT_URLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, gym_process_urls)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # ---------------------------------------------------------
    # HANDLER B: RESTO DE HERRAMIENTAS
    # ---------------------------------------------------------
    main_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("rank", enter_rank_mode),
            CommandHandler("mixer", enter_mixer_mode),
            CommandHandler("updater", enter_creator_mode),
            CommandHandler("sort", enter_sort_mode),
            CommandHandler("top", enter_top_mode),
            CommandHandler("help", help_command), # <--- AÑADIDO AQUÍ
        ],
        states={
            config.CHOOSING_MODE: [
                CommandHandler("rank", enter_rank_mode),
                CommandHandler("mixer", enter_mixer_mode),
                CommandHandler("updater", enter_creator_mode),
                CommandHandler("sort", enter_sort_mode),
                CommandHandler("top", enter_top_mode),
                CommandHandler("gym", enter_gym_mode),
                CommandHandler("help", help_command) # <--- AÑADIDO AQUÍ TAMBIÉN
            ],
            
            # --- RANK ---
            config.RANK_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, rank_handle_playlist)],
            config.RANK_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, rank_handle_number)],
            
            # --- MIXER ---
            config.MIXER_INPUT: [
                CommandHandler("modo", mixer_set_mode_command),
                MessageHandler(filters.TEXT & ~filters.COMMAND, mixer_process_input)
            ],
            config.MIXER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, mixer_process_name)],
            
            # --- UPDATER ---
            config.CREATOR_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, creator_process_days)],
            
            # --- SORT ---
            config.SORT_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_sort_url)],
            
            # --- TOP ---
            config.TOP_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_top_url)],
            config.TOP_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_top_number)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)]
    )

    # Añadimos los handlers (Gym primero para aislar su lógica)
    application.add_handler(gym_handler)
    application.add_handler(main_conv_handler)

    print("🤖 Bot de Telegram en línea. Pulsa /start en tu chat.")
    application.run_polling()

if __name__ == "__main__":
    main()
