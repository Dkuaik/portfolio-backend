from app.services.markdown_processor import MarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from pathlib import Path
import hashlib
import json

def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

# ------- Configuración -------

S3_BUBKET_NAME = "portfolio"  # Nombre del bucket S3 donde se almacenan los archivos Markdown
STORE_DIR = Path ("vectorstores/portfolio_index")
HASH_FILE = Path ("vectorstores/portfolio_hashes.json")
CHUNCK_SIZE = 1000  # Tamaño máximo de cada fragmento
CHUNK_OVERLAP = 200  # Superposición entre fragmentos
EMB_MODEL = "text-embedding-3-small"  # Modelo de embeddings de OpenAI


def main():
    """
    Función principal que procesa documentos Markdown desde S3,
    crea embeddings y construye un índice de vectores con FAISS.
    """
    # se cargan los hashes de los documentos procesados previamente
    prev_hashes = {}
    if HASH_FILE.exists():
        prev_hashes = json.loads(HASH_FILE.read_text())

    # Carga de documentos Markdown desde un bucket S3 

    # Esta clase se encarga de cargar archivos Markdown desde un bucket S3 y convertirlos en documentos de LangChain.
    # con un singleton de la clase MarkdownProcessor
    loader = MarkdownLoader(
        bucket_name=S3_BUBKET_NAME,
    )

    documents = loader.load()

    # Filtrar solo documentos nuevos/cambiados
    new_docs, kept_docs = [], []
    current_hashes = {}                 # se irá llenando

    for doc in documents:
        key   = doc.metadata["key"]          # adapta si tu campo se llama distinto
        h     = sha256(doc.page_content)  # calcula el hash del contenido del documento
        current_hashes[key] = h                # guarda hash igual lo proceses o no
        if prev_hashes.get(key) != h:
            new_docs.append(doc)               # requiere re-embeddings
        else:
            kept_docs.append(doc)              # sin cambios

    print(f"→ {len(new_docs)} docs modificados / {len(kept_docs)} sin cambios")

    # Si no hay nada nuevo, sal del script
    if not new_docs:
        print("No hay cambios. Índice sigue vigente ✅")
        return 0

    # Dividir los documentos en fragmentos más pequeños
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size= CHUNCK_SIZE ,  # Tamaño máximo de cada fragmento
        chunk_overlap=CHUNK_OVERLAP  # Superposición entre fragmentos
    )

    chunks = text_splitter.split_documents(new_docs)

    #creación de embeddings con OpenAIEmbeddings
    embedings = OpenAIEmbeddings(model=EMB_MODEL)

    # Construccion de index de vectores con FAISS
    vector_store = FAISS.from_documents(chunks, embedings)

    # Guardar el índice de vectores en un directorio local
    if not STORE_DIR.exists():
        STORE_DIR.mkdir(parents=True, exist_ok=True)
    vector_store.save_local(STORE_DIR.as_posix())
    
    # Guardar los hashes actualizados
    HASH_FILE.parent.mkdir(parents=True, exist_ok=True)
    HASH_FILE.write_text(json.dumps(current_hashes, indent=2))
    
    print("✅ Índice de vectores creado y guardado exitosamente")


if __name__ == "__main__":
    main()