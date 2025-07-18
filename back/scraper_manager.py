"""
Gerenciador central para todos os scrapers de vagas.
"""
import asyncio
import logging
from typing import List, Dict, Optional, Type
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from .base_scraper import BaseScraper
from .linkedin_scraper import LinkedInScraper
from .gupy_scraper import GupyScraper
from .catho_scraper import CathoScraper
from .generic_scraper import GenericScraper, PLATFORM_CONFIGS
from backend.config.settings import settings
from backend.config.logging_config import get_logger


class ScraperManager:
    """Gerenciador central para coordenar todos os scrapers."""
    
    def __init__(self):
        self.logger = get_logger("scraping.manager")
        self.scrapers: Dict[str, BaseScraper] = {}
        self.credentials = self._load_credentials()
        
    def _load_credentials(self) -> Dict[str, Dict[str, str]]:
        """Carrega credenciais das plataformas."""
        return {
            "linkedin": {
                "email": settings.LINKEDIN_EMAIL,
                "password": settings.LINKEDIN_PASSWORD
            },
            "gupy": {
                "email": settings.GUPY_EMAIL,
                "password": settings.GUPY_PASSWORD
            },
            "catho": {
                "email": settings.CATHO_EMAIL,
                "password": settings.CATHO_PASSWORD
            },
            "himalayas": {
                "email": settings.HIMALAYAS_EMAIL,
                "password": settings.HIMALAYAS_PASSWORD
            },
            "remotar": {
                "email": settings.REMOTAR_EMAIL,
                "password": settings.REMOTAR_PASSWORD
            },
            "querohome": {
                "email": settings.QUEROHOME_EMAIL,
                "password": settings.QUEROHOME_PASSWORD
            }
        }
    
    def initialize_scrapers(self, platforms: Optional[List[str]] = None) -> bool:
        """Inicializa scrapers para as plataformas especificadas."""
        try:
            platforms = platforms or settings.SUPPORTED_PLATFORMS
            
            for platform in platforms:
                try:
                    scraper = self._create_scraper(platform)
                    if scraper:
                        self.scrapers[platform] = scraper
                        self.logger.info(f"Scraper {platform} inicializado com sucesso")
                    else:
                        self.logger.warning(f"Falha ao inicializar scraper {platform}")
                        
                except Exception as e:
                    self.logger.error(f"Erro ao inicializar scraper {platform}: {e}")
                    continue
            
            self.logger.info(f"Inicializados {len(self.scrapers)} scrapers")
            return len(self.scrapers) > 0
            
        except Exception as e:
            self.logger.error(f"Erro na inicialização dos scrapers: {e}")
            return False
    
    def _create_scraper(self, platform: str) -> Optional[BaseScraper]:
        """Cria scraper específico para a plataforma."""
        try:
            if platform == "linkedin":
                return LinkedInScraper()
            elif platform == "gupy":
                return GupyScraper()
            elif platform == "catho":
                return CathoScraper()
            elif platform in PLATFORM_CONFIGS:
                config = PLATFORM_CONFIGS[platform]
                return GenericScraper(
                    platform_name=platform,
                    base_url=config["base_url"],
                    config=config
                )
            else:
                self.logger.warning(f"Plataforma desconhecida: {platform}")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao criar scraper {platform}: {e}")
            return None
    
    def login_all(self) -> Dict[str, bool]:
        """Faz login em todas as plataformas."""
        login_results = {}
        
        for platform, scraper in self.scrapers.items():
            try:
                credentials = self.credentials.get(platform, {})
                email = credentials.get("email")
                password = credentials.get("password")
                
                if not email or not password:
                    self.logger.warning(f"Credenciais não configuradas para {platform}")
                    login_results[platform] = False
                    continue
                
                success = scraper.login(email, password)
                login_results[platform] = success
                
                if success:
                    self.logger.info(f"Login realizado com sucesso em {platform}")
                else:
                    self.logger.error(f"Falha no login em {platform}")
                    
            except Exception as e:
                self.logger.error(f"Erro no login {platform}: {e}")
                login_results[platform] = False
        
        successful_logins = sum(login_results.values())
        self.logger.info(f"Login realizado em {successful_logins}/{len(self.scrapers)} plataformas")
        
        return login_results
    
    def search_all_platforms(self, job_type: str = "dev", max_workers: int = 3) -> Dict[str, List[Dict]]:
        """Busca vagas em todas as plataformas em paralelo."""
        try:
            keywords = settings.JOB_TYPES.get(job_type, {}).get("keywords", [])
            if not keywords:
                self.logger.error(f"Tipo de trabalho desconhecido: {job_type}")
                return {}
            
            results = {}
            
            # Executar buscas em paralelo
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_platform = {
                    executor.submit(self._search_platform, platform, scraper, keywords, job_type): platform
                    for platform, scraper in self.scrapers.items()
                }
                
                for future in as_completed(future_to_platform):
                    platform = future_to_platform[future]
                    try:
                        jobs = future.result()
                        results[platform] = jobs
                        self.logger.info(f"Busca concluída em {platform}: {len(jobs)} vagas")
                    except Exception as e:
                        self.logger.error(f"Erro na busca em {platform}: {e}")
                        results[platform] = []
            
            total_jobs = sum(len(jobs) for jobs in results.values())
            self.logger.info(f"Busca concluída: {total_jobs} vagas encontradas em {len(results)} plataformas")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Erro na busca em todas as plataformas: {e}")
            return {}
    
    def _search_platform(self, platform: str, scraper: BaseScraper, keywords: List[str], job_type: str) -> List[Dict]:
        """Busca vagas em uma plataforma específica."""
        try:
            self.logger.info(f"Iniciando busca em {platform}")
            
            # Buscar vagas
            jobs = scraper.search_jobs(keywords)
            
            # Aplicar filtros
            filtered_jobs = scraper.apply_all_filters(jobs, job_type)
            
            # Adicionar metadados
            for job in filtered_jobs:
                job["search_type"] = job_type
                job["keywords_used"] = keywords
            
            return filtered_jobs
            
        except Exception as e:
            self.logger.error(f"Erro na busca em {platform}: {e}")
            return []
    
    def get_job_details_batch(self, jobs: List[Dict], max_workers: int = 5) -> List[Dict]:
        """Obtém detalhes de múltiplas vagas em paralelo."""
        try:
            enriched_jobs = []
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_job = {
                    executor.submit(self._get_job_details, job): job
                    for job in jobs if job.get("link")
                }
                
                for future in as_completed(future_to_job):
                    job = future_to_job[future]
                    try:
                        details = future.result()
                        if details:
                            job.update(details)
                        enriched_jobs.append(job)
                    except Exception as e:
                        self.logger.warning(f"Erro ao obter detalhes da vaga {job.get('title', 'N/A')}: {e}")
                        enriched_jobs.append(job)  # Adicionar mesmo sem detalhes
            
            self.logger.info(f"Detalhes obtidos para {len(enriched_jobs)} vagas")
            return enriched_jobs
            
        except Exception as e:
            self.logger.error(f"Erro ao obter detalhes em lote: {e}")
            return jobs  # Retornar vagas originais em caso de erro
    
    def _get_job_details(self, job: Dict) -> Optional[Dict]:
        """Obtém detalhes de uma vaga específica."""
        try:
            platform = job.get("platform")
            job_url = job.get("link")
            
            if not platform or not job_url:
                return None
            
            scraper = self.scrapers.get(platform)
            if not scraper:
                return None
            
            return scraper.get_job_details(job_url)
            
        except Exception as e:
            self.logger.warning(f"Erro ao obter detalhes da vaga: {e}")
            return None
    
    def search_specific_platforms(self, platforms: List[str], job_type: str = "dev") -> Dict[str, List[Dict]]:
        """Busca vagas apenas nas plataformas especificadas."""
        try:
            filtered_scrapers = {
                platform: scraper for platform, scraper in self.scrapers.items()
                if platform in platforms
            }
            
            if not filtered_scrapers:
                self.logger.warning("Nenhuma plataforma válida especificada")
                return {}
            
            # Temporariamente substituir scrapers
            original_scrapers = self.scrapers
            self.scrapers = filtered_scrapers
            
            try:
                results = self.search_all_platforms(job_type)
            finally:
                self.scrapers = original_scrapers
            
            return results
            
        except Exception as e:
            self.logger.error(f"Erro na busca em plataformas específicas: {e}")
            return {}
    
    def get_platform_status(self) -> Dict[str, Dict]:
        """Retorna status de todas as plataformas."""
        status = {}
        
        for platform, scraper in self.scrapers.items():
            try:
                credentials = self.credentials.get(platform, {})
                has_credentials = bool(credentials.get("email") and credentials.get("password"))
                
                status[platform] = {
                    "initialized": True,
                    "has_credentials": has_credentials,
                    "logged_in": getattr(scraper, "is_logged_in", False),
                    "scraper_type": type(scraper).__name__
                }
            except Exception as e:
                status[platform] = {
                    "initialized": False,
                    "error": str(e)
                }
        
        return status
    
    def close_all(self):
        """Fecha todos os scrapers e limpa recursos."""
        try:
            for platform, scraper in self.scrapers.items():
                try:
                    scraper.close()
                    self.logger.info(f"Scraper {platform} fechado")
                except Exception as e:
                    self.logger.warning(f"Erro ao fechar scraper {platform}: {e}")
            
            self.scrapers.clear()
            self.logger.info("Todos os scrapers foram fechados")
            
        except Exception as e:
            self.logger.error(f"Erro ao fechar scrapers: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_all()

