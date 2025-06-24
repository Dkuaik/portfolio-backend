from src.services.s3.S3Client import S3Client
import os
from datetime import datetime

def download_all_md_files():
    """
    Descarga todos los archivos .md del bucket 'portfolio' y los guarda en una lista
    """
    try:
        # Crear instancia del cliente S3
        s3_client = S3Client()
        bucket_name = "portfolio"
        
        # Obtener todos los objetos con extensión .md
        md_objects = s3_client.get_objects_by_extension(bucket_name, "md")
        
        if not md_objects:
            print("No se encontraron archivos .md en el bucket.")
            return []
        
        print(f"Encontrados {len(md_objects)} archivos .md en el bucket '{bucket_name}':")
        print("-" * 60)
        
        # Lista para guardar el contenido de los archivos .md
        md_files_content = []
        
        for obj in md_objects:
            file_key = obj['Key']
            print(f"Descargando: {file_key}")
            
            try:
                # Obtener el contenido del archivo
                content = s3_client.get_object_content(bucket_name, file_key)
                
                if content:
                    file_info = {
                        'filename': file_key,
                        'content': content,
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'etag': obj['ETag'],
                        'download_timestamp': datetime.now(),
                        'line_count': len(content.split('\n')),
                        'char_count': len(content)
                    }
                    md_files_content.append(file_info)
                    
                    print(f"  ✓ Descargado exitosamente")
                    print(f"  📊 Tamaño: {obj['Size']} bytes")
                    print(f"  📝 Líneas: {len(content.split('\n'))}")
                    print(f"  🔤 Caracteres: {len(content)}")
                    print()
                else:
                    print(f"  ❌ Error: No se pudo obtener el contenido")
                    print()
                    
            except Exception as e:
                print(f"  ❌ Error descargando {file_key}: {str(e)}")
                print()
        
        print(f"Descarga completada. Total de archivos .md procesados: {len(md_files_content)}")
        return md_files_content
        
    except Exception as e:
        print(f"Error general: {str(e)}")
        return []

def save_md_files_locally(md_files_list, output_dir="downloaded_md_files"):
    """
    Guarda los archivos .md descargados localmente
    """
    try:
        # Crear directorio si no existe
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        saved_files = []
        
        for file_info in md_files_list:
            # Crear nombre de archivo local seguro
            filename = file_info['filename'].replace('/', '_')
            local_path = os.path.join(output_dir, filename)
            
            # Guardar el contenido
            with open(local_path, 'w', encoding='utf-8') as f:
                f.write(file_info['content'])
            
            saved_files.append(local_path)
            print(f"Guardado localmente: {local_path}")
        
        print(f"Total de archivos guardados localmente: {len(saved_files)}")
        return saved_files
        
    except Exception as e:
        print(f"Error guardando archivos localmente: {str(e)}")
        return []

def print_md_file_contents(md_files_list, max_lines_per_file=20):
    """
    Imprime el contenido de los archivos .md descargados
    """
    for file_info in md_files_list:
        print(f"\n{'='*80}")
        print(f"📄 ARCHIVO: {file_info['filename']}")
        print(f"📊 Tamaño: {file_info['size']} bytes | Líneas: {file_info['line_count']} | Caracteres: {file_info['char_count']}")
        print(f"🕒 Última modificación: {file_info['last_modified']}")
        print(f"⬇️  Descargado: {file_info['download_timestamp']}")
        print(f"{'='*80}")
        
        lines = file_info['content'].split('\n')
        
        if max_lines_per_file and len(lines) > max_lines_per_file:
            print(f"Mostrando las primeras {max_lines_per_file} líneas de {len(lines)} totales:\n")
            for i, line in enumerate(lines[:max_lines_per_file], 1):
                print(f"{i:3d}: {line}")
            print(f"\n... ({len(lines) - max_lines_per_file} líneas más) ...")
        else:
            print("Contenido completo:\n")
            for i, line in enumerate(lines, 1):
                print(f"{i:3d}: {line}")
        
        print(f"\n{'='*80}\n")

def search_in_md_files(md_files_list, search_term):
    """
    Busca un término en todos los archivos .md descargados
    """
    results = []
    
    for file_info in md_files_list:
        lines = file_info['content'].split('\n')
        matches = []
        
        for line_num, line in enumerate(lines, 1):
            if search_term.lower() in line.lower():
                matches.append({
                    'line_number': line_num,
                    'line_content': line.strip()
                })
        
        if matches:
            results.append({
                'filename': file_info['filename'],
                'matches': matches,
                'total_matches': len(matches)
            })
    
    if results:
        print(f"\n🔍 Resultados de búsqueda para '{search_term}':")
        print("-" * 60)
        
        for result in results:
            print(f"\n📄 {result['filename']} ({result['total_matches']} coincidencias):")
            for match in result['matches']:
                print(f"  Línea {match['line_number']}: {match['line_content']}")
    else:
        print(f"\n❌ No se encontraron coincidencias para '{search_term}'")
    
    return results

if __name__ == "__main__":
    # Descargar todos los archivos .md
    md_files = download_all_md_files()
    
    if md_files:
        # Mostrar el contenido (primeras 20 líneas de cada archivo)
        print_md_file_contents(md_files, max_lines_per_file=20)
        
        # Guardar archivos localmente (opcional)
        # save_md_files_locally(md_files)
        
        # Ejemplo de búsqueda (opcional)
        # search_in_md_files(md_files, "readme")



