"""
API endpoints para gerenciamento de vagas
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
import asyncio

from backend.modules.scraping.scraper_manager import ScraperManager
from backend.modules.ai.ai_manager import AIManager
from backend.modules.database.repositories import JobRepository, UserRepository
from backend.modules.database.database import DatabaseManager

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

# Dependency injection
def get_db():
    return DatabaseManager()

def get_scraper_manager():
    return ScraperManager()

def get_ai_manager():
    return AIManager()

@router.get("/")
async def get_jobs(
    platform: Optional[str] = Query(None, description="Filtrar por plataforma"),
    min_score: Optional[int] = Query(None, description="Pontuação mínima"),
    status: Optional[str] = Query(None, description="Status da vaga"),
    search: Optional[str] = Query(None, description="Busca por texto"),
    limit: int = Query(50, description="Limite de resultados"),
    offset: int = Query(0, description="Offset para paginação"),
    db: DatabaseManager = Depends(get_db)
):
    """Listar vagas com filtros"""
    try:
        job_repo = JobRepository(db)
        jobs = job_repo.get_jobs_with_filters(
            platform=platform,
            min_score=min_score,
            status=status,
            search_term=search,
            limit=limit,
            offset=offset
        )
        return {
            "success": True,
            "data": jobs,
            "total": len(jobs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{job_id}")
async def get_job(job_id: int, db: DatabaseManager = Depends(get_db)):
    """Obter detalhes de uma vaga específica"""
    try:
        job_repo = JobRepository(db)
        job = job_repo.get_job_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Vaga não encontrada")
        return {
            "success": True,
            "data": job
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scrape")
async def start_scraping(
    platforms: Optional[List[str]] = None,
    scraper_manager: ScraperManager = Depends(get_scraper_manager),
    db: DatabaseManager = Depends(get_db)
):
    """Iniciar processo de scraping"""
    try:
        if not platforms:
            platforms = ["linkedin", "gupy", "catho", "himalayas"]
        
        # Executar scraping em background
        results = await asyncio.create_task(
            scraper_manager.run_all_scrapers_async(platforms)
        )
        
        return {
            "success": True,
            "message": "Scraping iniciado com sucesso",
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{job_id}/analyze")
async def analyze_job(
    job_id: int,
    ai_manager: AIManager = Depends(get_ai_manager),
    db: DatabaseManager = Depends(get_db)
):
    """Analisar compatibilidade de uma vaga"""
    try:
        job_repo = JobRepository(db)
        job = job_repo.get_job_by_id(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Vaga não encontrada")
        
        # Executar análise de IA
        analysis = await ai_manager.analyze_job_compatibility(job)
        
        # Salvar análise no banco
        job_repo.save_job_analysis(job_id, analysis)
        
        return {
            "success": True,
            "data": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/overview")
async def get_jobs_stats(db: DatabaseManager = Depends(get_db)):
    """Obter estatísticas gerais das vagas"""
    try:
        job_repo = JobRepository(db)
        stats = {
            "total_jobs": job_repo.count_total_jobs(),
            "new_jobs_today": job_repo.count_jobs_by_date(datetime.now().date()),
            "jobs_by_platform": job_repo.get_jobs_count_by_platform(),
            "jobs_by_score_range": job_repo.get_jobs_count_by_score_range(),
            "avg_compatibility_score": job_repo.get_average_compatibility_score()
        }
        
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{job_id}/bookmark")
async def toggle_bookmark(
    job_id: int,
    db: DatabaseManager = Depends(get_db)
):
    """Favoritar/desfavoritar uma vaga"""
    try:
        job_repo = JobRepository(db)
        result = job_repo.toggle_job_bookmark(job_id)
        
        return {
            "success": True,
            "bookmarked": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

