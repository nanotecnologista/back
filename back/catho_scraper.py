"""
Scraper para Catho usando requests e BeautifulSoup.
"""
import re
from typing import List, Dict, Optional
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup
from datetime import datetime

from .base_scraper import BaseScraper


class CathoScraper(BaseScraper):
    """Scraper para Catho usando requests e BeautifulSoup."""
    
    def __init__(self):
        super().__init__("catho")
        self.base_url = "https://www.catho.com.br"
        self.is_logged_in = False
        
    def login(self, email: str, password: str) -> bool:
        """Faz login no Catho."""
        try:
            self.logger.info("Iniciando login no Catho")
            
            # Página de login
            login_url = f"{self.base_url}/login"
            response = self.make_request(login_url)
            
            if not response:
                return False
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Encontrar token CSRF se existir
            csrf_token = None
            csrf_input = soup.find('input', {'name': '_token'})
            if csrf_input:
                csrf_token = csrf_input.get('value')
            
            # Dados do login
            login_data = {
                'email': email,
                'password': password
            }
            
            if csrf_token:
                login_data['_token'] = csrf_token
            
            # Fazer login
            login_response = self.make_request(
                login_url,
                method="POST",
                data=login_data,
                allow_redirects=True
            )
            
            if login_response and "perfil" in login_response.url:
                self.is_logged_in = True
                self.logger.info("Login no Catho realizado com sucesso")
                return True
            else:
                self.logger.error("Falha no login do Catho")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro durante login no Catho: {e}")
            return False
    
    def search_jobs(self, keywords: List[str], **kwargs) -> List[Dict]:
        """Busca vagas no Catho."""
        jobs = []
        
        try:
            for keyword in keywords:
                keyword_jobs = self._search_by_keyword(keyword, **kwargs)
                jobs.extend(keyword_jobs)
            
            # Remover duplicatas baseado na URL
            unique_jobs = {}
            for job in jobs:
                job_url = job.get("link")
                if job_url and job_url not in unique_jobs:
                    unique_jobs[job_url] = job
            
            jobs = list(unique_jobs.values())
            self.logger.info(f"Total de {len(jobs)} vagas únicas encontradas no Catho")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Erro na busca de vagas no Catho: {e}")
            return []
    
    def _search_by_keyword(self, keyword: str, **kwargs) -> List[Dict]:
        """Busca vagas por palavra-chave específica."""
        jobs = []
        
        try:
            # URL de busca com filtros
            search_params = {
                'q': keyword,
                'trabalho_remoto': 'true',  # Apenas remotas
                'periodo_publicacao': '7',  # Última semana
                'page': 1
            }
            
            # Construir URL de busca
            search_url = f"{self.base_url}/vagas?"
            for key, value in search_params.items():
                search_url += f"{key}={quote(str(value))}&"
            
            # Buscar múltiplas páginas
            for page in range(1, 4):  # Máximo 3 páginas
                page_url = search_url.replace('page=1', f'page={page}')
                page_jobs = self._scrape_jobs_page(page_url)
                
                if not page_jobs:
                    break  # Não há mais vagas
                
                jobs.extend(page_jobs)
                self.random_delay(2, 5)  # Delay entre páginas
            
            self.logger.info(f"Encontradas {len(jobs)} vagas para '{keyword}' no Catho")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Erro na busca por '{keyword}' no Catho: {e}")
            return []
    
    def _scrape_jobs_page(self, url: str) -> List[Dict]:
        """Extrai vagas de uma página de resultados."""
        jobs = []
        
        try:
            response = self.make_request(url)
            if not response:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Encontrar cards de vagas
            job_cards = soup.find_all('article', class_='sc-1hbxyh9-0') or \
                       soup.find_all('div', class_='job-card') or \
                       soup.find_all('div', {'data-testid': 'job-card'})
            
            for card in job_cards:
                try:
                    job = self._extract_job_from_card(card)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    self.logger.warning(f"Erro ao extrair vaga: {e}")
                    continue
            
            return jobs
            
        except Exception as e:
            self.logger.error(f"Erro ao processar página {url}: {e}")
            return []
    
    def _extract_job_from_card(self, card) -> Optional[Dict]:
        """Extrai informações de uma vaga do card."""
        try:
            # Título da vaga
            title_elem = (
                card.find('h2') or 
                card.find('h3') or 
                card.find('a', class_='job-title') or
                card.find('span', class_='job-title')
            )
            title = title_elem.get_text(strip=True) if title_elem else None
            
            # Link da vaga
            link_elem = card.find('a', href=True)
            link = None
            if link_elem:
                href = link_elem.get('href')
                if href:
                    link = urljoin(self.base_url, href)
            
            # Empresa
            company_elem = (
                card.find('span', class_='company-name') or
                card.find('div', class_='company') or
                card.find('p', class_='company')
            )
            company = company_elem.get_text(strip=True) if company_elem else "N/A"
            
            # Localização
            location_elem = (
                card.find('span', class_='location') or
                card.find('div', class_='location') or
                card.find('p', class_='location')
            )
            location = location_elem.get_text(strip=True) if location_elem else "Remoto"
            
            # Salário
            salary_elem = (
                card.find('span', class_='salary') or
                card.find('div', class_='salary')
            )
            salary = salary_elem.get_text(strip=True) if salary_elem else None
            
            # Data de publicação
            date_elem = (
                card.find('time') or
                card.find('span', class_='date') or
                card.find('div', class_='date')
            )
            published_date = None
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                published_date = self._parse_date(date_text)
            
            # Descrição resumida
            desc_elem = (
                card.find('p', class_='description') or
                card.find('div', class_='description')
            )
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            if not title:
                return None
            
            return {
                "title": title,
                "company": company,
                "location": location,
                "link": link,
                "salary": salary,
                "published_date": published_date,
                "platform": "catho",
                "type": "listing",
                "description": description,
                "scraped_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.warning(f"Erro ao extrair vaga do card: {e}")
            return None
    
    def _parse_date(self, date_text: str) -> Optional[str]:
        """Converte texto de data para formato ISO."""
        try:
            date_text = date_text.lower().strip()
            
            # Padrões comuns
            if "hoje" in date_text or "agora" in date_text:
                return datetime.now().isoformat()
            elif "ontem" in date_text:
                return (datetime.now() - timedelta(days=1)).isoformat()
            elif "dias" in date_text:
                # Extrair número de dias
                match = re.search(r'(\d+)\s*dias?', date_text)
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
            
            # Descrição completa
            description_elem = (
                soup.find('div', class_='job-description') or
                soup.find('section', class_='description') or
                soup.find('div', {'data-testid': 'job-description'})
            )
            description = description_elem.get_text(strip=True) if description_elem else ""
            
            # Requisitos
            requirements_elem = (
                soup.find('div', class_='requirements') or
                soup.find('section', class_='requirements')
            )
            requirements = requirements_elem.get_text(strip=True) if requirements_elem else ""
            
            # Benefícios
            benefits_elem = (
                soup.find('div', class_='benefits') or
                soup.find('section', class_='benefits')
            )
            benefits = benefits_elem.get_text(strip=True) if benefits_elem else ""
            
            # Informações da empresa
            company_info = {}
            company_section = soup.find('section', class_='company-info')
            if company_section:
                company_info = {
                    "description": company_section.get_text(strip=True)
                }
            
            # Tipo de contrato
            contract_elem = soup.find('span', class_='contract-type')
            contract_type = contract_elem.get_text(strip=True) if contract_elem else None
            
            return {
                "full_description": description,
                "requirements": requirements,
                "benefits": benefits,
                "company_info": company_info,
                "contract_type": contract_type,
                "scraped_details_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter detalhes da vaga {job_url}: {e}")
            return None
    
    def search_by_company(self, company_name: str) -> List[Dict]:
        """Busca vagas de uma empresa específica."""
        try:
            search_url = f"{self.base_url}/vagas?empresa={quote(company_name)}&trabalho_remoto=true"
            return self._scrape_jobs_page(search_url)
        except Exception as e:
            self.logger.error(f"Erro na busca por empresa '{company_name}': {e}")
            return []

