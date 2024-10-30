"""
SRT YouTube Generator - Video Processor
-------------------------------------
Este módulo maneja el procesamiento de videos de YouTube, incluyendo:
- Descarga de videos
- Extracción de audio
- Generación de subtítulos usando OpenAI
- Creación de archivos HTML con transcripciones

Clases:
    VideoProcessor: Clase principal que maneja todo el procesamiento de videos
"""

import os
import yt_dlp
import ffmpeg
import asyncio
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from openai import AsyncOpenAI
from jinja2 import Environment, FileSystemLoader
import re

# Cargar variables de entorno
load_dotenv()

class VideoProcessor:
    """
    Clase principal para procesar videos de YouTube y generar subtítulos.
    
    Atributos:
        api_key (str): API key de OpenAI
        output_dir (Path): Directorio de salida para archivos generados
        template_dir (Path): Directorio de plantillas HTML
        jinja_env: Entorno Jinja2 para renderizar plantillas
        ydl_opts (dict): Opciones para youtube-dl
    """

    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.output_dir = Path(os.getenv('OUTPUT_DIR', 'output'))
        self.template_dir = Path('templates')
        self.jinja_env = Environment(loader=FileSystemLoader('templates'))
        self.ydl_opts = {
            'format': 'best[height<=720]',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True
        }

    def _download_video(self, url, output_dir):
        """
        Descarga un video de YouTube y extrae su audio.
        
        Args:
            url (str): URL del video de YouTube
            output_dir (Path): Directorio donde guardar los archivos
            
        Returns:
            dict: Información del video descargado
        """
        try:
            # Configurar opciones de descarga
            ydl_opts = {
                'format': 'best[height<=720]',
                'outtmpl': str(output_dir / 'video.%(ext)s'),
                'quiet': True,
                'no_warnings': True
            }

            # Descargar video y extraer información
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # Asegurar formato MP4
                video_path = list(output_dir.glob('video.*'))[0]
                if video_path.suffix != '.mp4':
                    new_path = output_dir / 'video.mp4'
                    video_path.rename(new_path)
                
                # Extraer audio en MP3
                audio_path = output_dir / 'audio.mp3'
                ffmpeg.input(str(output_dir / 'video.mp4')).output(
                    str(audio_path), 
                    acodec='libmp3lame', 
                    ab='128k'
                ).overwrite_output().run(capture_stdout=True, capture_stderr=True)

                return {
                    'title': info.get('title', ''),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'description': info.get('description', '')
                }

        except Exception as e:
            print(f"Error descargando video: {str(e)}")
            raise

    def _extract_video_id(self, url):
        """
        Extrae el ID del video de una URL de YouTube.
        
        Args:
            url (str): URL del video
            
        Returns:
            str: ID del video o None si no se encuentra
        """
        try:
            patterns = [
                r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
                r'youtu\.be\/([0-9A-Za-z_-]{11})',
                r'youtube\.com\/embed\/([0-9A-Za-z_-]{11})'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            return None
            
        except Exception as e:
            print(f"Error extrayendo ID del video: {str(e)}")
            return None

    def _generate_report(self, video_dir, video_info, url):
        """
        Genera un reporte del procesamiento del video.
        
        Args:
            video_dir (Path): Directorio del video
            video_info (dict): Información del video
            url (str): URL original del video
        """
        try:
            report_path = video_dir / 'report.txt'
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(f"URL: {url}\n")
                f.write(f"Título: {video_info['title']}\n")
                f.write(f"Duración: {video_info['duration']} segundos\n")
                f.write(f"Fecha de procesamiento: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                
        except Exception as e:
            print(f"Error generando reporte: {str(e)}")
            raise

    async def validate_api(self):
        """
        Valida la API key de OpenAI.
        
        Returns:
            bool: True si la API key es válida
        """
        try:
            client = AsyncOpenAI(api_key=self.api_key)
            await client.models.list()
            return True
        except Exception:
            return False

    async def process_video(self, url):
        """
        Procesa un video completo: descarga, genera subtítulos y HTML.
        
        Args:
            url (str): URL del video de YouTube
            
        Returns:
            bool: True si el proceso fue exitoso
        """
        client = None
        try:
            print(f"Procesando URL: {url}")
            
            # Extraer información y crear directorio
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_title = info.get('title', '').replace('/', '-')
                video_id = info.get('id', '')

            video_dir = self.output_dir / video_title
            video_dir.mkdir(parents=True, exist_ok=True)

            # Procesar video y generar archivos
            video_info = self._download_video(url, video_dir)
            client = AsyncOpenAI(api_key=self.api_key)
            
            # Generar y guardar subtítulos
            es_srt, en_srt = await self.generate_subtitles(
                str(video_dir / 'audio.mp3'),
                video_info['duration']
            )
            
            es_srt_path = video_dir / 'subtitles_es.srt'
            en_srt_path = video_dir / 'subtitles_en.srt'
            
            with open(es_srt_path, 'w', encoding='utf-8') as f:
                f.write(es_srt)
            with open(en_srt_path, 'w', encoding='utf-8') as f:
                f.write(en_srt)

            # Generar HTML y reporte
            video_data = {
                'title': video_title,
                'url': url,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            await self.generate_html(video_data, video_dir)
            self._generate_report(video_dir, video_info, url)
            
            return True

        except Exception as e:
            print(f"Error procesando video: {str(e)}")
            raise
        finally:
            if client:
                await client.close()

    async def generate_subtitles(self, audio_path, duration):
        """
        Genera subtítulos en español e inglés usando OpenAI.
        
        Args:
            audio_path (str): Ruta al archivo de audio
            duration (int): Duración del video en segundos
            
        Returns:
            tuple: (subtítulos_español, subtítulos_inglés)
        """
        print("Transcribiendo audio...")
        
        try:
            client = AsyncOpenAI(api_key=self.api_key)
            async with client:
                # Generar transcripción en español
                with open(audio_path, 'rb') as audio_file:
                    transcript = await client.audio.transcriptions.create(
                        file=audio_file,
                        model="whisper-1",
                        response_format="srt",
                        language="es"
                    )

                # Traducir a inglés usando GPT-4
                translation = await client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "Eres un traductor profesional. Traduce los subtítulos manteniendo el formato SRT."},
                        {"role": "user", "content": f"Traduce estos subtítulos al inglés:\n\n{transcript}"}
                    ]
                )

                return transcript, translation.choices[0].message.content

        except Exception as e:
            print(f"Error generando subtítulos: {str(e)}")
            raise

    def _sanitize_filename(self, filename):
        """Limpia el nombre del archivo de caracteres no válidos"""
        return "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).strip()

    def _parse_srt(self, srt_content):
        """
        Parsea el contenido SRT en una lista de diccionarios.
        
        Args:
            srt_content (str): Contenido del archivo SRT
            
        Returns:
            list: Lista de diccionarios con índice, timestamp y texto
        """
        entries = []
        current_entry = {}
        lines = srt_content.strip().split('\n')
        i = 0
        
        while i < len(lines):
            if not lines[i].strip():
                i += 1
                continue
                
            current_entry = {
                'index': lines[i],
                'timestamp': lines[i + 1],
                'text': lines[i + 2]
            }
            entries.append(current_entry)
            i += 3
            
        return entries

    def _srt_to_text(self, srt_path):
        """
        Convierte archivo SRT a texto plano.
        
        Args:
            srt_path (Path): Ruta al archivo SRT
            
        Returns:
            str: Texto plano extraído del SRT
        """
        if not srt_path.exists():
            return ""
            
        text = []
        current_text = []
        
        with open(srt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if line and not line.isdigit() and not '-->' in line:
                current_text.append(line)
            elif not line and current_text:
                text.append(' '.join(current_text))
                current_text = []
                
        if current_text:
            text.append(' '.join(current_text))
            
        return '\n\n'.join(text)

    async def generate_html(self, video_data, video_dir):
        """
        Genera el archivo HTML usando la plantilla.
        
        Args:
            video_data (dict): Datos del video
            video_dir (Path): Directorio del video
        """
        try:
            # Convertir subtítulos a texto
            es_srt_path = video_dir / 'subtitles_es.srt'
            en_srt_path = video_dir / 'subtitles_en.srt'
            
            es_text = self._srt_to_text(es_srt_path)
            en_text = self._srt_to_text(en_srt_path)

            # Preparar datos y generar HTML
            template = self.jinja_env.get_template('index.html')
            template_data = {
                'title': video_data['title'],
                'video_name': 'video.mp4',
                'audio_name': 'audio.mp3',
                'es_srt_name': 'subtitles_es.srt',
                'en_srt_name': 'subtitles_en.srt',
                'url': video_data['url'],
                'timestamp': video_data['timestamp'],
                'es_text': es_text,
                'en_text': en_text
            }

            html_content = template.render(**template_data)
            
            # Guardar HTML
            html_path = video_dir / 'index.html'
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

        except Exception as e:
            print(f"Error generando HTML: {str(e)}")
            raise