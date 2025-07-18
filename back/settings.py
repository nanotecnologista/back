"""
Configurações da aplicação de automação de vagas de emprego.
"""
import os
from typing import List, Optional
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()


class Settings:
    """Classe de configurações da aplicação."""
    
    # Database Configuration
    DATABASE_TYPE: str = os.getenv("DATABASE_TYPE", "sqlite")
    DATABASE_HOST: str = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT: int = int(os.getenv("DATABASE_PORT", "5432"))
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "job_automation")
    DATABASE_USER: str = os.getenv("DATABASE_USER", "")
    DATABASE_PASSWORD: str = os.getenv("DATABASE_PASSWORD", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///job_automation.db")
    DATABASE_ECHO: bool = os.getenv("DATABASE_ECHO", "False").lower() == "true"
    
    # OpenAI API Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    
    # Email Configuration
    EMAIL_ADDRESS: str = os.getenv("EMAIL_ADDRESS", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    
    # Platform Credentials
    LINKEDIN_EMAIL: str = os.getenv("LINKEDIN_EMAIL", "")
    LINKEDIN_PASSWORD: str = os.getenv("LINKEDIN_PASSWORD", "")
    
    GUPY_EMAIL: str = os.getenv("GUPY_EMAIL", "")
    GUPY_PASSWORD: str = os.getenv("GUPY_PASSWORD", "")
    
    CATHO_EMAIL: str = os.getenv("CATHO_EMAIL", "")
    CATHO_PASSWORD: str = os.getenv("CATHO_PASSWORD", "")
    
    HIMALAYAS_EMAIL: str = os.getenv("HIMALAYAS_EMAIL", "")
    HIMALAYAS_PASSWORD: str = os.getenv("HIMALAYAS_PASSWORD", "")
    
    REMOTAR_EMAIL: str = os.getenv("REMOTAR_EMAIL", "")
    REMOTAR_PASSWORD: str = os.getenv("REMOTAR_PASSWORD", "")
    
    QUEROHOME_EMAIL: str = os.getenv("QUEROHOME_EMAIL", "")
    QUEROHOME_PASSWORD: str = os.getenv("QUEROHOME_PASSWORD", "")
    
    # Application Settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    SCRAPING_DELAY_MIN: int = int(os.getenv("SCRAPING_DELAY_MIN", "1"))
    SCRAPING_DELAY_MAX: int = int(os.getenv("SCRAPING_DELAY_MAX", "10"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    
    # User Profile Information
    USER_FULL_NAME: str = os.getenv("USER_FULL_NAME", "")
    USER_PHONE: str = os.getenv("USER_PHONE", "")
    USER_LOCATION: str = os.getenv("USER_LOCATION", "")
    USER_LINKEDIN_PROFILE: str = os.getenv("USER_LINKEDIN_PROFILE", "")
    
    # Job Search Filters
    SEARCH_KEYWORDS_DEV: List[str] = os.getenv(
        "SEARCH_KEYWORDS_DEV", 
        "python,javascript,typescript,backend,salesforce,go,apex"
    ).split(",")
    
    SEARCH_KEYWORDS_ADMIN: List[str] = os.getenv(
        "SEARCH_KEYWORDS_ADMIN", 
        "call center,assistente administrativo,suporte,customer service"
    ).split(",")
    
    BLACKLIST_COMPANIES: List[str] = os.getenv(
        "BLACKLIST_COMPANIES", 
        "WiseUp"
    ).split(",")
    
    BLACKLIST_KEYWORDS: List[str] = os.getenv(
        "BLACKLIST_KEYWORDS", 
        "100% comissionado,sem CLT,autônomo"
    ).split(",")
    
    # Supported Platforms
    SUPPORTED_PLATFORMS = [
        "linkedin",
        "gupy", 
        "catho",
        "himalayas",
        "remotar",
        "querohome"
    ]
    
    # Job Types
    JOB_TYPES = {
        "dev": {
            "keywords": SEARCH_KEYWORDS_DEV,
            "resume_template": "dev_resume_template"
        },
        "admin": {
            "keywords": SEARCH_KEYWORDS_ADMIN,
            "resume_template": "admin_resume_template"
        }
    }
    
    # Languages
    SUPPORTED_LANGUAGES = ["pt", "en"]
    
    @classmethod
    def validate_required_settings(cls) -> List[str]:
        """Valida se as configurações obrigatórias estão definidas."""
        missing_settings = []
        
        required_settings = [
            "DATABASE_URL",
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_CHAT_ID",
            "USER_FULL_NAME",
            "USER_PHONE",
            "EMAIL_ADDRESS"
        ]
        
        for setting in required_settings:
            if not getattr(cls, setting):
                missing_settings.append(setting)
        
        return missing_settings


# Instância global das configurações
settings = Settings()

