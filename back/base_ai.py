"""
Classe base para módulos de IA e processamento de linguagem natural.
"""
import logging
import openai
from typing import List, Dict, Optional, Any, Union
from abc import ABC, abstractmethod
import time
import random

from transformers import pipeline, AutoTokenizer, AutoModel
from langdetect import detect, DetectorFactory
import torch

from backend.config.settings import settings
from backend.config.logging_config import get_logger


# Configurar seed para detecção de idioma consistente
DetectorFactory.seed = 0


class BaseAI(ABC):
    """Classe base para módulos de IA."""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.logger = get_logger(f"ai.{module_name}")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Configurar OpenAI
        self._setup_openai()
        
        # Cache para modelos carregados
        self._model_cache = {}
        
    def _setup_openai(self):
        """Configura cliente OpenAI."""
        try:
            if settings.OPENAI_API_KEY:
                openai.api_key = settings.OPENAI_API_KEY
                openai.api_base = settings.OPENAI_API_BASE
                self.logger.info("OpenAI configurado com sucesso")
            else:
                self.logger.warning("Chave da API OpenAI não configurada")
        except Exception as e:
            self.logger.error(f"Erro ao configurar OpenAI: {e}")
    
    def detect_language(self, text: str) -> str:
        """Detecta o idioma do texto."""
        try:
            if not text or len(text.strip()) < 10:
                return "pt"  # Padrão português
            
            # Limpar texto
            clean_text = text.strip()[:1000]  # Primeiros 1000 caracteres
            
            detected = detect(clean_text)
            
            # Mapear códigos de idioma
            language_map = {
                "pt": "pt",
                "en": "en",
                "es": "pt",  # Espanhol -> Português (similar)
                "fr": "en",  # Francês -> Inglês
            }
            
            return language_map.get(detected, "pt")
            
        except Exception as e:
            self.logger.warning(f"Erro na detecção de idioma: {e}")
            return "pt"  # Padrão português
    
    def load_huggingface_model(self, model_name: str, task: str = None) -> Any:
        """Carrega modelo do Hugging Face com cache."""
        try:
            cache_key = f"{model_name}_{task}"
            
            if cache_key in self._model_cache:
                return self._model_cache[cache_key]
            
            self.logger.info(f"Carregando modelo {model_name}")
            
            if task:
                model = pipeline(task, model=model_name, device=0 if self.device == "cuda" else -1)
            else:
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModel.from_pretrained(model_name)
                model = {"tokenizer": tokenizer, "model": model}
            
            self._model_cache[cache_key] = model
            self.logger.info(f"Modelo {model_name} carregado com sucesso")
            
            return model
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar modelo {model_name}: {e}")
            return None
    
    def call_openai_api(self, prompt: str, model: str = "gpt-3.5-turbo", max_tokens: int = 1000, 
                       temperature: float = 0.7, **kwargs) -> Optional[str]:
        """Chama API OpenAI com tratamento de erros e retry."""
        try:
            if not settings.OPENAI_API_KEY:
                self.logger.warning("API OpenAI não configurada")
                return None
            
            # Retry com backoff exponencial
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = openai.ChatCompletion.create(
                        model=model,
                        messages=[
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=max_tokens,
                        temperature=temperature,
                        **kwargs
                    )
                    
                    return response.choices[0].message.content.strip()
                    
                except openai.error.RateLimitError:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) + random.uniform(0, 1)
                        self.logger.warning(f"Rate limit atingido, aguardando {wait_time:.2f}s")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise
                        
                except openai.error.APIError as e:
                    self.logger.error(f"Erro na API OpenAI: {e}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Erro ao chamar OpenAI: {e}")
            return None
    
    def call_huggingface_generation(self, model_name: str, prompt: str, 
                                  max_length: int = 500, **kwargs) -> Optional[str]:
        """Chama modelo de geração do Hugging Face."""
        try:
            generator = self.load_huggingface_model(model_name, "text-generation")
            if not generator:
                return None
            
            # Configurações padrão
            generation_kwargs = {
                "max_length": max_length,
                "num_return_sequences": 1,
                "temperature": 0.7,
                "do_sample": True,
                "pad_token_id": generator.tokenizer.eos_token_id,
                **kwargs
            }
            
            # Gerar texto
            results = generator(prompt, **generation_kwargs)
            
            if results and len(results) > 0:
                generated_text = results[0]["generated_text"]
                # Remover prompt original
                if generated_text.startswith(prompt):
                    generated_text = generated_text[len(prompt):].strip()
                return generated_text
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erro na geração com Hugging Face: {e}")
            return None
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extrai palavras-chave importantes do texto."""
        try:
            # Usar modelo de NER ou TF-IDF simples
            words = text.lower().split()
            
            # Filtrar palavras comuns
            stop_words = {
                "pt": ["o", "a", "os", "as", "um", "uma", "de", "da", "do", "para", "com", "em", "na", "no", "que", "e", "ou"],
                "en": ["the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"]
            }
            
            language = self.detect_language(text)
            stop_list = stop_words.get(language, stop_words["pt"])
            
            # Filtrar e contar palavras
            word_count = {}
            for word in words:
                clean_word = word.strip(".,!?;:")
                if len(clean_word) > 3 and clean_word not in stop_list:
                    word_count[clean_word] = word_count.get(clean_word, 0) + 1
            
            # Ordenar por frequência
            sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
            
            return [word for word, count in sorted_words[:max_keywords]]
            
        except Exception as e:
            self.logger.warning(f"Erro na extração de palavras-chave: {e}")
            return []
    
    def translate_text(self, text: str, target_language: str) -> str:
        """Traduz texto para o idioma alvo."""
        try:
            if not text:
                return text
            
            source_lang = self.detect_language(text)
            if source_lang == target_language:
                return text
            
            # Tentar OpenAI primeiro
            if settings.OPENAI_API_KEY:
                prompt = f"Translate the following text to {target_language}:\n\n{text}"
                translation = self.call_openai_api(prompt, max_tokens=len(text) * 2)
                if translation:
                    return translation
            
            # Fallback para Hugging Face
            model_name = f"Helsinki-NLP/opus-mt-{source_lang}-{target_language}"
            try:
                translator = self.load_huggingface_model(model_name, "translation")
                if translator:
                    result = translator(text)
                    if result and len(result) > 0:
                        return result[0]["translation_text"]
            except:
                pass
            
            # Se não conseguir traduzir, retornar original
            self.logger.warning(f"Não foi possível traduzir de {source_lang} para {target_language}")
            return text
            
        except Exception as e:
            self.logger.error(f"Erro na tradução: {e}")
            return text
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analisa sentimento do texto."""
        try:
            sentiment_analyzer = self.load_huggingface_model(
                "cardiffnlp/twitter-roberta-base-sentiment-latest", 
                "sentiment-analysis"
            )
            
            if not sentiment_analyzer:
                return {"positive": 0.5, "negative": 0.5, "neutral": 0.0}
            
            result = sentiment_analyzer(text[:512])  # Limitar tamanho
            
            if result and len(result) > 0:
                label = result[0]["label"].lower()
                score = result[0]["score"]
                
                sentiment_map = {
                    "positive": {"positive": score, "negative": 1-score, "neutral": 0.0},
                    "negative": {"positive": 1-score, "negative": score, "neutral": 0.0},
                    "neutral": {"positive": 0.0, "negative": 0.0, "neutral": score}
                }
                
                return sentiment_map.get(label, {"positive": 0.5, "negative": 0.5, "neutral": 0.0})
            
            return {"positive": 0.5, "negative": 0.5, "neutral": 0.0}
            
        except Exception as e:
            self.logger.warning(f"Erro na análise de sentimento: {e}")
            return {"positive": 0.5, "negative": 0.5, "neutral": 0.0}
    
    def clean_text(self, text: str) -> str:
        """Limpa e normaliza texto."""
        try:
            if not text:
                return ""
            
            # Remover caracteres especiais excessivos
            import re
            
            # Normalizar espaços
            text = re.sub(r'\s+', ' ', text)
            
            # Remover caracteres de controle
            text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
            
            # Limitar tamanho de linhas muito longas
            lines = text.split('\n')
            cleaned_lines = []
            for line in lines:
                if len(line) > 1000:
                    # Quebrar linha longa em sentenças
                    sentences = re.split(r'[.!?]+', line)
                    cleaned_lines.extend([s.strip() for s in sentences if s.strip()])
                else:
                    cleaned_lines.append(line)
            
            return '\n'.join(cleaned_lines).strip()
            
        except Exception as e:
            self.logger.warning(f"Erro na limpeza de texto: {e}")
            return text
    
    @abstractmethod
    def process(self, input_data: Any) -> Any:
        """Método abstrato para processamento principal."""
        pass
    
    def __del__(self):
        """Limpa recursos ao destruir objeto."""
        try:
            # Limpar cache de modelos
            for model in self._model_cache.values():
                if hasattr(model, 'model') and hasattr(model['model'], 'cpu'):
                    model['model'].cpu()
                del model
            self._model_cache.clear()
        except:
            pass

