"""
Script de teste para validar funcionamento dos scrapers.
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path

from scraper_manager import ScraperManager
from backend.config.settings import settings
from backend.config.logging_config import setup_logging, get_logger


def test_scrapers():
    """Testa todos os scrapers disponíveis."""
    # Configurar logging
    setup_logging()
    logger = get_logger("scraping.test")
    
    logger.info("Iniciando teste dos scrapers")
    
    try:
        # Inicializar gerenciador
        with ScraperManager() as manager:
            # Inicializar scrapers
            success = manager.initialize_scrapers()
            if not success:
                logger.error("Falha ao inicializar scrapers")
                return
            
            # Verificar status
            status = manager.get_platform_status()
            logger.info(f"Status das plataformas: {json.dumps(status, indent=2)}")
            
            # Fazer login (apenas em plataformas com credenciais)
            login_results = manager.login_all()
            logger.info(f"Resultados do login: {login_results}")
            
            # Testar busca para desenvolvedor
            logger.info("Testando busca para desenvolvedor...")
            dev_results = manager.search_all_platforms(job_type="dev")
            
            # Testar busca para atendimento
            logger.info("Testando busca para atendimento...")
            admin_results = manager.search_all_platforms(job_type="admin")
            
            # Salvar resultados
            save_test_results(dev_results, admin_results, logger)
            
            # Testar obtenção de detalhes (apenas algumas vagas)
            test_job_details(manager, dev_results, logger)
            
    except Exception as e:
        logger.error(f"Erro durante teste: {e}", exc_info=True)


def save_test_results(dev_results: dict, admin_results: dict, logger):
    """Salva resultados dos testes em arquivos."""
    try:
        # Criar diretório de resultados
        results_dir = Path("test_results")
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Salvar resultados de desenvolvedor
        dev_file = results_dir / f"dev_jobs_{timestamp}.json"
        with open(dev_file, 'w', encoding='utf-8') as f:
            json.dump(dev_results, f, indent=2, ensure_ascii=False, default=str)
        
        # Salvar resultados de atendimento
        admin_file = results_dir / f"admin_jobs_{timestamp}.json"
        with open(admin_file, 'w', encoding='utf-8') as f:
            json.dump(admin_results, f, indent=2, ensure_ascii=False, default=str)
        
        # Estatísticas
        dev_total = sum(len(jobs) for jobs in dev_results.values())
        admin_total = sum(len(jobs) for jobs in admin_results.values())
        
        stats = {
            "timestamp": timestamp,
            "dev_jobs": {
                "total": dev_total,
                "by_platform": {platform: len(jobs) for platform, jobs in dev_results.items()}
            },
            "admin_jobs": {
                "total": admin_total,
                "by_platform": {platform: len(jobs) for platform, jobs in admin_results.items()}
            }
        }
        
        stats_file = results_dir / f"stats_{timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Resultados salvos em {results_dir}")
        logger.info(f"Desenvolvedor: {dev_total} vagas")
        logger.info(f"Atendimento: {admin_total} vagas")
        
    except Exception as e:
        logger.error(f"Erro ao salvar resultados: {e}")


def test_job_details(manager: ScraperManager, results: dict, logger):
    """Testa obtenção de detalhes de algumas vagas."""
    try:
        # Coletar algumas vagas para teste
        test_jobs = []
        
        for platform, jobs in results.items():
            if jobs:
                # Pegar até 2 vagas por plataforma
                test_jobs.extend(jobs[:2])
        
        if not test_jobs:
            logger.warning("Nenhuma vaga disponível para teste de detalhes")
            return
        
        logger.info(f"Testando detalhes de {len(test_jobs)} vagas")
        
        # Obter detalhes
        enriched_jobs = manager.get_job_details_batch(test_jobs[:5])  # Máximo 5 vagas
        
        # Salvar vagas com detalhes
        details_file = Path("test_results") / f"job_details_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(details_file, 'w', encoding='utf-8') as f:
            json.dump(enriched_jobs, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Detalhes de vagas salvos em {details_file}")
        
    except Exception as e:
        logger.error(f"Erro ao testar detalhes de vagas: {e}")


def test_specific_platform(platform_name: str):
    """Testa uma plataforma específica."""
    setup_logging()
    logger = get_logger(f"scraping.test.{platform_name}")
    
    try:
        with ScraperManager() as manager:
            # Inicializar apenas a plataforma específica
            success = manager.initialize_scrapers([platform_name])
            if not success:
                logger.error(f"Falha ao inicializar scraper {platform_name}")
                return
            
            # Login
            login_results = manager.login_all()
            logger.info(f"Login em {platform_name}: {login_results.get(platform_name, False)}")
            
            # Buscar vagas
            results = manager.search_specific_platforms([platform_name], "dev")
            
            jobs = results.get(platform_name, [])
            logger.info(f"Encontradas {len(jobs)} vagas em {platform_name}")
            
            # Salvar resultados
            if jobs:
                results_file = Path("test_results") / f"{platform_name}_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                results_file.parent.mkdir(exist_ok=True)
                
                with open(results_file, 'w', encoding='utf-8') as f:
                    json.dump(jobs, f, indent=2, ensure_ascii=False, default=str)
                
                logger.info(f"Resultados salvos em {results_file}")
            
    except Exception as e:
        logger.error(f"Erro ao testar {platform_name}: {e}", exc_info=True)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Testar plataforma específica
        platform = sys.argv[1]
        test_specific_platform(platform)
    else:
        # Testar todas as plataformas
        test_scrapers()

