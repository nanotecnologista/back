"""
Scraper para Gupy - usando API pública quando disponível.
"""
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from urllib.parse import urlencode

from .base_scraper import BaseScraper
from backend.config.settings import settings


class GupyScraper(BaseScraper):
    """Scraper para Gupy usando API pública."""
    
    def __init__(self):
        super().__init__("gupy")
        self.api_base_url = "https://portal.api.gupy.io/api"
        self.is_logged_in = False
        
    def login(self, email: str, password: str) -> bool:
        """
        Gupy não requer login para busca via API pública.
        Este método é mantido para compatibilidade.
        """
        self.logger.info("Gupy não requer login para API pública")
        self.is_logged_in = True
        return True
    
    def search_jobs(self, keywords: List[str], **kwargs) -> List[Dict]:
        """Busca vagas no Gupy via API."""
        jobs = []
        
        try:
            # Buscar para cada palavra-chave
            for keyword in keywords:
                keyword_jobs = self._search_by_keyword(keyword, **kwargs)
                jobs.extend(keyword_jobs)
            
            # Remover duplicatas baseado no ID
            unique_jobs = {}
            for job in jobs:
                job_id = job.get("id")
                if job_id and job_id not in unique_jobs:
                    unique_jobs[job_id] = job
            
            jobs = list(unique_jobs.values())
            self.logger.info(f"Total de {len(jobs)} vagas únicas encontradas no Gupy")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Erro na busca de vagas no Gupy: {e}")
            return []
    
    def _search_by_keyword(self, keyword: str, **kwargs) -> List[Dict]:
        """Busca vagas por palavra-chave específica."""
        jobs = []
        
        try:
            # Parâmetros da API
            params = {
                "name": keyword,
                "workplaceType": "remote",  # Apenas remotas
                "limit": 100,
                "offset": 0
            }
            
            # Filtro de data (última semana)
            week_ago = datetime.now() - timedelta(days=7)
            params["publishedDate"] = week_ago.strftime("%Y-%m-%d")
            
            # Fazer requisição para API
            url = f"{self.api_base_url}/job"
            response = self.make_request(url, params=params)
            
            if not response:
                return []
            
            data = response.json()
            
            # Processar resultados
            if "data" in data:
                for job_data in data["data"]:
                    job = self._parse_job_data(job_data)
                    if job:
                        jobs.append(job)
            
            self.logger.info(f"Encontradas {len(jobs)} vagas para '{keyword}' no Gupy")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Erro na busca por '{keyword}' no Gupy: {e}")
            return []
    
    def _parse_job_data(self, job_data: Dict) -> Optional[Dict]:
        """Converte dados da API do Gupy para formato padrão."""
        try:
            # Extrair informações básicas
            job_id = job_data.get("id")
            title = job_data.get("name", "")
            company_data = job_data.get("company", {})
            company = company_data.get("name", "N/A")
            
            # Localização
            location = "Remoto"  # Já filtrado por remoto
            
            # Link da vaga
            link = f"https://portal.gupy.io/job/{job_id}" if job_id else None
            
            # Data de publicação
            published_date = job_data.get("publishedDate")
            
            # Descrição
            description = job_data.get("description", "")
            
            # Requisitos
            requirements = job_data.get("requirements", "")
            
            # Benefícios
            benefits = job_data.get("benefits", "")
            
            # Tipo de contrato
            contract_type = job_data.get("contractType", "")
            
            # Salário
            salary_info = job_data.get("salary", {})
            salary_min = salary_info.get("min")
            salary_max = salary_info.get("max")
            
            if not title or not company:
                return None
            
            return {
                "id": job_id,
                "title": title,
                "company": company,
                "location": location,
                "link": link,
                "published_date": published_date,
                "platform": "gupy",
                "type": "api",
                "description": description,
                "requirements": requirements,
                "benefits": benefits,
                "contract_type": contract_type,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "scraped_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.warning(f"Erro ao processar vaga do Gupy: {e}")
            return None
    
    def get_job_details(self, job_url: str) -> Optional[Dict]:
        """Obtém detalhes completos de uma vaga."""
        try:
            # Extrair ID da URL
            job_id = self._extract_job_id_from_url(job_url)
            if not job_id:
                return None
            
            # Fazer requisição para API de detalhes
            url = f"{self.api_base_url}/job/{job_id}"
            response = self.make_request(url)
            
            if not response:
                return None
            
            data = response.json()
            
            # Extrair informações detalhadas
            details = {
                "full_description": data.get("description", ""),
                "requirements": data.get("requirements", ""),
                "benefits": data.get("benefits", ""),
                "additional_info": data.get("additionalInformation", ""),
                "company_info": data.get("company", {}),
                "application_deadline": data.get("applicationDeadline"),
                "scraped_details_at": datetime.now().isoformat()
            }
            
            # Informações sobre processo seletivo
            selection_process = data.get("selectionProcess", {})
            if selection_process:
                details["selection_process"] = selection_process
            
            return details
            
        except Exception as e:
            self.logger.error(f"Erro ao obter detalhes da vaga {job_url}: {e}")
            return None
    
    def _extract_job_id_from_url(self, url: str) -> Optional[str]:
        """Extrai ID da vaga da URL."""
        try:
            # URL padrão: https://portal.gupy.io/job/123456
            if "/job/" in url:
                return url.split("/job/")[-1].split("?")[0]
            return None
        except:
            return None
    
    def search_companies(self, company_names: List[str]) -> List[Dict]:
        """Busca vagas de empresas específicas."""
        jobs = []
        
        try:
            for company_name in company_names:
                # Buscar empresa
                company_url = f"{self.api_base_url}/company"
                company_params = {"name": company_name}
                
                company_response = self.make_request(company_url, params=company_params)
                if not company_response:
                    continue
                
                company_data = company_response.json()
                
                # Para cada empresa encontrada, buscar vagas
                if "data" in company_data:
                    for company in company_data["data"]:
                        company_id = company.get("id")
                        if company_id:
                            company_jobs = self._get_company_jobs(company_id)
                            jobs.extend(company_jobs)
            
            self.logger.info(f"Encontradas {len(jobs)} vagas de empresas específicas no Gupy")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Erro na busca por empresas no Gupy: {e}")
            return []
    
    def _get_company_jobs(self, company_id: str) -> List[Dict]:
        """Obtém vagas de uma empresa específica."""
        try:
            params = {
                "companyId": company_id,
                "workplaceType": "remote",
                "limit": 50
            }
            
            url = f"{self.api_base_url}/job"
            response = self.make_request(url, params=params)
            
            if not response:
                return []
            
            data = response.json()
            jobs = []
            
            if "data" in data:
                for job_data in data["data"]:
                    job = self._parse_job_data(job_data)
                    if job:
                        jobs.append(job)
            
            return jobs
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar vagas da empresa {company_id}: {e}")
            return []
    
    def get_job_application_form(self, job_id: str) -> Optional[Dict]:
        """Obtém informações sobre o formulário de candidatura."""
        try:
            url = f"{self.api_base_url}/job/{job_id}/application-form"
            response = self.make_request(url)
            
            if not response:
                return None
            
            form_data = response.json()
            
            # Processar campos do formulário
            fields = []
            if "fields" in form_data:
                for field in form_data["fields"]:
                    field_info = {
                        "id": field.get("id"),
                        "name": field.get("name"),
                        "type": field.get("type"),
                        "required": field.get("required", False),
                        "options": field.get("options", [])
                    }
                    fields.append(field_info)
            
            return {
                "form_id": form_data.get("id"),
                "fields": fields,
                "application_url": f"https://portal.gupy.io/job/{job_id}/apply",
                "scraped_form_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter formulário da vaga {job_id}: {e}")
            return None

