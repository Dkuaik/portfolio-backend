import boto3
from botocore.client import Config
import dotenv
import os
import io
import json
from datetime import datetime
# Load environment variables from .env file
dotenv.load_dotenv()

class S3Client:
    def __init__(self, endpoint_url=None, access_key=None, secret_key=None, region_name="us-east-1"):
        self.s3 = boto3.client(
            's3',
            endpoint_url=endpoint_url or os.getenv("S3_ENDPOINT_URL"),
            aws_access_key_id=access_key or os.getenv("S3_ACCESS_KEY"),
            aws_secret_access_key=secret_key or os.getenv("S3_SECRET_KEY"),
            region_name=region_name,
            config=Config(signature_version='s3v4')
        )

    def upload_file(self, file_path, bucket_name, object_name):
        self.s3.upload_file(file_path, bucket_name, object_name)

    def download_file(self, bucket_name, object_name, file_path):
        self.s3.download_file(bucket_name, object_name, file_path)

    def list_objects(self, bucket_name, prefix=""):
        response = self.s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        return response.get('Contents', [])

    def create_bucket(self, bucket_name):
        self.s3.create_bucket(Bucket=bucket_name)

    def delete_object(self, bucket_name, object_name):
        self.s3.delete_object(Bucket=bucket_name, Key=object_name)

    def get_object_content(self, bucket_name, object_name):
        """
        Obtiene el contenido de un objeto como string
        """
        try:
            response = self.s3.get_object(Bucket=bucket_name, Key=object_name)
            return response['Body'].read().decode('utf-8')
        except Exception as e:
            print(f"Error obteniendo contenido de {object_name}: {e}")
            return None

    def get_object_content_bytes(self, bucket_name, object_name):
        """
        Obtiene el contenido de un objeto como bytes (para archivos binarios)
        """
        try:
            response = self.s3.get_object(Bucket=bucket_name, Key=object_name)
            return response['Body'].read()
        except Exception as e:
            print(f"Error obteniendo contenido de {object_name}: {e}")
            return None

    def download_fileobj(self, bucket_name, object_name, fileobj):
        """
        Descarga un archivo a un objeto tipo archivo en memoria
        """
        try:
            self.s3.download_fileobj(bucket_name, object_name, fileobj)
            return True
        except Exception as e:
            print(f"Error descargando {object_name}: {e}")
            return False

    def upload_from_string(self, content, bucket_name, object_name, content_type='text/plain'):
        """
        Sube contenido desde un string directamente a S3
        """
        try:
            self.s3.put_object(
                Bucket=bucket_name,
                Key=object_name,
                Body=content.encode('utf-8'),
                ContentType=content_type
            )
            return True
        except Exception as e:
            print(f"Error subiendo contenido a {object_name}: {e}")
            return False

    def upload_from_bytes(self, content_bytes, bucket_name, object_name, content_type='application/octet-stream'):
        """
        Sube contenido desde bytes directamente a S3
        """
        try:
            self.s3.put_object(
                Bucket=bucket_name,
                Key=object_name,
                Body=content_bytes,
                ContentType=content_type
            )
            return True
        except Exception as e:
            print(f"Error subiendo bytes a {object_name}: {e}")
            return False

    def copy_object(self, source_bucket, source_key, dest_bucket, dest_key):
        """
        Copia un objeto de una ubicación a otra en S3
        """
        try:
            copy_source = {'Bucket': source_bucket, 'Key': source_key}
            self.s3.copy_object(
                CopySource=copy_source,
                Bucket=dest_bucket,
                Key=dest_key
            )
            return True
        except Exception as e:
            print(f"Error copiando objeto: {e}")
            return False

    def move_object(self, source_bucket, source_key, dest_bucket, dest_key):
        """
        Mueve un objeto (copia y luego elimina el original)
        """
        try:
            # Copiar el objeto
            if self.copy_object(source_bucket, source_key, dest_bucket, dest_key):
                # Eliminar el original
                self.delete_object(source_bucket, source_key)
                return True
            return False
        except Exception as e:
            print(f"Error moviendo objeto: {e}")
            return False

    def get_object_metadata(self, bucket_name, object_name):
        """
        Obtiene los metadatos de un objeto
        """
        try:
            response = self.s3.head_object(Bucket=bucket_name, Key=object_name)
            return {
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag'),
                'metadata': response.get('Metadata', {}),
                'storage_class': response.get('StorageClass'),
                'server_side_encryption': response.get('ServerSideEncryption'),
                'version_id': response.get('VersionId')
            }
        except Exception as e:
            print(f"Error obteniendo metadatos de {object_name}: {e}")
            return None

    def object_exists(self, bucket_name, object_name):
        """
        Verifica si un objeto existe en el bucket
        """
        try:
            self.s3.head_object(Bucket=bucket_name, Key=object_name)
            return True
        except:
            return False

    def get_object_size(self, bucket_name, object_name):
        """
        Obtiene el tamaño de un objeto en bytes
        """
        try:
            response = self.s3.head_object(Bucket=bucket_name, Key=object_name)
            return response.get('ContentLength', 0)
        except Exception as e:
            print(f"Error obteniendo tamaño de {object_name}: {e}")
            return 0

    def list_objects_detailed(self, bucket_name, prefix="", max_keys=1000):
        """
        Lista objetos con información detallada
        """
        try:
            response = self.s3.list_objects_v2(
                Bucket=bucket_name, 
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            objects = response.get('Contents', [])
            detailed_objects = []
            
            for obj in objects:
                # Obtener metadatos adicionales
                metadata = self.get_object_metadata(bucket_name, obj['Key'])
                
                detailed_obj = {
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag'],
                    'storage_class': obj.get('StorageClass', 'STANDARD'),
                    'content_type': metadata.get('content_type') if metadata else None,
                    'metadata': metadata.get('metadata', {}) if metadata else {}
                }
                detailed_objects.append(detailed_obj)
            
            return detailed_objects
        except Exception as e:
            print(f"Error listando objetos detallados: {e}")
            return []

    def search_objects(self, bucket_name, search_term, prefix=""):
        """
        Busca objetos que contengan el término de búsqueda en su nombre
        """
        try:
            objects = self.list_objects(bucket_name, prefix)
            filtered_objects = [
                obj for obj in objects 
                if search_term.lower() in obj['Key'].lower()
            ]
            return filtered_objects
        except Exception as e:
            print(f"Error buscando objetos: {e}")
            return []

    def get_objects_by_extension(self, bucket_name, extension, prefix=""):
        """
        Obtiene todos los objetos con una extensión específica
        """
        try:
            objects = self.list_objects(bucket_name, prefix)
            filtered_objects = [
                obj for obj in objects 
                if obj['Key'].lower().endswith(f'.{extension.lower()}')
            ]
            return filtered_objects
        except Exception as e:
            print(f"Error filtrando por extensión: {e}")
            return []

    def print_file_content(self, bucket_name, object_name, max_lines=None):
        """
        Imprime el contenido de un archivo de texto
        """
        try:
            content = self.get_object_content(bucket_name, object_name)
            if content:
                print(f"\n{'='*60}")
                print(f"Contenido de: {object_name}")
                print(f"{'='*60}")
                
                lines = content.split('\n')
                if max_lines:
                    lines = lines[:max_lines]
                    if len(content.split('\n')) > max_lines:
                        print(f"... mostrando solo las primeras {max_lines} líneas ...")
                
                for i, line in enumerate(lines, 1):
                    print(f"{i:4d}: {line}")
                
                print(f"{'='*60}\n")
            else:
                print(f"No se pudo leer el contenido de {object_name}")
        except Exception as e:
            print(f"Error imprimiendo contenido: {e}")

    def get_file_info_summary(self, bucket_name, object_name):
        """
        Obtiene un resumen completo de información del archivo
        """
        try:
            metadata = self.get_object_metadata(bucket_name, object_name)
            if not metadata:
                return None
            
            # Determinar tipo de archivo
            file_type = "Desconocido"
            if metadata.get('content_type'):
                if metadata['content_type'].startswith('text/'):
                    file_type = "Texto"
                elif metadata['content_type'].startswith('image/'):
                    file_type = "Imagen"
                elif metadata['content_type'].startswith('application/'):
                    file_type = "Aplicación"
            
            summary = {
                'nombre': object_name,
                'tamaño_bytes': metadata.get('content_length', 0),
                'tamaño_legible': self._format_file_size(metadata.get('content_length', 0)),
                'tipo_contenido': metadata.get('content_type', 'application/octet-stream'),
                'tipo_archivo': file_type,
                'ultima_modificacion': metadata.get('last_modified'),
                'etag': metadata.get('etag'),
                'clase_almacenamiento': metadata.get('storage_class', 'STANDARD'),
                'cifrado': metadata.get('server_side_encryption', 'Ninguno'),
                'metadatos_personalizados': metadata.get('metadata', {})
            }
            
            return summary
        except Exception as e:
            print(f"Error obteniendo resumen del archivo: {e}")
            return None

    def _format_file_size(self, size_bytes):
        """
        Convierte bytes a formato legible (KB, MB, GB)
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.2f} {size_names[i]}"

    def backup_object(self, bucket_name, object_name, backup_suffix="_backup"):
        """
        Crea una copia de respaldo de un objeto
        """
        try:
            # Generar nombre de backup con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{object_name}{backup_suffix}_{timestamp}"
            
            return self.copy_object(bucket_name, object_name, bucket_name, backup_name)
        except Exception as e:
            print(f"Error creando backup: {e}")
            return False