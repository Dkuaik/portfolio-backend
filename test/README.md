# Tests para EmbeddingService

Este directorio contiene tests completos para el servicio de embeddings del backend del portfolio.

## Estructura de Tests

### `test_embedding_service.py`
Tests básicos y fundamentales del servicio:
- ✅ Inicialización del servicio
- ✅ Funciones de hashing (SHA256)
- ✅ Carga y guardado de hashes
- ✅ Procesamiento de embeddings (casos felices)
- ✅ Búsqueda semántica
- ✅ Estadísticas del servicio
- ✅ Manejo de errores básicos
- ✅ Test de integración completo

### `test_embedding_service_advanced.py`
Tests avanzados y casos edge:
- ✅ Manejo de errores de permisos
- ✅ Archivos corrompidos
- ✅ Excepciones del loader
- ✅ Parámetros extremos en búsquedas
- ✅ Performance con documentos grandes
- ✅ Updates incrementales
- ✅ Estadísticas detalladas
- ✅ Recuperación de errores

### `conftest.py`
Fixtures compartidos:
- `mock_settings`: Configuración mock para tests
- `temp_dir`: Directorio temporal para cada test
- `sample_documents`: Documentos de ejemplo
- `mock_openai_embeddings`: Mock de embeddings de OpenAI
- `mock_faiss_store`: Mock del vector store FAISS

### `test_utils.py`
Utilidades para tests:
- Creación de documentos de prueba
- Constantes para tests
- Funciones helper

## Ejecutar Tests

### Opción 1: Script automatizado
```bash
./scripts/run_tests.sh
```

### Opción 2: Comandos individuales
```bash
# Solo tests básicos
python -m pytest test/test_embedding_service.py -v

# Solo tests avanzados
python -m pytest test/test_embedding_service_advanced.py -v

# Todos los tests
python -m pytest test/ -v

# Tests con cobertura (requiere pytest-cov)
python -m pytest test/ --cov=app.services.embedding_service --cov-report=html
```

## Cobertura de Tests

Los tests cubren:

### Funcionalidades Core ✅
- Inicialización del servicio
- Carga y procesamiento de documentos
- Generación de embeddings
- Búsqueda semántica
- Gestión de hashes para cambios incrementales
- Estadísticas del servicio

### Casos Edge ✅
- Archivos no existentes
- Permisos insuficientes
- JSON corrompido
- Conexiones S3 fallidas
- Vector store no disponible
- Parámetros inválidos

### Performance ✅
- Procesamiento de documentos grandes
- Updates incrementales eficientes
- Búsquedas con diferentes umbrales

### Integración ✅
- Workflow completo: cargar → procesar → buscar
- Integración entre componentes

## Dependencias de Test

```toml
[tool.uv]
dev-dependencies = [
    "pytest>=7.0.0",
    "pytest-mock>=3.10.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
]
```

## Mocks Utilizados

### OpenAI Embeddings
- Mock para evitar llamadas reales a la API
- Embeddings sintéticos para tests

### FAISS Vector Store
- Mock del índice vectorial
- Simulación de búsquedas con scores

### S3/Markdown Loader
- Mock de carga de documentos
- Control de excepciones de red

### File System
- Directorios temporales
- Simulación de errores de permisos

## Consejos de Testing

1. **Aislamiento**: Cada test usa directorios temporales únicos
2. **Mocking**: Se evitan llamadas a servicios externos (OpenAI, S3)
3. **Determinismo**: Los tests son repetibles y no dependen del estado externo
4. **Performance**: Los tests son rápidos (< 1 segundo total)
5. **Coverage**: Se cubren tanto casos felices como casos de error

## Agregar Nuevos Tests

Para agregar tests nuevos:

1. **Tests básicos**: Agregar a `test_embedding_service.py`
2. **Tests avanzados**: Agregar a `test_embedding_service_advanced.py`
3. **Fixtures nuevos**: Agregar a `conftest.py`
4. **Utilidades**: Agregar a `test_utils.py`

### Ejemplo de nuevo test:
```python
def test_nueva_funcionalidad(self, embedding_service, sample_documents):
    """Test para nueva funcionalidad"""
    # Arrange
    expected_result = "valor_esperado"
    
    # Act
    result = embedding_service.nueva_funcionalidad(sample_documents)
    
    # Assert
    assert result == expected_result
```

## Troubleshooting

### Error: "Vector store not available"
- El servicio necesita procesar embeddings antes de buscar
- Verificar mocks de FAISS

### Error: "Permission denied" 
- Tests usan directorios temporales con permisos correctos
- Verificar paths en fixtures

### Error: "OpenAI API key"
- Los tests usan mocks, no requieren API key real
- Verificar que los mocks estén configurados

### Tests lentos
- Verificar que no se estén haciendo llamadas reales a APIs
- Usar mocks para todas las operaciones I/O
