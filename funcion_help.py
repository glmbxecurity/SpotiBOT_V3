from telegram import Update
from telegram.ext import ContextTypes

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envía un mensaje de ayuda detallado."""
    
    txt_intro = "📚 **AYUDA DE SPOTIBOT v3**\n\nAquí tienes la guía rápida de uso."

    txt_comandos = (
        "🎮 **1. COMANDOS PRINCIPALES**\n\n"
        "🔸 **/rank** (Ranking): Le pasas una playlist y te dice cuáles son las canciones más famosas y cuáles las desconocidas.\n"
        "🔸 **/mixer** (Mezclador): Une varias playlists en una sola. Ideal para fiestas.\n"
        "🔸 **/updater** (Novedades): Busca canciones nuevas en las listas que configures en el archivo YAML, y crea o actualiza playlists por genero.\n"
        "🔸 **/sort** (Ordenar): Ordena permanentemente una de TUS playlists de mayor a menor fama.\n"
        "🔸 **/top** (Filtrar): Borra la paja de tu playlist y deja solo las 'N' mejores canciones.\n"
        "🔸 **/gym** (Entrenador): Crea sesiones de +90min filtrando por Energía, Hits o tus Favoritas."
    )

    txt_updater = (
        "⚙️ **2. CÓMO CONFIGURAR EL UPDATER**\n\n"
        "Para que el comando `/updater` funcione, debes editar el archivo `playlists.yaml` que está en la carpeta del bot.\n\n"
        "📝 **Formato del archivo YAML:**\n"
        "Debes seguir esta estructura exacta (cuidado con los espacios al inicio):\n"
        "```yaml\n"
        "- name: \"Techno 2026\"\n"
        "  genre: \"Hard Techno\"\n"
        "  url: \"[https://open.spotify.com/playlist/](https://open.spotify.com/playlist/)...\"\n\n"
        "- name: \"Otra Lista\"\n"
        "  genre: \"House\"\n"
        "  url: \"...\"\n"
        "```\n\n"
        "🖼️ **Cómo poner portadas:**\n"
        "El bot buscará automáticamente una imagen para ponerle a la playlist generada.\n"
        "1. **Nombre:** Debe llamarse IGUAL que el `genre` que pusiste en el YAML.\n"
        "   *Ejemplo:* Si `genre: \"Hard Techno\"`, la imagen debe ser `Hard Techno.jpg`.\n"
        "2. **Ubicación:** Guárdala en la carpeta `images/`.\n"
        "3. **Formato:** Preferiblemente **.jpg** (Spotify a veces falla con PNG).\n"
        "4. **Tamaño:** Cuadrada y maximo 500x500 y que pese menos de 500kb."
    )
    
    txt_tips = (
        "💡 **CONSEJOS EXTRA**\n"
        "• Usa **/cancel** en cualquier momento si te equivocas o el bot se queda esperando.\n"
        "• En el modo **/gym**, asegúrate de tener las imágenes `Gym Energy.jpg`, `Gym Hype Popular.jpg` y `Gym Bangers Favoritos.jpg` en la carpeta `images/`."
    )

    # Enviamos los mensajes por partes para no saturar la pantalla
    await update.message.reply_markdown(txt_intro)
    await update.message.reply_markdown(txt_comandos)
    await update.message.reply_markdown(txt_updater)
    await update.message.reply_markdown(txt_tips)
