"""
SRT YouTube Generator - Flask Application
---------------------------------------
Este módulo implementa el servidor web Flask que maneja las peticiones para procesar
videos de YouTube, generar subtítulos y gestionar archivos.

Características principales:
- Procesamiento de videos de YouTube
- Gestión de archivos de entrada/salida
- Manejo de listas de reproducción
- API RESTful para interactuar con el frontend
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from processor import VideoProcessor
import os
from pathlib import Path
from dotenv import load_dotenv
from asgiref.sync import async_to_sync
from yt_dlp import YoutubeDL
import json
from datetime import datetime
from werkzeug.utils import secure_filename

# Cargar variables de entorno
load_dotenv()

# Inicializar aplicación Flask
app = Flask(__name__, static_url_path='/static')
processor = VideoProcessor()

# Rutas principales
@app.route('/')
def index():
    """Renderiza la página principal del dashboard"""
    return render_template('dashboard.html')

@app.route('/process', methods=['POST'])
async def process_video():
    """
    Procesa un video de YouTube
    Recibe: URL del video en formato JSON
    Retorna: Estado del procesamiento
    """
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL no proporcionada'}), 400

        processor = VideoProcessor()
        
        # Validar API key antes de procesar
        if not await processor.validate_api():
            return jsonify({'error': 'API key inválida'}), 401

        await processor.process_video(url)
        return jsonify({'success': True, 'message': 'Video procesado correctamente'})
    
    except Exception as e:
        print(f"Error en /process: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/videos')
def list_videos():
    """
    Lista todos los videos procesados en la carpeta output
    Retorna: Lista de videos con sus metadatos
    """
    output_dir = Path(os.getenv('OUTPUT_DIR', 'output'))
    videos = []
    
    if output_dir.exists():
        for video_dir in output_dir.iterdir():
            if video_dir.is_dir():
                html_file = video_dir / 'index.html'
                if html_file.exists():
                    try:
                        # Leer URL original del report.txt
                        report_file = video_dir / 'report.txt'
                        youtube_url = ''
                        if report_file.exists():
                            with open(report_file, 'r', encoding='utf-8') as f:
                                for line in f:
                                    if line.startswith('URL:'):
                                        youtube_url = line.split('URL:')[1].strip()
                                        break
                        
                        videos.append({
                            'title': video_dir.name,
                            'path': f'output/{video_dir.name}/index.html',
                            'youtubeUrl': youtube_url,
                            'timestamp': datetime.fromtimestamp(html_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                        })
                    except Exception as e:
                        print(f"Error leyendo información del video {video_dir.name}: {e}")
    
    # Ordenar por fecha de procesamiento (más reciente primero)
    videos.sort(key=lambda x: x['timestamp'], reverse=True)
    return jsonify(videos)

# Rutas para servir archivos
@app.route('/output/<path:filename>')
def serve_output(filename):
    """Sirve archivos desde la carpeta output"""
    return send_from_directory('output', filename)

@app.route('/static/<path:path>')
def send_static(path):
    """Sirve archivos estáticos"""
    return send_from_directory('static', path)

# Rutas para gestión de archivos de entrada
@app.route('/input-files')
def list_input_files():
    """Lista todos los archivos .txt en la carpeta input"""
    input_dir = Path(os.getenv('INPUT_DIR', 'input'))
    files = []
    
    if input_dir.exists():
        files = [f.name for f in input_dir.glob('*.txt')]
    
    return jsonify(files)

@app.route('/file-urls/<filename>')
def get_file_urls(filename):
    """
    Obtiene las URLs de un archivo de entrada
    Retorna: Lista de URLs y títulos
    """
    input_dir = Path(os.getenv('INPUT_DIR', 'input'))
    file_path = input_dir / filename
    
    if not file_path.exists():
        return jsonify([])
    
    try:
        urls = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split('#', 1)
                    url = parts[0].strip()
                    title = parts[1].strip() if len(parts) > 1 else ''
                    
                    if url:
                        urls.append({
                            'url': url,
                            'title': title
                        })
        return jsonify(urls)
    except Exception as e:
        print(f"Error leyendo archivo: {str(e)}")
        return jsonify([])

# Rutas para gestión de listas de reproducción
@app.route('/process-playlist', methods=['POST'])
def process_playlist():
    """
    Procesa una lista de reproducción de YouTube
    Retorna: Lista de videos en la playlist
    """
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'URL no proporcionada'}), 400

    try:
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'force_generic_extractor': False,
            'ignoreerrors': True,
            'no_warnings': True,
            'playlistreverse': False,
            'playliststart': 1,
            'playlistend': None,
            'extract_flat': 'in_playlist'
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            videos = []
            
            if 'entries' in info:
                for entry in info['entries']:
                    if entry:
                        videos.append({
                            'title': entry.get('title', ''),
                            'url': entry.get('url', '') or entry.get('webpage_url', ''),
                            'duration': entry.get('duration', 0),
                            'id': entry.get('id', '')
                        })
            elif info.get('_type') == 'url' and info.get('ie_key') == 'Youtube':
                videos.append({
                    'title': info.get('title', ''),
                    'url': info.get('webpage_url', ''),
                    'duration': info.get('duration', 0),
                    'id': info.get('id', '')
                })
            
            return jsonify({'videos': videos}) if videos else (
                jsonify({'error': 'No se encontraron videos en la playlist'}), 404
            )
    except Exception as e:
        print(f"Error procesando playlist: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/save-playlist', methods=['POST'])
def save_playlist():
    """
    Guarda los videos seleccionados de una playlist en un archivo .txt
    """
    videos = request.json.get('videos', [])
    if not videos:
        return jsonify({'error': 'No hay videos seleccionados'}), 400

    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'playlist_{timestamp}.txt'
        filepath = Path(os.getenv('INPUT_DIR', 'input')) / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            for video in videos:
                f.write(f"{video['url']} # {video['title']}\n")

        return jsonify({'message': 'Lista guardada correctamente'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Rutas para gestión de archivos
@app.route('/delete-file/<filename>', methods=['DELETE'])
def delete_file(filename):
    """Elimina un archivo de la carpeta input"""
    try:
        filepath = Path(os.getenv('INPUT_DIR', 'input')) / filename
        if filepath.exists():
            filepath.unlink()
            return jsonify({'message': 'Archivo eliminado correctamente'})
        return jsonify({'error': 'Archivo no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload-file', methods=['POST'])
def upload_file():
    """
    Maneja la subida de archivos .txt
    Valida y guarda el archivo en la carpeta input
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No se envió ningún archivo'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
    
    if not file.filename.endswith('.txt'):
        return jsonify({'error': 'Solo se permiten archivos .txt'}), 400
    
    try:
        filename = secure_filename(file.filename)
        input_dir = Path(os.getenv('INPUT_DIR', 'input'))
        input_dir.mkdir(exist_ok=True)
        
        filepath = input_dir / filename
        file.save(str(filepath))
        
        return jsonify({'message': 'Archivo subido correctamente'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Iniciar servidor en modo debug si se ejecuta directamente
if __name__ == '__main__':
    app.run(debug=True)
