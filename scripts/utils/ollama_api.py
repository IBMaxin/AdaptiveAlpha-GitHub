"""
Enhanced Ollama API Integration with Multi-Model Support.

Supports:
- CodeLlama (120B, 20B variants)
- GPT4All models
- Optimized settings and context handling
"""

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
import requests
from llm_logger import LLMLogger

@dataclass
class ModelConfig:
    """Model configuration settings."""
    name: str
    context_window: int
    mmap: bool = True
    num_gpu: int = 1
    num_thread: int = 8
    top_k: int = 40
    top_p: float = 0.9
    temperature: float = 0.7
    repeat_penalty: float = 1.1

class OllamaAPI:
    """Enhanced Ollama API client with multi-model support."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        logger: Optional[LLMLogger] = None
    ):
        """Initialize Ollama API client.
        
        Args:
            base_url: Ollama API endpoint
            logger: Optional logger instance
        """
        self.base_url = base_url.rstrip("/")
        self.logger = logger or LLMLogger(log_dir="logs/ollama")
        
        # Default model configurations
        self.models = {
            "codellama-120b": ModelConfig(
                name="codellama:120b",
                context_window=8192,
                num_gpu=2,  # Requires multiple GPUs
                num_thread=16,
                top_k=50,
                temperature=0.7
            ),
            "codellama-20b": ModelConfig(
                name="codellama:20b",
                context_window=4096,
                num_gpu=1,
                num_thread=8,
                top_k=40,
                temperature=0.8
            ),
            "gpt4all-turbo": ModelConfig(
                name="gpt4all:latest",
                context_window=2048,
                num_gpu=1,
                num_thread=4,
                top_k=30,
                temperature=0.9
            ),
            "fallback": ModelConfig(
                name="tinyllama",
                context_window=1024,
                mmap=True,
                num_gpu=0,  # CPU only
                num_thread=4,
                temperature=0.8
            )
        }
        
    async def list_models(self) -> List[str]:
        """Get list of available models."""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            return [model["name"] for model in response.json()["models"]]
        except Exception as e:
            self.logger.log_system(
                "list_models_failed",
                level="error",
                error=str(e)
            )
            return []
            
    async def load_model(
        self,
        model_name: str,
        config: Optional[ModelConfig] = None
    ) -> bool:
        """Load model with optional configuration.
        
        Args:
            model_name: Name of model to load
            config: Optional custom configuration
        """
        try:
            model_config = config or self.models.get(
                model_name,
                self.models["fallback"]
            )
            
            response = requests.post(
                f"{self.base_url}/api/load",
                json={
                    "name": model_config.name,
                    "config": {
                        "mmap": model_config.mmap,
                        "num_gpu": model_config.num_gpu,
                        "num_thread": model_config.num_thread,
                        "context_window": model_config.context_window,
                        "top_k": model_config.top_k,
                        "top_p": model_config.top_p,
                        "temperature": model_config.temperature,
                        "repeat_penalty": model_config.repeat_penalty
                    }
                }
            )
            response.raise_for_status()
            
            self.logger.log_system(
                "model_loaded",
                level="info",
                model=model_name
            )
            return True
            
        except Exception as e:
            self.logger.log_system(
                "model_load_failed",
                level="error",
                model=model_name,
                error=str(e)
            )
            return False
            
    async def generate(
        self,
        prompt: str,
        model_name: str = "codellama-20b",
        **kwargs: Any
    ) -> Optional[str]:
        """Generate text using specified model.
        
        Args:
            prompt: Input prompt
            model_name: Model to use
            **kwargs: Additional generation parameters
        """
        try:
            model_config = self.models.get(model_name, self.models["fallback"])
            
            # Merge default and custom parameters
            params = {
                "model": model_config.name,
                "prompt": prompt,
                "stream": False,
                "top_k": model_config.top_k,
                "top_p": model_config.top_p,
                "temperature": model_config.temperature,
                "repeat_penalty": model_config.repeat_penalty,
                **kwargs
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=params,
                timeout=60
            )
            response.raise_for_status()
            
            generation_time = time.time() - start_time
            response_json = response.json()
            
            self.logger.log_system(
                "generation_complete",
                level="info",
                model=model_name,
                tokens=response_json.get("tokens", 0),
                time=generation_time
            )
            
            return response_json.get("response")
            
        except Exception as e:
            self.logger.log_system(
                "generation_failed",
                level="error",
                model=model_name,
                error=str(e)
            )
            return None
            
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model_name: str = "codellama-20b",
        **kwargs: Any
    ) -> Optional[Dict[str, Any]]:
        """Chat completion using specified model.
        
        Args:
            messages: Chat messages
            model_name: Model to use
            **kwargs: Additional parameters
        """
        try:
            model_config = self.models.get(model_name, self.models["fallback"])
            
            params = {
                "model": model_config.name,
                "messages": messages,
                "stream": False,
                "top_k": model_config.top_k,
                "top_p": model_config.top_p,
                "temperature": model_config.temperature,
                **kwargs
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=params,
                timeout=60
            )
            response.raise_for_status()
            
            generation_time = time.time() - start_time
            response_json = response.json()
            
            self.logger.log_system(
                "chat_complete",
                level="info",
                model=model_name,
                time=generation_time
            )
            
            return response_json
            
        except Exception as e:
            self.logger.log_system(
                "chat_failed",
                level="error",
                model=model_name,
                error=str(e)
            )
            return None
            
    async def embeddings(
        self,
        text: Union[str, List[str]],
        model_name: str = "codellama-20b"
    ) -> Optional[List[List[float]]]:
        """Generate embeddings using specified model.
        
        Args:
            text: Input text or list of texts
            model_name: Model to use
        """
        try:
            texts = [text] if isinstance(text, str) else text
            
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.models[model_name].name,
                    "texts": texts
                },
                timeout=30
            )
            response.raise_for_status()
            
            self.logger.log_system(
                "embeddings_complete",
                level="info",
                model=model_name,
                count=len(texts)
            )
            
            return response.json()["embeddings"]
            
        except Exception as e:
            self.logger.log_system(
                "embeddings_failed",
                level="error",
                model=model_name,
                error=str(e)
            )
            return None
            
    def create_completion(
        self,
        prompt: str,
        model_name: str = "codellama-20b",
        **kwargs: Any
    ) -> Optional[str]:
        """Synchronous completion wrapper."""
        import asyncio
        return asyncio.run(self.generate(prompt, model_name, **kwargs))
        
    def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model_name: str = "codellama-20b",
        **kwargs: Any
    ) -> Optional[Dict[str, Any]]:
        """Synchronous chat completion wrapper."""
        import asyncio
        return asyncio.run(self.chat(messages, model_name, **kwargs))
        
    def create_embeddings(
        self,
        text: Union[str, List[str]],
        model_name: str = "codellama-20b"
    ) -> Optional[List[List[float]]]:
        """Synchronous embeddings wrapper."""
        import asyncio
        return asyncio.run(self.embeddings(text, model_name))
        
# Example usage
if __name__ == "__main__":
    # Initialize client
    client = OllamaAPI()
    
    # List models
    print("Available models:", asyncio.run(client.list_models()))
    
    # Basic completion
    response = client.create_completion(
        "Write a Python function to calculate fibonacci numbers.",
        model_name="codellama-20b"
    )
    print("Completion:", response)
    
    # Chat completion
    chat_response = client.create_chat_completion([
        {"role": "system", "content": "You are a Python expert."},
        {"role": "user", "content": "What is a generator?"}
    ])
    print("Chat:", chat_response)
    
    # Embeddings
    embeddings = client.create_embeddings(
        ["Hello world", "Python programming"],
        model_name="codellama-20b"
    )
    print("Embeddings shape:", len(embeddings), "x", len(embeddings[0]))