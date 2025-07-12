# Portfolio Backend - Contexto del Proyecto

## 🎯 Propósito

Este es un backend API inteligente diseñado para ser la columna vertebral de un portafolio personal/profesional que utiliza búsqueda semántica con IA para encontrar información relevante en documentos Markdown almacenados en la nube.

## 🏗️ Arquitectura y Tecnologías

### Core Framework
- **FastAPI** - Framework web moderno y rápido para Python
- **Python 3.12+** - Lenguaje base con tipado moderno
- **UV** - Gestor de paquetes y dependencias ultra-rápido (reemplazo de pip/poetry)

### Inteligencia Artificial y ML
- **OpenAI Embeddings** (text-embedding-3-small) - Para convertir texto en vectores
- **LangChain** - Framework para aplicaciones de IA con LLMs
- **FAISS** (Facebook AI Similarity Search) - Base de datos vectorial para búsqueda rápida
- **Semantic Search** - Búsqueda inteligente por significado, no solo palabras clave

### Almacenamiento y Datos
- **Amazon S3** - Almacenamiento de archivos Markdown en la nube
- **JSON** - Para metadatos y hashes de archivos
- **Vector Store** - Índice local de vectores para búsquedas rápidas

### DevOps y Deployment
- **Docker** - Containerización de la aplicación
- **Uvicorn** - Servidor ASGI de alto rendimiento
- **CORS** - Configurado para integración con frontend

## 🔧 Funcionalidades Principales

### 1. Procesamiento Inteligente de Documentos
- Extracción y chunking inteligente de contenido
- Generación de embeddings con OpenAI

### 2. API de Búsqueda Semántica
- Endpoints RESTful para consultas en lenguaje natural
- Resultados relevantes basados en similaridad semántica

### 3. Sistema de Cache Inteligente
- **Hash-based caching** - Solo procesa archivos modificados
- **Incremental updates** - Actualiza solo lo necesario
- **Persistent storage** - Mantiene el índice entre reinicios

## 📁 Estructura del Proyecto

```
portfolio-backend/
├── app/
│   ├── main.py
│   ├── embeddings_maker.py
│   └── ...
├── Dockerfile
├── requirements.txt
└── README.md
```

## 🚀 Flujo de Trabajo

1. **Ingesta**: Los archivos `.md` se almacenan en S3
2. **Procesamiento**: `embeddings_maker.py` los convierte en vectores
3. **Indexación**: FAISS crea un índice searchable
4. **API**: FastAPI expone endpoints para búsqueda
5. **Frontend**: Puede consumir la API para mostrar resultados

## ⚙️ Configuración

El sistema usa variables de entorno para:

- `OPENAI_API_KEY` - Para generar embeddings
- `S3_ACCESS_KEY` / `S3_SECRET_KEY` - Acceso a S3
- Configuraciones de chunking, similarity threshold, etc.

## 🎯 Caso de Uso

Este backend permite crear un portafolio inteligente donde los visitantes pueden:

- Hacer preguntas en lenguaje natural sobre tus proyectos
- Buscar información específica entre todos tus documentos
- Obtener respuestas contextuales y relevantes
- Navegar tu contenido de forma intuitiva

**Ejemplo**: Un visitante pregunta *"¿Qué proyectos has hecho con React?"* y el sistema encuentra automáticamente todos los documentos relevantes, incluso si no mencionan "React" explícitamente pero hablan de "frontend" o "componentes".

## 🐳 Docker Deployment

### Desarrollo Local

1. **Configurar variables de entorno**:
   ```bash
   cp .env.example .env
   # Editar .env con tus valores
   ```

2. **Build y run con Docker**:
   ```bash
   # Opción 1: Script automatizado
   ./scripts/run_docker.sh
   
   # Opción 2: Docker Compose
   docker-compose up --build
   
   # Opción 3: Comandos manuales
   docker build -t portfolios-backend:latest .
   docker run --env-file .env -p 8000:8000 portfolios-backend:latest
   ```

3. **Acceder a la API**:
   - API: http://localhost:8000
   - Documentación: http://localhost:8000/docs
   - Health Check: http://localhost:8000/api/v1/health

### Producción con Dokploy

1. **Configurar variables en Dokploy**:
   - Usar las variables definidas en `.env.prod.dokploy`
   - Formato: `{{project.VARIABLE_NAME}}`

2. **Deploy**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Características del Dockerfile

- **Multi-stage build** - Optimizado para producción
- **UV package manager** - Instalación ultra-rápida de dependencias  
- **Non-root user** - Seguridad mejorada
- **Health checks** - Monitoreo automático
- **Layer caching** - Builds incrementales eficientes