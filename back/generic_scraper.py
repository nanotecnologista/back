"""
Scraper genérico para outras plataformas (Himalayas, Remotar, QueroHome, etc.).
"""
import re
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from datetime import datetime

from .base_scraper import BaseScraper


class GenericScraper(BaseScraper):
    """Scraper genérico que pode ser adaptado para diferentes plataformas."""
    
    def __init__(self, platform_name: str, base_url: str, config: Dict):
        super().__init__(platform_name)
        self.base_url = base_url
        self.config = config
        self.is_logged_in = False
        
    def login(self, email: str, password: str) -> bool:
        """Login genérico baseado na configuração."""
        try:
            if not self.config.get("login_required", False):
                self.is_logged_in = True
                return True
            
            login_config = self.config.get("login", {})
            login_url = urljoin(self.base_url, login_config.get("url", "/login"))
            
            self.logger.info(f"Iniciando login em {self.platform_name}")
            
            # Obter página de login
            response = self.make_request(login_url)
            if not response:
                return False
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Encontrar formulário de login
            form = soup.find('form', {'id': login_config.get("form_id")}) or \
                   soup.find('form', class_=login_config.get("form_class")) or \
                   soup.find('form')
            
            if not form:
                self.logger.error("Formulário de login não encontrado")
                return False
            
            # Preparar dados do formulário
            form_data = {}
            
            # Campos obrigatórios
            email_field = login_config.get("email_field", "email")
            password_field = login_config.get("password_field", "password")
            
            form_data[email_field] = email
            form_data[password_field] = password
            
            # Campos ocultos (CSRF, etc.)
            hidden_inputs = form.find_all('input', type='hidden')
            for hidden in hidden_inputs:
                name = hidden.get('name')
                value = hidden.get('value')
                if name and value:
                    form_data[name] = value
            
            # Fazer login
            form_action = form.get('action') or login_url
            if not form_action.startswith('http'):
                form_action = urljoin(self.base_url, form_action)
            
            login_response = self.make_request(
                form_action,
                method="POST",
                data=form_data,
                allow_redirects=True
            )
            
            # Verificar sucesso do login
            success_indicators = login_config.get("success_indicators", [])
            if login_response:
                for indicator in success_indicators:
                    if indicator in login_response.url or indicator in login_response.text:
                        self.is_logged_in = True
                        self.logger.info(f"Login em {self.platform_name} realizado com sucesso")
                        return True
            
            self.logger.error(f"Falha no login em {self.platform_name}")
            return False
            
        except Exception as e:
            self.logger.error(f"Erro durante login em {self.platform_name}: {e}")
            return False
    
    def search_jobs(self, keywords: List[str], **kwargs) -> List[Dict]:
        """Busca vagas usando configuração genérica."""
        jobs = []
        
        try:
            search_config = self.config.get("search", {})
            
            for keyword in keywords:
                keyword_jobs = self._search_by_keyword(keyword, search_config, **kwargs)
                jobs.extend(keyword_jobs)
            
            # Remover duplicatas
            unique_jobs = {}
            for job in jobs:
                job_key = job.get("link") or job.get("title", "") + job.get("company", "")
                if job_key and job_key not in unique_jobs:
                    unique_jobs[job_key] = job
            
            jobs = list(unique_jobs.values())
            self.logger.info(f"Total de {len(jobs)} vagas únicas encontradas em {self.platform_name}")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Erro na busca de vagas em {self.platform_name}: {e}")
            return []
    
    def _search_by_keyword(self, keyword: str, search_config: Dict, **kwargs) -> List[Dict]:
        """Busca vagas por palavra-chave específica."""
        jobs = []
        
        try:
            # Construir URL de busca
            search_url = self._build_search_url(keyword, search_config)
            
            # Buscar múltiplas páginas se configurado
            max_pages = search_config.get("max_pages", 3)
            
            for page in range(1, max_pages + 1):
                page_url = self._build_page_url(search_url, page, search_config)
                page_jobs = self._scrape_jobs_page(page_url, search_config)
                
                if not page_jobs:
                    break  # Não há mais vagas
                
                jobs.extend(page_jobs)
                self.random_delay(2, 5)  # Delay entre páginas
            
            self.logger.info(f"Encontradas {len(jobs)} vagas para '{keyword}' em {self.platform_name}")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Erro na busca por '{keyword}' em {self.platform_name}: {e}")
            return []
    
    def _build_search_url(self, keyword: str, search_config: Dict) -> str:
        """Constrói URL de busca baseada na configuração."""
        base_search_url = urljoin(self.base_url, search_config.get("url", "/jobs"))
        
        # Parâmetros de busca
        params = search_config.get("params", {})
        query_param = search_config.get("query_param", "q")
        
        # Substituir placeholders
        url_params = []
        for key, value in params.items():
            if isinstance(value, str) and "{keyword}" in value:
                value = value.replace("{keyword}", keyword)
            url_params.append(f"{key}={value}")
        
        # Adicionar palavra-chave
        url_params.append(f"{query_param}={keyword}")
        
        return f"{base_search_url}?{'&'.join(url_params)}"
    
    def _build_page_url(self, base_url: str, page: int, search_config: Dict) -> str:
        """Constrói URL para página específica."""
        page_param = search_config.get("page_param", "page")
        
        if "?" in base_url:
            return f"{base_url}&{page_param}={page}"
        else:
            return f"{base_url}?{page_param}={page}"
    
    def _scrape_jobs_page(self, url: str, search_config: Dict) -> List[Dict]:
        """Extrai vagas de uma página de resultados."""
        jobs = []
        
        try:
            response = self.make_request(url)
            if not response:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Encontrar containers de vagas
            selectors = search_config.get("job_selectors", [])
            job_cards = []
            
            for selector in selectors:
                if selector.get("type") == "class":
                    cards = soup.find_all(selector.get("tag", "div"), class_=selector.get("value"))
                elif selector.get("type") == "id":
                    cards = soup.find_all(selector.get("tag", "div"), id=selector.get("value"))
                else:
                    cards = soup.find_all(selector.get("tag", "div"))
                
                if cards:
                    job_cards = cards
                    break
            
            # Extrair informações de cada vaga
            for card in job_cards:
                try:
                    job = self._extract_job_from_card(card, search_config)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    self.logger.warning(f"Erro ao extrair vaga: {e}")
                    continue
            
            return jobs
            
        except Exception as e:
            self.logger.error(f"Erro ao processar página {url}: {e}")
            return []
    
    def _extract_job_from_card(self, card, search_config: Dict) -> Optional[Dict]:
        """Extrai informações de uma vaga usando configuração."""
        try:
            extraction_config = search_config.get("extraction", {})
            
            # Título
            title = self._extract_field(card, extraction_config.get("title", {}))
            
            # Empresa
            company = self._extract_field(card, extraction_config.get("company", {}))
            
            # Link
            link = self._extract_field(card, extraction_config.get("link", {}))
            if link and not link.startswith('http'):
                link = urljoin(self.base_url, link)
            
            # Localização
            location = self._extract_field(card, extraction_config.get("location", {})) or "Remoto"
            
            # Descrição
            description = self._extract_field(card, extraction_config.get("description", {})) or ""
            
            # Data
            date_text = self._extract_field(card, extraction_config.get("date", {}))
            published_date = self._parse_date(date_text) if date_text else None
            
            # Salário
            salary = self._extract_field(card, extraction_config.get("salary", {}))
            
            if not title:
                return None
            
            return {
                "title": title,
                "company": company or "N/A",
                "location": location,
                "link": link,
                "salary": salary,
                "published_date": published_date,
                "platform": self.platform_name,
                "type": "listing",
                "description": description,
                "scraped_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.warning(f"Erro ao extrair vaga: {e}")
            return None
    
    def _extract_field(self, card, field_config: Dict) -> Optional[str]:
        """Extrai um campo específico usando configuração."""
        try:
            if not field_config:
                return None
            
            selector_type = field_config.get("type", "class")
            tag = field_config.get("tag", "div")
            value = field_config.get("value", "")
            attribute = field_config.get("attribute")
            
            # Encontrar elemento
            element = None
            if selector_type == "class":
                element = card.find(tag, class_=value)
            elif selector_type == "id":
                element = card.find(tag, id=value)
            elif selector_type == "xpath":
                # BeautifulSoup não suporta XPath, usar CSS selector
                element = card.select_one(value)
            
            if not element:
                return None
            
            # Extrair valor
            if attribute:
                return element.get(attribute)
            else:
                return element.get_text(strip=True)
                
        except Exception as e:
            self.logger.warning(f"Erro ao extrair campo: {e}")
            return None
    
    def _parse_date(self, date_text: str) -> Optional[str]:
        """Converte texto de data para formato ISO."""
        try:
            if not date_text:
                return None
            
            date_text = date_text.lower().strip()
            
            # Padrões comuns em português e inglês
            if any(word in date_text for word in ["hoje", "today", "agora", "now"]):
                return datetime.now().isoformat()
            elif any(word in date_text for word in ["ontem", "yesterday"]):
                return (datetime.now() - timedelta(days=1)).isoformat()
            elif "dias" in date_text or "days" in date_text:
                match = re.search(r'(\d+)\s*(dias?|days?)', date_text)
                if match:
                    days = int(match.group(1))
                    return (datetime.now() - timedelta(days=days)).isoformat()
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Erro ao processar data '{date_text}': {e}")
            return None
    
    def get_job_details(self, job_url: str) -> Optional[Dict]:
        """Obtém detalhes completos de uma vaga."""
        try:
            if not job_url:
                return None
            
            response = self.make_request(job_url)
            if not response:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Configuração para extração de detalhes
            details_config = self.config.get("details", {})
            
            details = {}
            
            # Extrair campos configurados
            for field_name, field_config in details_config.items():
                field_value = self._extract_field(soup, field_config)
                if field_value:
                    details[field_name] = field_value
            
            details["scraped_details_at"] = datetime.now().isoformat()
            
            return details
            
        except Exception as e:
            self.logger.error(f"Erro ao obter detalhes da vaga {job_url}: {e}")
            return None


# Configurações específicas para plataformas conhecidas
PLATFORM_CONFIGS = {
    "himalayas": {
        "base_url": "https://himalayas.app",
        "login_required": False,
        "search": {
            "url": "/jobs",
            "params": {
                "remote": "true",
                "date": "week"
            },
            "query_param": "q",
            "page_param": "page",
            "max_pages": 3,
            "job_selectors": [
                {"type": "class", "tag": "div", "value": "job-card"}
            ],
            "extraction": {
                "title": {"type": "class", "tag": "h3", "value": "job-title"},
                "company": {"type": "class", "tag": "span", "value": "company-name"},
                "link": {"type": "class", "tag": "a", "value": "job-link", "attribute": "href"},
                "location": {"type": "class", "tag": "span", "value": "location"},
                "description": {"type": "class", "tag": "p", "value": "job-description"}
            }
        }
    },
    
    "remotar": {
        "base_url": "https://remotar.com.br",
        "login_required": False,
        "search": {
            "url": "/vagas",
            "params": {
                "tipo": "remoto"
            },
            "query_param": "busca",
            "page_param": "pagina",
            "max_pages": 3,
            "job_selectors": [
                {"type": "class", "tag": "div", "value": "vaga-item"}
            ],
            "extraction": {
                "title": {"type": "class", "tag": "h2", "value": "vaga-titulo"},
                "company": {"type": "class", "tag": "span", "value": "empresa"},
                "link": {"type": "class", "tag": "a", "value": "vaga-link", "attribute": "href"},
                "location": {"type": "class", "tag": "span", "value": "localizacao"}
            }
        }
    },
    
    "querohome": {
        "base_url": "https://querohome.com.br",
        "login_required": False,
        "search": {
            "url": "/vagas",
            "params": {
                "modalidade": "home-office"
            },
            "query_param": "q",
            "page_param": "page",
            "max_pages": 3,
            "job_selectors": [
                {"type": "class", "tag": "article", "value": "job-card"}
            ],
            "extraction": {
                "title": {"type": "class", "tag": "h3", "value": "job-title"},
                "company": {"type": "class", "tag": "span", "value": "company"},
                "link": {"type": "class", "tag": "a", "value": "job-link", "attribute": "href"},
                "location": {"type": "class", "tag": "span", "value": "location"}
            }
        }
    }
}

