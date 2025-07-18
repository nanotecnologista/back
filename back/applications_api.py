
"""
API endpoints para gerenciamento de aplicações de vagas
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime

from backend.modules.database.repositories import JobApplicationRepository, JobRepository
from backend.modules.database.database import DatabaseManager

router = APIRouter(prefix="/api/applications", tags=["applications"])

# Dependency injection
def get_db():
    return DatabaseManager()

@router.get("/")
async def get_applications(
    status: Optional[str] = Query(None, description="Filtrar por status"),
    search: Optional[str] = Query(None, description="Busca por texto"),
    limit: int = Query(50, description="Limite de resultados"),
    offset: int = Query(0, description="Offset para paginação"),
    db: DatabaseManager = Depends(get_db)
):
    """Listar aplicações com filtros"""
    try:
        app_repo = JobApplicationRepository(db)
        applications = app_repo.get_applications_with_filters(
            status=status,
            search_term=search,
            limit=limit,
            offset=offset
        )
        return {
            "success": True,
            "data": applications,
            "total": len(applications)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{application_id}")
async def get_application(application_id: int, db: DatabaseManager = Depends(get_db)):
    """Obter detalhes de uma aplicação específica"""
    try:
        app_repo = JobApplicationRepository(db)
        application = app_repo.get_by_id(application_id)
        if not application:
            raise HTTPException(status_code=404, detail="Aplicação não encontrada")
        return {
            "success": True,
            "data": application
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{job_id}/apply")
async def apply_to_job(
    job_id: int,
    application_method: str = "automatic",
    db: DatabaseManager = Depends(get_db)
):
    """Registrar uma aplicação para uma vaga"""
    try:
        job_repo = JobRepository(db)
        job = job_repo.get_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Vaga não encontrada")
        
        app_repo = JobApplicationRepository(db)
        application = app_repo.create(
            job_id=job_id,
            application_method=application_method,
            status="applied"
        )
        
        return {
            "success": True,
            "message": "Aplicação registrada com sucesso",
            "data": application
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{application_id}/status")
async def update_application_status(
    application_id: int,
    new_status: str = Query(..., description="Novo status da aplicação"),
    db: DatabaseManager = Depends(get_db)
):
    """Atualizar o status de uma aplicação"""
    try:
        app_repo = JobApplicationRepository(db)
        updated_app = app_repo.update(application_id, status=new_status)
        if not updated_app:
            raise HTTPException(status_code=404, detail="Aplicação não encontrada")
        return {
            "success": True,
            "message": "Status da aplicação atualizado",
            "data": updated_app
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/overview")
async def get_applications_stats(db: DatabaseManager = Depends(get_db)):
    """Obter estatísticas gerais das aplicações"""
    try:
        app_repo = JobApplicationRepository(db)
        stats = {
            "total_applications": app_repo.get_applications_stats().get("total", 0),
            "applications_by_status": app_repo.get_applications_stats().get("by_status", {}),
            "success_rate": app_repo.get_applications_stats().get("success_rate", 0),
            "avg_response_time": app_repo.get_applications_stats().get("avg_response_time", 0)
        }
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

