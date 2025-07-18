"""
Scraper para LinkedIn - vagas oficiais e posts com imagens.
"""
import time
import re
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

from .base_scraper import BaseScraper
from backend.config.settings import settings


class LinkedInScraper(BaseScraper):
    """Scraper para LinkedIn usando Selenium."""
    
    def __init__(self):
        super().__init__("linkedin")
        self.driver = None
        self.wait = None
        self.is_logged_in = False
        
    def _setup_driver(self):
        """Configura o driver do Selenium."""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Em produção, usar headless
        if not settings.DEBUG:
            chrome_options.add_argument("--headless")
        
        # User agent
        chrome_options.add_argument(f"--user-agent={self.session.headers['User-Agent']}")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 10)
        
        self.logger.info("Driver do Selenium configurado para LinkedIn")
    
    def login(self, email: str, password: str) -> bool:
        """Faz login no LinkedIn."""
        try:
            if not self.driver:
                self._setup_driver()
            
            self.logger.info("Iniciando login no LinkedIn")
            self.driver.get("https://www.linkedin.com/login")
            
            # Aguardar página carregar
            time.sleep(2)
            
            # Preencher email
            email_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.clear()
            email_field.send_keys(email)
            
            # Preencher senha
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)
            
            # Clicar em entrar
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Aguardar redirecionamento
            time.sleep(5)
            
            # Verificar se login foi bem-sucedido
            if "feed" in self.driver.current_url or "mynetwork" in self.driver.current_url:
                self.is_logged_in = True
                self.logger.info("Login no LinkedIn realizado com sucesso")
                return True
            else:
                self.logger.error("Falha no login do LinkedIn")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro durante login no LinkedIn: {e}")
            return False
    
    def search_jobs(self, keywords: List[str], **kwargs) -> List[Dict]:
        """Busca vagas no LinkedIn."""
        if not self.is_logged_in:
            self.logger.error("Não está logado no LinkedIn")
            return []
        
        jobs = []
        
        try:
            # Buscar vagas oficiais
            official_jobs = self._search_official_jobs(keywords, **kwargs)
            jobs.extend(official_jobs)
            
            # Buscar posts com vagas (imagens)
            post_jobs = self._search_post_jobs(keywords, **kwargs)
            jobs.extend(post_jobs)
            
            self.logger.info(f"Total de {len(jobs)} vagas encontradas no LinkedIn")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Erro na busca de vagas no LinkedIn: {e}")
            return []
    
    def _search_official_jobs(self, keywords: List[str], **kwargs) -> List[Dict]:
        """Busca vagas oficiais do LinkedIn."""
        jobs = []
        
        try:
            # Navegar para página de vagas
            search_query = " OR ".join(keywords)
            jobs_url = f"https://www.linkedin.com/jobs/search/?keywords={search_query}&location=Brasil&f_WT=2&f_TPR=r604800"  # Última semana, remoto
            
            self.driver.get(jobs_url)
            time.sleep(3)
            
            # Scroll para carregar mais vagas
            self._scroll_and_load_more()
            
            # Extrair vagas da página
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            job_cards = soup.find_all('div', class_='base-card')
            
            for card in job_cards:
                try:
                    job = self._extract_job_from_card(card)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    self.logger.warning(f"Erro ao extrair vaga: {e}")
                    continue
            
            self.logger.info(f"Encontradas {len(jobs)} vagas oficiais no LinkedIn")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Erro na busca de vagas oficiais: {e}")
            return []
    
    def _search_post_jobs(self, keywords: List[str], **kwargs) -> List[Dict]:
        """Busca posts com vagas (que podem conter imagens)."""
        jobs = []
        
        try:
            # Navegar para feed
            self.driver.get("https://www.linkedin.com/feed/")
            time.sleep(3)
            
            # Buscar posts com palavras-chave relacionadas a vagas
            search_terms = keywords + ["vaga", "oportunidade", "contratando", "hiring"]
            
            for term in search_terms[:3]:  # Limitar busca
                try:
                    # Usar busca do LinkedIn
                    search_url = f"https://www.linkedin.com/search/results/content/?keywords={term}&datePosted=%22past-week%22"
                    self.driver.get(search_url)
                    time.sleep(3)
                    
                    # Scroll para carregar posts
                    self._scroll_posts()
                    
                    # Extrair posts
                    post_jobs = self._extract_jobs_from_posts()
                    jobs.extend(post_jobs)
                    
                except Exception as e:
                    self.logger.warning(f"Erro na busca de posts para '{term}': {e}")
                    continue
            
            self.logger.info(f"Encontradas {len(jobs)} vagas em posts do LinkedIn")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Erro na busca de posts com vagas: {e}")
            return []
    
    def _scroll_and_load_more(self):
        """Scroll na página de vagas e clica em 'Ver mais'."""
        try:
            for _ in range(3):  # Máximo 3 scrolls
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Tentar clicar em "Ver mais vagas"
                try:
                    see_more_button = self.driver.find_element(
                        By.XPATH, "//button[contains(text(), 'Ver mais vagas') or contains(text(), 'See more jobs')]"
                    )
                    if see_more_button.is_displayed():
                        see_more_button.click()
                        time.sleep(3)
                except NoSuchElementException:
                    pass
                    
        except Exception as e:
            self.logger.warning(f"Erro durante scroll: {e}")
    
    def _scroll_posts(self):
        """Scroll no feed de posts."""
        try:
            for _ in range(2):  # Scroll limitado
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
        except Exception as e:
            self.logger.warning(f"Erro durante scroll de posts: {e}")
    
    def _extract_job_from_card(self, card) -> Optional[Dict]:
        """Extrai informações de uma vaga oficial."""
        try:
            # Título
            title_elem = card.find('h3', class_='base-search-card__title')
            title = title_elem.get_text(strip=True) if title_elem else "N/A"
            
            # Empresa
            company_elem = card.find('h4', class_='base-search-card__subtitle')
            company = company_elem.get_text(strip=True) if company_elem else "N/A"
            
            # Localização
            location_elem = card.find('span', class_='job-search-card__location')
            location = location_elem.get_text(strip=True) if location_elem else "N/A"
            
            # Link
            link_elem = card.find('a', class_='base-card__full-link')
            link = link_elem.get('href') if link_elem else None
            
            # Data de publicação
            time_elem = card.find('time')
            published_date = time_elem.get('datetime') if time_elem else None
            
            if not title or not company:
                return None
            
            return {
                "title": title,
                "company": company,
                "location": location,
                "link": link,
                "published_date": published_date,
                "platform": "linkedin",
                "type": "official",
                "description": "",  # Será preenchido em get_job_details
                "scraped_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.warning(f"Erro ao extrair vaga do card: {e}")
            return None
    
    def _extract_jobs_from_posts(self) -> List[Dict]:
        """Extrai vagas de posts do feed."""
        jobs = []
        
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            posts = soup.find_all('div', class_='feed-shared-update-v2')
            
            for post in posts:
                try:
                    # Verificar se o post contém palavras relacionadas a vagas
                    post_text = post.get_text().lower()
                    job_keywords = ["vaga", "oportunidade", "contratando", "hiring", "job", "position"]
                    
                    if any(keyword in post_text for keyword in job_keywords):
                        job = self._extract_job_from_post(post)
                        if job:
                            jobs.append(job)
                            
                except Exception as e:
                    self.logger.warning(f"Erro ao processar post: {e}")
                    continue
            
            return jobs
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair vagas de posts: {e}")
            return []
    
    def _extract_job_from_post(self, post) -> Optional[Dict]:
        """Extrai informações de vaga de um post."""
        try:
            # Texto do post
            text_elem = post.find('div', class_='feed-shared-text')
            text = text_elem.get_text(strip=True) if text_elem else ""
            
            # Autor do post
            author_elem = post.find('span', class_='feed-shared-actor__name')
            author = author_elem.get_text(strip=True) if author_elem else "N/A"
            
            # Link do post
            link_elem = post.find('a', class_='app-aware-link')
            link = link_elem.get('href') if link_elem else None
            
            # Verificar se há imagens (para OCR posterior)
            images = post.find_all('img', class_='feed-shared-image__image')
            has_images = len(images) > 0
            
            # Extrair título da vaga do texto (heurística)
            title = self._extract_title_from_text(text)
            
            if not title:
                return None
            
            return {
                "title": title,
                "company": author,  # Autor do post como empresa
                "location": "Remoto",  # Assumir remoto para posts
                "link": link,
                "published_date": None,
                "platform": "linkedin",
                "type": "post",
                "description": text,
                "has_images": has_images,
                "scraped_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.warning(f"Erro ao extrair vaga do post: {e}")
            return None
    
    def _extract_title_from_text(self, text: str) -> Optional[str]:
        """Extrai título da vaga do texto do post usando heurísticas."""
        try:
            # Padrões comuns para títulos de vagas
            patterns = [
                r"vaga.*?para\s+([^.!?\n]+)",
                r"contratando\s+([^.!?\n]+)",
                r"oportunidade.*?([^.!?\n]+)",
                r"hiring\s+([^.!?\n]+)",
                r"position.*?([^.!?\n]+)"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    if len(title) > 5 and len(title) < 100:  # Validação básica
                        return title
            
            # Se não encontrar padrão, usar primeiras palavras
            words = text.split()
            if len(words) >= 3:
                return " ".join(words[:5])  # Primeiras 5 palavras
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Erro ao extrair título: {e}")
            return None
    
    def get_job_details(self, job_url: str) -> Optional[Dict]:
        """Obtém detalhes completos de uma vaga."""
        try:
            if not job_url:
                return None
            
            self.driver.get(job_url)
            time.sleep(3)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Descrição completa
            description_elem = soup.find('div', class_='show-more-less-html__markup')
            description = description_elem.get_text(strip=True) if description_elem else ""
            
            # Informações adicionais
            criteria = {}
            criteria_sections = soup.find_all('li', class_='description__job-criteria-item')
            
            for section in criteria_sections:
                try:
                    label_elem = section.find('h3')
                    value_elem = section.find('span')
                    
                    if label_elem and value_elem:
                        label = label_elem.get_text(strip=True)
                        value = value_elem.get_text(strip=True)
                        criteria[label] = value
                except:
                    continue
            
            return {
                "description": description,
                "criteria": criteria,
                "scraped_details_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter detalhes da vaga {job_url}: {e}")
            return None
    
    def close(self):
        """Fecha o driver e limpa recursos."""
        try:
            if self.driver:
                self.driver.quit()
                self.logger.info("Driver do LinkedIn fechado")
        except Exception as e:
            self.logger.warning(f"Erro ao fechar driver: {e}")
        
        super().close()

