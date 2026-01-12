import os

# --- CREDENCIALES ---
TELEGRAM_TOKEN = "TELEGRAM_TOKEN"
SPOTIPY_CLIENT_ID = "SPOTIFY CLIENT"
SPOTIPY_CLIENT_SECRET = "SPOTIFY SECRET"
SPOTIPY_REDIRECT_URI = "http://127.0.0.1:8888/callback"

# IDs y Permisos 
#Cada ID separado por coma, estos seran los que puedan interactuar con el bot (los que hay son de ejemplo)
AUTHORIZED_USER_IDS = {942135888, 123456789}
SCOPE = "playlist-read-private playlist-modify-private ugc-image-upload playlist-modify-public user-library-read"

# --- ESTADOS DE CONVERSACIÓN (GLOBALES) ---
# Definimos los números aquí para poder importarlos en cada función y en el main
(
    CHOOSING_MODE,       # Menú Principal
    RANK_URL, RANK_NUMBER,          # Rank
    MIXER_INPUT, MIXER_NAME,        # Mixer
    CREATOR_DAYS,                   # Updater
    SORT_URL,                       # Sort
    TOP_URL, TOP_NUMBER             # Top Filter
) = range(9)
