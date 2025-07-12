import requests
import json
import logging
import os
import time
from typing import List, Optional, Dict, Any
from app.core.config import settings  # Importar configuración centralizada

class OpenRouterAPI:
    def __init__(self, api_key=None, model=None, temperature=None, max_tokens=None, 
                 response_format=None, top_p=None, frequency_penalty=None, presence_penalty=None):
        """
        Clase para realizar peticiones a la API de OpenRouter.
        """
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        if not self.api_key:
            raise ValueError("API key must be provided either as parameter or in settings")

        self.model = model or settings.OPENROUTER_MODEL
        self.temperature = temperature or settings.OPENROUTER_TEMPERATURE
        self.max_tokens = max_tokens or settings.OPENROUTER_MAX_TOKENS
        self.response_format = response_format
        self.top_p = top_p or 1
        self.frequency_penalty = frequency_penalty or 0
        self.presence_penalty = presence_penalty or 0
        self.url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def send_request(self, messages, response_format=None):
        """
        Envía una solicitud a OpenRouter con los mensajes proporcionados.
        :param messages: Lista de mensajes en formato [{"role": "system|user|assistant", "content": "mensaje"}, ...]
        :param response_format: Formato de respuesta deseado (e.g., {"type": "json_object"})
        Retorna la respuesta directa de la API o lanza una excepción si algo falla.
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "stream": False
        }

        if response_format is not None:
            payload["response_format"] = response_format

        response = requests.post(self.url, headers=self.headers, json=payload)
        response.raise_for_status()
        time.sleep(1)
        return response.json()
    
    def send_request_with_embeddings(self, 
                                   user_query: str, 
                                   embedding_service=None,
                                   max_context_results: int = 3, 
                                   similarity_threshold: float = 0.3,
                                   system_prompt: Optional[str] = None,
                                   response_format: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Envía una solicitud a OpenRouter usando embeddings para proporcionar contexto relevante.
        
        :param user_query: La consulta del usuario
        :param embedding_service: Instancia del servicio de embeddings (si no se proporciona, se importa)
        :param max_context_results: Número máximo de resultados de contexto a incluir
        :param similarity_threshold: Umbral de similitud para filtrar resultados
        :param system_prompt: Prompt del sistema personalizado (opcional)
        :param response_format: Formato de respuesta deseado
        :return: Respuesta de la API con información adicional sobre el contexto usado
        """
        try:
            # Importar EmbeddingService si no se proporciona
            if embedding_service is None:
                from app.services.embedding_service import EmbeddingService
                embedding_service = EmbeddingService.get_instance()
            
            # Buscar contexto relevante usando embeddings
            context_chunks = embedding_service.search(
                query=user_query,
                max_results=max_context_results,
                threshold=similarity_threshold
            )
            
            # Construir el contexto desde los chunks encontrados
            context_texts = []
            context_sources = []
            
            for chunk in context_chunks:
                context_texts.append(f"**Fuente: {chunk.metadata.source}**\n{chunk.content}")
                context_sources.append({
                    "source": chunk.metadata.source,
                    "key": chunk.metadata.key,
                    "score": chunk.score
                })
            
            # Crear el prompt del sistema con el contexto
            if system_prompt is None:
                system_prompt = """Eres un asistente experto que responde preguntas basándose en información específica proporcionada. 
Usa únicamente la información del contexto proporcionado para responder. Si la información no está en el contexto, indica que no tienes esa información específica."""
            
            context_text = "\n\n---\n\n".join(context_texts) if context_texts else "No se encontró contexto relevante."
            
            full_system_prompt = f"""{system_prompt}

CONTEXTO RELEVANTE:
{context_text}

Responde basándote en este contexto."""
            
            # Preparar los mensajes
            messages = [
                {"role": "system", "content": full_system_prompt},
                {"role": "user", "content": user_query}
            ]
            
            # Enviar la solicitud
            api_response = self.send_request(messages, response_format)
            
            # Agregar información sobre el contexto usado
            return {
                "response": api_response,
                "context_used": {
                    "chunks_found": len(context_chunks),
                    "sources": context_sources,
                    "query": user_query,
                    "threshold": similarity_threshold
                },
                "success": True
            }
            
        except Exception as e:
            return {
                "response": None,
                "context_used": {
                    "chunks_found": 0,
                    "sources": [],
                    "query": user_query,
                    "threshold": similarity_threshold
                },
                "error": str(e),
                "success": False
            }
    
    def chat_with_context(self, user_query: str, context_query: Optional[str] = None) -> Dict[str, Any]:
        """
        Función simplificada para chat con contexto de embeddings.
        
        :param user_query: La pregunta o consulta del usuario
        :param context_query: Query específico para buscar contexto (si es diferente al user_query)
        :return: Respuesta estructurada con el resultado del chat
        """
        # Usar la query de contexto o la query del usuario
        search_query = context_query if context_query else user_query
        
        return self.send_request_with_embeddings(
            user_query=user_query,
            max_context_results=3,
            similarity_threshold=0.3,
            system_prompt="""Eres un asistente que ayuda a responder preguntas sobre proyectos y experiencia profesional. 
Usa la información del contexto proporcionado para dar respuestas precisas y útiles."""
        )


# Función de utilidad para usar directamente
def chat_with_portfolio_context(user_query: str, 
                               model: str = "google/gemini-2.5-flash-lite-preview-06-17",
                               temperature: float = 0.7) -> Dict[str, Any]:
    """
    Función de utilidad para hacer chat con contexto del portfolio.
    
    :param user_query: La consulta del usuario
    :param model: Modelo a usar
    :param temperature: Temperatura para la respuesta
    :return: Respuesta estructurada
    """
    client = OpenRouterAPI(model=model, temperature=temperature, max_tokens=1000)
    return client.chat_with_context(user_query)


if __name__ == "__main__":
    # Ejemplo de uso
    try:
        # Usando la clase directamente
        client = OpenRouterAPI()
        result = client.chat_with_context("¿Qué proyectos de IA has desarrollado?")
        
        if result["success"]:
            print("Respuesta:", result["response"]["choices"][0]["message"]["content"])
            print(f"Contexto usado: {result['context_used']['chunks_found']} chunks")
            for source in result["context_used"]["sources"]:
                print(f"  - {source['source']} (score: {source['score']})")
        else:
            print("Error:", result["error"])
            
    except Exception as e:
        print(f"Error en ejemplo: {e}")
        
    # Usando la función de utilidad
    try:
        result = chat_with_portfolio_context("Háblame sobre tus proyectos con embeddings")
        print("\n--- Usando función de utilidad ---")
        if result["success"]:
            print("Respuesta:", result["response"]["choices"][0]["message"]["content"])
        else:
            print("Error:", result["error"])
    except Exception as e:
        print(f"Error en función de utilidad: {e}")



