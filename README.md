# 🎧 Ultimate SpotiBOT v3

**Ultimate SpotiBOT v3** es un bot de Telegram avanzado escrito en Python que actúa como tu asistente personal para gestionar, analizar y automatizar tu cuenta de Spotify. Desde crear las sesiones de entrenamiento perfectas hasta mantener tus playlists actualizadas automáticamente.
![image](https://raw.githubusercontent.com/glmbxecurity/SpotiBOT_V3/refs/heads/main/images/spotibot4.png)
---

## 1. ¿Qué es y qué hace?

Este proyecto permite interactuar con la API de Spotify directamente desde Telegram. Su arquitectura es modular, dividiendo cada herramienta en una función específica.

### 🛠️ Funciones Principales

#### 🏋️‍♂️ **/gym (Entrenador Personal)**
Crea sesiones de entrenamiento de **+90 minutos** basándose en playlists que le envíes. Utiliza un algoritmo de **"Cremallera" (Round Robin)** para asegurar una mezcla equitativa de todas las fuentes y aplica un factor de **aleatoriedad** para que la sesión nunca sea idéntica.
* **Modo Energía (`/energy`):** Selecciona las canciones más rápidas y potentes (BPM y Energía altos).
* **Modo Hype (`/hype`):** Filtra canciones con energía decente y las ordena por Popularidad Global (Hits).
* **Modo Favoritas (`/bangers`):** Cruza las playlists con tu historial de "Top Tracks". Prioriza lo que te gusta y rellena el resto con energía.
* **Persistencia Inteligente:** Si la playlist ya existe (ej: "Gym Energy 2026"), la vacía y actualiza en lugar de crear una nueva, manteniendo a tus seguidores.

#### 🚀 **/updater (Escanear Novedades)**
Es un sistema de automatización basado en el archivo `playlists.yaml`.
* Escanea listas de terceros (ej: Playlists editoriales de Spotify).
* Busca canciones añadidas en los últimos `X` días.
* Las agrupa por **Género** y las añade a tus propias playlists anuales (ej: "Hard Techno 2026").
* **Gestión de Imágenes:** Intenta poner una portada específica (`Genero.jpg`). Si no existe, usa una genérica (`Generic Playlist.jpg`).

#### 🍹 **/mixer (Mezclador)**
Fusiona múltiples playlists en una sola.
* **Modo Normal:** Elimina duplicados.
* **Modo Mix:** Intercala canciones de las distintas listas para una mezcla fluida.

#### 📊 **/rank (Analizar Popularidad)**
Le envías una playlist y devuelve un ranking de las canciones ordenadas por su índice de popularidad actual en Spotify. Ideal para descubrir "Hidden Gems" o ver cuáles son los hits comerciales.

#### 🧹 **/sort (Reordenar Listas)**
Toma una de **tus** playlists y reordena las canciones permanentemente de mayor a menor popularidad.

#### ✂️ **/top (Top Filter)**
Filtra una playlist existente, manteniendo solo las `N` mejores canciones (según popularidad) y eliminando el resto.

---

### 🧠 Memoria y Persistencia del Bot

El bot utiliza varios archivos locales para ser eficiente y no duplicar trabajo:

1. **`token_cache.json`**:
   * Guarda el token de acceso de Spotify. Esto permite que el bot siga funcionando sin pedirte que te loguees cada vez que se reinicia.
2. **`global_tracks.txt`**:
   * Usado por la función `/updater`. Es un registro histórico de canciones que el bot ya ha procesado y añadido a tus listas. Evita que la misma canción se añada dos veces, incluso si aparece en diferentes listas de origen.
3. **Carpeta `data/`**:
   * Contiene archivos como `{playlist_id}_tracks.txt`. Son historiales locales por playlist para saber qué canciones ya se han escaneado de esa fuente específica.

---

## 2. Instalación de Dependencias

El bot está construido en **Python 3**. Necesitas instalar las siguientes librerías para que funcione:

```bash
pip install python-telegram-bot spotipy pyyaml nest_asyncio
```

* `python-telegram-bot`: Para interactuar con Telegram.
* `spotipy`: La librería oficial para la API de Spotify.
* `pyyaml`: Para leer la configuración de `playlists.yaml`.
* `nest_asyncio`: Para gestionar bucles de eventos asíncronos.

---

## 3. Configuración y Puesta en Marcha

### Paso 1: Crear el Bot de Telegram
1. Abre Telegram y busca a **@BotFather**.
2. Envía el comando `/newbot`.
3. Ponle un nombre y un usuario. BotFather te dará un **Token** (ej: `123456:ABC-DEF...`).
4. Copia ese token en el archivo `config.py` en la variable `TELEGRAM_TOKEN`.
5. **Importante:** Obtén tu ID de usuario de Telegram (puedes usar el bot @userinfobot) y añádelo a `AUTHORIZED_USER_IDS` en `config.py` para que el bot te haga caso.

### Paso 2: Configurar Spotify Developer
1. Ve al [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
2. Inicia sesión y pulsa "Create App".
3. Dale un nombre y descripción.
4. En la configuración de la App, busca **Redirect URIs** y añade exactamente:
   `http://127.0.0.1:8888/callback`
5. Copia el **Client ID** y el **Client Secret**.
6. Pégalos en tu archivo `config.py` en las variables correspondientes.

### Paso 3: Primer Inicio (Login)
1. Ejecuta el bot desde la terminal:
   ```bash
   python3 main.py
   ```
2. La primera vez, la terminal te mostrará un mensaje de advertencia y un enlace URL.
3. Copia ese enlace y ábrelo en tu navegador (en el PC donde uses Spotify habitualmente).
4. Acepta los permisos de Spotify.
5. Serás redirigido a una página que probablemente de error (localhost), pero la URL habrá cambiado. **Copia la URL completa de la barra de direcciones**.
6. Pégala en la terminal donde está corriendo el bot y pulsa Enter.
7. El bot guardará el `token_cache.json` y ya estará conectado para siempre.

### Paso 4: Servicio (Opcional)
Puedes configurar `main.py` para que se ejecute como un servicio del sistema (Systemd en Debian/Ubuntu o OpenRC en Alpine) para que arranque automáticamente si reinicias el servidor.

---

## 4. Configuración Avanzada

### Archivo `playlists.yaml` (Para /updater)
Este archivo define qué listas debe escanear el bot para buscar música nueva. Debe estar en la misma carpeta que `main.py`.

**Estructura:**
```yaml
- name: "Nombre Identificativo"
  genre: "Nombre del Genero"
  url: "[https://open.spotify.com/playlist/](https://open.spotify.com/playlist/)..."

- name: "Techno Bunker Source"
  genre: "Techno"
  url: "[https://open.spotify.com/playlist/](https://open.spotify.com/playlist/)..."
```
* **genre:** Es clave. El bot creará una playlist llamada `Nombre del Genero 202X` y buscará una imagen con ese mismo nombre.

### Imágenes de Portada
Para que el bot suba portadas automáticamente a las playlists creadas (tanto en `/gym` como en `/updater`), debes guardar las imágenes en la carpeta `images/`.

* **Formato:** `.jpg` (Recomendado, máximo 500x500px y <500KB).
* **Nombres obligatorios para Gym:**
  * `Gym Energy.jpg`
  * `Gym Hype Popular.jpg`
  * `Gym Bangers Favoritos.jpg`
* **Nombres para Updater:** Deben coincidir con el `genre` del YAML (ej: `Techno.jpg`).
* **Imagen por defecto:** Si no encuentra la imagen del género, el bot buscará `Generic Playlist.jpg`.
