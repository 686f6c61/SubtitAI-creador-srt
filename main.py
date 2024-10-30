import asyncio
from processor import VideoProcessor
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

class Menu:
    def __init__(self):
        self.processor = VideoProcessor()

    async def main_menu(self):
        # Validar API key
        print("Validando API key...")
        if not await self.processor.validate_api():
            print("Error: API key inválida")
            return

        while True:
            print("\n=== YouTube Processor ===")
            print("1. Procesar archivo de URLs")
            print("2. Procesar URL específica")
            print("3. Salir")
            
            option = input("\nSeleccione una opción: ")
            
            if option == "1":
                await self.process_all()
            elif option == "2":
                await self.process_single()
            elif option == "3":
                break
            else:
                print("Opción no válida")

    async def process_all(self):
        input_file = Path(os.getenv('INPUT_FILE', 'input/videos.txt'))
        
        if not input_file.exists():
            print(f"Archivo no encontrado: {input_file}")
            return

        with open(input_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]

        print(f"\nEncontradas {len(urls)} URLs")
        print("1. Procesar todas")
        print("2. Seleccionar una")
        
        option = input("\nSeleccione una opción: ")
        
        if option == "1":
            for url in urls:
                print(f"\nProcesando: {url}")
                await self.processor.process_video(url)
        elif option == "2":
            for i, url in enumerate(urls, 1):
                print(f"{i}. {url}")
            try:
                idx = int(input("\nSeleccione número de URL: ")) - 1
                if 0 <= idx < len(urls):
                    await self.processor.process_video(urls[idx])
                else:
                    print("Índice no válido")
            except ValueError:
                print("Entrada no válida")

    async def process_single(self):
        url = input("\nIntroduzca la URL de YouTube: ")
        if url.strip():
            await self.processor.process_video(url)

if __name__ == "__main__":
    menu = Menu()
    asyncio.run(menu.main_menu())