import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from app.services.s3.S3Client import S3Client
from langchain.document_loaders.base import BaseLoader
from langchain_core.documents import Document

class MarkdownProcessor:
    """
    Procesador de archivos Markdown para manejo eficiente de documentos almacenados en S3.
        
        Esta clase proporciona funcionalidades completas para:
        - Obtener y procesar archivos Markdown desde buckets de S3
        - Extraer metadatos, estadísticas y contenido de los archivos
        - Generar resúmenes y reportes de los documentos
        - Filtrar archivos según diferentes criterios
        - Exportar información a formatos JSON
        
        Nota: Aunque esta es la clase base del modelo, en la práctica se recomienda usar
        MarkdownProcessorSingleton.get_instance() para garantizar una única instancia
        y optimizar el uso de recursos, especialmente las conexiones S3.
    """
    def __init__(self, bucket_name: str):
        """
        Inicializa el procesador de archivos Markdown
        
        Args:
            bucket_name: Nombre del bucket de S3
        """
        self.s3_client = S3Client()
        self.bucket_name = bucket_name
        
    def get_all_markdown_files(self, prefix: str = "") -> List[Dict]:
        """
        Obtiene todos los archivos .md del bucket y los organiza en una lista de objetos

        Args:
            prefix: Prefijo para filtrar archivos por ruta
        
        Returns:
            Lista de diccionarios con información de cada archivo Markdown. Cada objeto tiene el siguiente formato:

            Ejemplo:
            [
                {
                "key":  key of the file in S3 as a string,
                "filename": filename of the file as a string,
                "path": path of the file in S3 as a string,
                "size_bytes": size of the file in bytes as an integer,
                "size_readable": size of the file in a human-readable format as a string,
                "last_modified": last modified date of the file as a datetime object,
                "content": "content of the file as a string in Markdown format",
                "content_length": content length in bytes,
                "word_count": int,
                "line_count": int,
                "has_content": bool,
                "metadata": {},
                "preview": "This is a preview of the content, truncated to 150 characters",
                "headers": array of headers found in the Markdown file
                }
                ...
            ]
        """
        try:
            # Obtener todos los archivos .md
            markdown_objects = self.s3_client.get_objects_by_extension(
                self.bucket_name, 
                "md", 
                prefix
            )
            
            markdown_files = []
            
            print(f"📁 Procesando {len(markdown_objects)} archivos Markdown...")
            
            for i, obj in enumerate(markdown_objects, 1):
                print(f"⏳ Procesando archivo {i}/{len(markdown_objects)}: {obj['Key']}")
                
                # Obtener información detallada del archivo
                file_info = self.s3_client.get_file_info_summary(self.bucket_name, obj['Key'])
                
                # Obtener contenido del archivo
                content = self.s3_client.get_object_content(self.bucket_name, obj['Key'])
                
                # Crear objeto con toda la información
                markdown_file = {
                    'content': content,
                    "metadata":{
                    'key': obj['Key'],
                    'filename': os.path.basename(obj['Key']),
                    'path': os.path.dirname(obj['Key']),
                    'size_bytes': obj['Size'],
                    'size_readable': self._format_file_size(obj['Size']),
                    'last_modified': obj['LastModified'],
                    'content_length': len(content) if content else 0,
                    'word_count': len(content.split()) if content else 0,
                    'line_count': len(content.split('\n')) if content else 0,
                    'has_content': bool(content and content.strip()),
                    'metadata': file_info.get('metadatos_personalizados', {}) if file_info else {},
                    'preview': self._get_content_preview(content) if content else "",
                    'headers': self._extract_markdown_headers(content) if content else []
                }
                }
                
                
                
                markdown_files.append(markdown_file)
            
            print(f"✅ Procesados {len(markdown_files)} archivos Markdown exitosamente")
            return markdown_files
            
        except Exception as e:
            print(f"❌ Error obteniendo archivos Markdown: {e}")
            return []
    
    def get_markdown_files_summary(self, prefix: str = "") -> Dict:
        """
        Obtiene un resumen de todos los archivos Markdown
        
        Args:
            prefix: Prefijo para filtrar archivos
            
        Returns:
            Diccionario con resumen estadístico
        """
        files = self.get_all_markdown_files(prefix)
        
        if not files:
            return {"error": "No se encontraron archivos Markdown"}
        
        total_size = sum(f['size_bytes'] for f in files)
        total_words = sum(f['word_count'] for f in files)
        total_lines = sum(f['line_count'] for f in files)
        
        summary = {
            'total_files': len(files),
            'total_size_bytes': total_size,
            'total_size_readable': self._format_file_size(total_size),
            'total_words': total_words,
            'total_lines': total_lines,
            'average_file_size': total_size // len(files) if files else 0,
            'average_words_per_file': total_words // len(files) if files else 0,
            'files_with_content': len([f for f in files if f['has_content']]),
            'empty_files': len([f for f in files if not f['has_content']]),
            'largest_file': max(files, key=lambda x: x['size_bytes']) if files else None,
            'smallest_file': min(files, key=lambda x: x['size_bytes']) if files else None,
            'most_recent': max(files, key=lambda x: x['last_modified']) if files else None
        }
        
        return summary
    
    def print_markdown_files(self, prefix: str = "", show_content: bool = False):
        """
        Imprime información de todos los archivos Markdown
        
        Args:
            prefix: Prefijo para filtrar archivos
            show_content: Si mostrar el contenido completo o solo preview
        """
        files = self.get_all_markdown_files(prefix)
        
        if not files:
            print("❌ No se encontraron archivos Markdown")
            return
        
        print(f"\n{'='*80}")
        print(f"📄 ARCHIVOS MARKDOWN ENCONTRADOS: {len(files)}")
        print(f"{'='*80}")
        
        for i, file in enumerate(files, 1):
            print(f"\n🔹 Archivo {i}: {file['filename']}")
            print(f"   📁 Ruta: {file['key']}")
            print(f"   📏 Tamaño: {file['size_readable']} ({file['size_bytes']:,} bytes)")
            print(f"   📝 Palabras: {file['word_count']:,}")
            print(f"   📋 Líneas: {file['line_count']:,}")
            print(f"   📅 Modificado: {file['last_modified']}")
            print(f"   ✅ Tiene contenido: {'Sí' if file['has_content'] else 'No'}")
            
            if file['headers']:
                print(f"   📑 Encabezados: {', '.join(file['headers'][:3])}...")
            
            if show_content and file['content']:
                print(f"   📄 Contenido completo:")
                print(f"   {'-'*60}")
                for line_num, line in enumerate(file['content'].split('\n')[:20], 1):
                    print(f"   {line_num:3d}: {line}")
                if file['line_count'] > 20:
                    print(f"   ... ({file['line_count'] - 20} líneas más)")
            elif file['preview']:
                print(f"   👀 Preview: {file['preview']}")
        
        # Mostrar resumen
        summary = self.get_markdown_files_summary(prefix)
        print(f"\n{'='*80}")
        print(f"📊 RESUMEN")
        print(f"{'='*80}")
        print(f"📁 Total de archivos: {summary['total_files']}")
        print(f"📏 Tamaño total: {summary['total_size_readable']}")
        print(f"📝 Palabras totales: {summary['total_words']:,}")
        print(f"📋 Líneas totales: {summary['total_lines']:,}")
        print(f"✅ Archivos con contenido: {summary['files_with_content']}")
        print(f"❌ Archivos vacíos: {summary['empty_files']}")
        
        if summary['largest_file']:
            print(f"🔝 Archivo más grande: {summary['largest_file']['filename']} ({summary['largest_file']['size_readable']})")
        
        if summary['most_recent']:
            print(f"🆕 Más reciente: {summary['most_recent']['filename']}")
    
    def save_markdown_list_to_json(self, output_file: str, prefix: str = ""):
        """
        Guarda la lista de archivos Markdown en un archivo JSON
        
        Args:
            output_file: Ruta del archivo JSON de salida
            prefix: Prefijo para filtrar archivos
        """
        try:
            files = self.get_all_markdown_files(prefix)
            summary = self.get_markdown_files_summary(prefix)
            
            output_data = {
                'timestamp': datetime.now().isoformat(),
                'bucket_name': self.bucket_name,
                'prefix': prefix,
                'summary': summary,
                'files': files
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"✅ Lista guardada en: {output_file}")
            print(f"📁 {len(files)} archivos procesados")
            
        except Exception as e:
            print(f"❌ Error guardando archivo JSON: {e}")
    
    def filter_markdown_files(self, files: List[Dict], **filters) -> List[Dict]:
        """
        Filtra archivos Markdown según criterios específicos
        
        Args:
            files: Lista de archivos Markdown
            **filters: Filtros a aplicar (min_size, max_size, has_content, etc.)
            
        Returns:
            Lista filtrada de archivos
        """
        filtered = files.copy()
        
        if 'min_size' in filters:
            filtered = [f for f in filtered if f['size_bytes'] >= filters['min_size']]
        
        if 'max_size' in filters:
            filtered = [f for f in filtered if f['size_bytes'] <= filters['max_size']]
        
        if 'has_content' in filters:
            filtered = [f for f in filtered if f['has_content'] == filters['has_content']]
        
        if 'min_words' in filters:
            filtered = [f for f in filtered if f['word_count'] >= filters['min_words']]
        
        if 'contains_text' in filters:
            text = filters['contains_text'].lower()
            filtered = [f for f in filtered if text in f['content'].lower()]
        
        if 'filename_pattern' in filters:
            pattern = filters['filename_pattern'].lower()
            filtered = [f for f in filtered if pattern in f['filename'].lower()]
        
        return filtered
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Convierte bytes a formato legible"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        size = float(size_bytes)
        i = 0
        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024
            i += 1
        
        return f"{size:.2f} {size_names[i]}"
    
    def _get_content_preview(self, content: str, max_length: int = 150) -> str:
        """Obtiene un preview del contenido"""
        if not content:
            return ""
        
        # Limpiar el contenido
        clean_content = content.strip().replace('\n', ' ').replace('\r', '')
        
        if len(clean_content) <= max_length:
            return clean_content
        
        return clean_content[:max_length] + "..."
    
    def _extract_markdown_headers(self, content: str) -> List[str]:
        """Extrae los encabezados de un archivo Markdown"""
        if not content:
            return []
        
        headers = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('#'):
                # Extraer el texto del encabezado
                header_text = line.lstrip('#').strip()
                if header_text:
                    headers.append(header_text)
        
        return headers

class MarkdownProcessorSingleton:
    _instance = None

    @classmethod
    def get_instance(cls, bucket_name: str):
        if cls._instance is None:
            cls._instance = MarkdownProcessor(bucket_name)
        return cls._instance

class MarkdownLoader(BaseLoader):
    """
    Cargador de archivos Markdown para LangChain
    Permite cargar archivos Markdown desde un bucket de S3 y convertirlos en documentos LangChain.
    
    """
    def __init__(self, bucket_name: str, prefix: str = ""):
        self.bucket_name = bucket_name
        self.prefix = prefix
        self.processor = MarkdownProcessorSingleton.get_instance(bucket_name)

    def load(self) -> List[Document]:
        files = self.processor.get_all_markdown_files(self.prefix)
        return [Document(page_content=file['content'], metadata=file['metadata']) for file in files if file['metadata']['has_content']]


if __name__ == "__main__":
    # Este bloque se deja vacío para evitar ejecución directa
    pass
