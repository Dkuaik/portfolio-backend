#!/usr/bin/env python3
"""
Script simple para imprimir solo los nombres de archivos del bucket de portfolio
"""

from src.services.s3.S3Client import S3Client
import os

def main():
    # Crear una instancia del cliente S3
    s3_client = S3Client()
    
    # Nombre del bucket de portfolio
    bucket_name = os.getenv("BUCKET_NAME", "portfolio")
    
    try:
        # Obtener la lista de objetos del bucket
        objects = s3_client.list_objects(bucket_name)
        
        if not objects:
            print("No hay archivos en el bucket.")
            return
        
        print(f"Archivos en el bucket '{bucket_name}':")
        for obj in objects:
            print(obj['Key'])
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
