# 🎥 SRT YouTube Generator

Un procesador y generador de transcripciones y subtítulos de videos de YouTube que genera páginas web con esas transcripciones, los videos en mp4, el audio en mp3, los subtítulos en srt y un reporte.

## ✨ Características

- 📥 Descarga videos de YouTube
- 🔊 Extrae el audio
- 📝 Genera transcripciones en español
- 🌍 Traduce al inglés
- 🎯 Genera archivos SRT (subtítulos):
  - `subtitles_es.srt` - Subtítulos en español
  - `subtitles_en.srt` - Subtítulos en inglés
- 🎬 Crea una página web con:
  - Video reproductor
  - Transcripción bilingüe
  - Subtítulos descargables
  - Recursos multimedia

## 🛠️ Tecnologías

- Python 3.8+
- Flask (Servidor web)
- OpenAI API (Transcripción y traducción)
- yt-dlp (Descarga de videos)
- FFmpeg (Procesamiento de audio/video)
- Jinja2 (Plantillas HTML)

## 📋 Requisitos

- Python 3.8 o superior
- FFmpeg instalado en el sistema
- Clave API de OpenAI
- Dependencias de Python listadas en `requirements.txt`

## 🚀 Instalación

1. Clonar el repositorio
2. Instalar dependencias:

```bash
pip install -r requirements.txt
```
3. Crear archivo `.env` con la API key de OpenAI:
```env
OPENAI_API_KEY=tu_api_key_aquí

## 📁 Estructura de Carpetas

### Carpeta Input
La carpeta `input/` es donde debes colocar los archivos .txt con las URLs de YouTube:

- Crear la carpeta si no existe: `mkdir input`
- Formato del archivo .txt:
  ```txt
  https://www.youtube.com/watch?v=VIDEO_ID_1 # Título del video 1
  https://www.youtube.com/watch?v=VIDEO_ID_2 # Título del video 2
  ```

### Carpeta Output
La carpeta `output/` es donde se generarán todos los archivos procesados:

- Se crea automáticamente al procesar videos
- Cada video tiene su propia subcarpeta
- Estructura por video:
  ```
  output/
  ├── [nombre-video]/
  │   ├── index.html        # Página web con reproductor
  │   ├── video.mp4         # Video descargado
  │   ├── audio.mp3         # Audio extraído
  │   ├── subtitles_es.srt  # Subtítulos en español
  │   ├── subtitles_en.srt  # Subtítulos en inglés
  │   └── report.txt        # Reporte del proceso
  ```

## 💻 Uso

### Interfaz Web

1. Iniciar el servidor:
```bash
python app.py
```
2. Acceder a `http://localhost:5000`
3. Opciones disponibles:
   - Subir archivo .txt con URLs
   - Procesar lista de reproducción de YouTube
   - Procesar URLs individuales

### Procesamiento de Videos

#### Por Archivo
1. Crear archivo .txt en la carpeta `input/`
2. Añadir URLs de YouTube (una por línea)
3. Subir el archivo desde la interfaz web

#### Por Lista de Reproducción
1. Copiar URL de la lista de reproducción de YouTube
2. Pegar en la sección "Procesar Lista"
3. Seleccionar videos a procesar
4. Iniciar procesamiento

## 🔍 Formato de Subtítulos SRT

Los archivos SRT generados siguen el formato estándar:

1
00:00:01,000 --> 00:00:04,000
Texto del subtítulo en español/inglés

2
00:00:04,001 --> 00:00:08,000
Siguiente línea de subtítulos

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue primero para discutir los cambios que te gustaría hacer.

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.


