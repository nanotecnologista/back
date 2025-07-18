"""
Classe base para todos os scrapers de vagas de emprego.
"""
import time
import random
import logging
import urllib.robotparser
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin, urlparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from backend.config.settings import settings
from backend.config.logging_config import get_logger


class BaseScraper(ABC):
    """Classe base abstrata para todos os scrapers."""
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.logger = get_logger(f"scraping.{platform_name}")
        self.session = self._create_session()
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0"
        ]
        
    def _create_session(self) -> requests.Session:
        """Cria uma sessão HTTP configurada com retry e timeout."""
        session = requests.Session()
        
        # Configurar retry strategy
        retry_strategy = Retry(
            total=settings.MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Configurar headers padrão
        session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        return session
    
    def check_robots_txt(self, base_url: str, path: str = "/") -> bool:
        """Verifica se é permitido acessar o path segundo robots.txt."""
        try:
            robots_url = urljoin(base_url, "/robots.txt")
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            user_agent = self.session.headers.get('User-Agent', '*')
            can_fetch = rp.can_fetch(user_agent, path)
            
            if not can_fetch:
                self.logger.warning(f"Acesso negado pelo robots.txt para {path}")
            
            return can_fetch
            
        except Exception as e:
            self.logger.warning(f"Erro ao verificar robots.txt: {e}")
            return True  # Se não conseguir verificar, permite o acesso
    
    def random_delay(self, min_delay: Optional[int] = None, max_delay: Optional[int] = None):
        """Aplica delay aleatório para evitar detecção."""
        min_delay = min_delay or settings.SCRAPING_DELAY_MIN
        max_delay = max_delay or settings.SCRAPING_DELAY_MAX
        
        delay = random.uniform(min_delay, max_delay)
        self.logger.debug(f"Aplicando delay de {delay:.2f} segundos")
        time.sleep(delay)
    
    def rotate_user_agent(self):
        """Rotaciona o User-Agent para evitar detecção."""
        new_user_agent = random.choice(self.user_agents)
        self.session.headers.update({'User-Agent': new_user_agent})
        self.logger.debug(f"User-Agent alterado para: {new_user_agent[:50]}...")
    
    def make_request(self, url: str, method: str = "GET", **kwargs) -> Optional[requests.Response]:
        """Faz uma requisição HTTP com tratamento de erros e anti-bloqueio."""
        try:
            # Verificar robots.txt
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            if not self.check_robots_txt(base_url, parsed_url.path):
                return None
            
            # Rotacionar User-Agent ocasionalmente
            if random.random() < 0.3:  # 30% de chance
                self.rotate_user_agent()
            
            # Aplicar delay
            self.random_delay()
            
            # Fazer requisição
            response = self.session.request(method, url, timeout=30, **kwargs)
            response.raise_for_status()
            
            self.logger.debug(f"Requisição bem-sucedida para {url}")
            return response
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro na requisição para {url}: {e}")
            return None
    
    def filter_jobs_by_keywords(self, jobs: List[Dict], job_type: str) -> List[Dict]:
        """Filtra vagas por palavras-chave do tipo de trabalho."""
        if job_type not in settings.JOB_TYPES:
            self.logger.warning(f"Tipo de trabalho desconhecido: {job_type}")
            return jobs
        
        keywords = settings.JOB_TYPES[job_type]["keywords"]
        filtered_jobs = []
        
        for job in jobs:
            title = job.get("title", "").lower()
            description = job.get("description", "").lower()
            
            # Verificar se alguma palavra-chave está presente
            for keyword in keywords:
                if keyword.lower() in title or keyword.lower() in description:
                    filtered_jobs.append(job)
                    break
        
        self.logger.info(f"Filtradas {len(filtered_jobs)} vagas de {len(jobs)} para tipo '{job_type}'")
        return filtered_jobs
    
    def filter_remote_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Filtra apenas vagas 100% remotas/home office."""
        remote_keywords = [
            "remoto", "remote", "home office", "homeoffice", "trabalho remoto",
            "100% remoto", "totalmente remoto", "anywhere", "work from home"
        ]
        
        filtered_jobs = []
        
        for job in jobs:
            title = job.get("title", "").lower()
            description = job.get("description", "").lower()
            location = job.get("location", "").lower()
            
            # Verificar se é remoto
            is_remote = any(
                keyword in title or keyword in description or keyword in location
                for keyword in remote_keywords
            )
            
            if is_remote:
                filtered_jobs.append(job)
        
        self.logger.info(f"Filtradas {len(filtered_jobs)} vagas remotas de {len(jobs)}")
        return filtered_jobs
    
    def filter_blacklisted_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Remove vagas de empresas ou com palavras-chave da lista negra."""
        filtered_jobs = []
        
        for job in jobs:
            title = job.get("title", "").lower()
            description = job.get("description", "").lower()
            company = job.get("company", "").lower()
            
            # Verificar empresas da lista negra
            is_blacklisted_company = any(
                blacklisted.lower() in company
                for blacklisted in settings.BLACKLIST_COMPANIES
            )
            
            # Verificar palavras-chave da lista negra
            is_blacklisted_keyword = any(
                keyword.lower() in title or keyword.lower() in description
                for keyword in settings.BLACKLIST_KEYWORDS
            )
            
            if not (is_blacklisted_company or is_blacklisted_keyword):
                filtered_jobs.append(job)
            else:
                self.logger.debug(f"Vaga filtrada pela lista negra: {job.get('title', 'N/A')}")
        
        self.logger.info(f"Removidas {len(jobs) - len(filtered_jobs)} vagas da lista negra")
        return filtered_jobs
    
    def apply_all_filters(self, jobs: List[Dict], job_type: str) -> List[Dict]:
        """Aplica todos os filtros nas vagas."""
        self.logger.info(f"Aplicando filtros em {len(jobs)} vagas para tipo '{job_type}'")
        
        # Filtrar por tipo de trabalho
        jobs = self.filter_jobs_by_keywords(jobs, job_type)
        
        # Filtrar apenas remotas
        jobs = self.filter_remote_jobs(jobs)
        
        # Remover lista negra
        jobs = self.filter_blacklisted_jobs(jobs)
        
        self.logger.info(f"Resultado final: {len(jobs)} vagas após todos os filtros")
        return jobs
    
    @abstractmethod
    def login(self, email: str, password: str) -> bool:
        """Faz login na plataforma."""
        pass
    
    @abstractmethod
    def search_jobs(self, keywords: List[str], **kwargs) -> List[Dict]:
        """Busca vagas na plataforma."""
        pass
    
    @abstractmethod
    def get_job_details(self, job_url: str) -> Optional[Dict]:
        """Obtém detalhes completos de uma vaga."""
        pass
    
    def close(self):
        """Fecha a sessão e limpa recursos."""
        if hasattr(self, 'session'):
            self.session.close()
        self.logger.info(f"Scraper {self.platform_name} finalizado")

