"""
Configuração de logging para a aplicação.
"""
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

from .settings import settings


def setup_logging():
    """Configura o sistema de logging da aplicação."""
    
    # Cria diretório de logs se não existir
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configuração do formato de log
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Configuração do logger principal
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Remove handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Handler para arquivo de log geral
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "job_automation.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    logger.addHandler(file_handler)
    
    # Handler para arquivo de log de erros
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / "errors.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(log_format, date_format))
    logger.addHandler(error_handler)
    
    # Handler para console (apenas em modo debug)
    if settings.DEBUG:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter(log_format, date_format))
        logger.addHandler(console_handler)
    
    # Configuração de loggers específicos
    
    # Logger para scraping
    scraping_logger = logging.getLogger("scraping")
    scraping_handler = logging.handlers.RotatingFileHandler(
        log_dir / "scraping.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    scraping_handler.setFormatter(logging.Formatter(log_format, date_format))
    scraping_logger.addHandler(scraping_handler)
    
    # Logger para aplicações
    applications_logger = logging.getLogger("applications")
    applications_handler = logging.handlers.RotatingFileHandler(
        log_dir / "applications.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    applications_handler.setFormatter(logging.Formatter(log_format, date_format))
    applications_logger.addHandler(applications_handler)
    
    # Logger para IA
    ai_logger = logging.getLogger("ai")
    ai_handler = logging.handlers.RotatingFileHandler(
        log_dir / "ai.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    ai_handler.setFormatter(logging.Formatter(log_format, date_format))
    ai_logger.addHandler(ai_handler)
    
    # Reduz verbosidade de bibliotecas externas
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    logger.info("Sistema de logging configurado com sucesso")
    return logger


def get_logger(name: str) -> logging.Logger:
    """Retorna um logger com o nome especificado."""
    return logging.getLogger(name)

