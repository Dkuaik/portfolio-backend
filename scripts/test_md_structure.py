#!/usr/bin/env python3
"""
Script para listar todos los archivos en el bucket de portfolio
"""

from app.services.s3.S3Client import S3Client
import os

def main():
    # Crear una instancia del cliente S3
    s3_client = S3Client()
    
    # Nombre del bucket de portfolio (puedes cambiar esto según tu configuración)
    bucket_name = os.getenv("PORTFOLIO_BUCKET_NAME", "portfolio")
    
    try:
        print(f"Listando archivos en el bucket: {bucket_name}")
        print("-" * 50)
        
        # Obtener la lista de objetos del bucket
        objects = s3_client.list_objects(bucket_name)
        
        if not objects:
            print("No se encontraron archivos en el bucket.")
            return
        
        # Imprimir información de cada archivo
        print(f"Total de archivos encontrados: {len(objects)}")
        print("-" * 50)
        
        for i, obj in enumerate(objects, 1):
            file_name = obj['Key']
            file_size = obj['Size']
            last_modified = obj['LastModified']
            
            # Convertir tamaño a formato legible
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.2f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.2f} MB"
            
            print(f"{i:3d}. {file_name}")
            print(f"     Tamaño: {size_str}")
            print(f"     Última modificación: {last_modified}")
            print()
            
    except Exception as e:
        print(f"Error al listar archivos del bucket: {str(e)}")
        print("Verifica que:")
        print("1. Las credenciales de S3 estén configuradas correctamente en el archivo .env")
        print("2. El bucket existe y tienes permisos de lectura")
        print("3. La conexión a S3 sea válida")

if __name__ == "__main__":
    main()
    # --- Bloque de prueba para guardar el primer archivo Markdown en JSON ---
    from app.services.markdown_processor import MarkdownProcessor
    import json

    BUCKET_NAME = os.getenv("PORTFOLIO_BUCKET_NAME", "portfolio")
    OUTPUT_FILE = "src/docs/md_file_structure.json"

    processor = MarkdownProcessor(BUCKET_NAME)
    archivos = processor.get_all_markdown_files()
    if archivos:
        primer_archivo = archivos[0]
        with open(OUTPUT_FILE, "+w", encoding="utf-8") as f:
            json.dump(primer_archivo, f, ensure_ascii=False, indent=2, default=str)
    else:
        print("❌ No se encontraron archivos Markdown en el bucket.")
