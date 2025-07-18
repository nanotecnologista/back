"""
API endpoints para gerenciamento de configurações do usuário
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any

from backend.modules.database.repositories import UserRepository
from backend.modules.database.database import DatabaseManager

router = APIRouter(prefix="/api/settings", tags=["settings"])

# Dependency injection
def get_db():
    return DatabaseManager()

class SettingsModel(BaseModel):
    profile: Dict[str, Any]
    preferences: Dict[str, Any]
    notifications: Dict[str, Any]
    automation: Dict[str, Any]
    credentials: Dict[str, Any]
    filters: Dict[str, Any]

@router.get("/")
async def get_settings(db: DatabaseManager = Depends(get_db)):
    """Obter todas as configurações do usuário"""
    try:
        user_repo = UserRepository(db)
        # Assuming a single user system for now, with user_id=1
        settings = user_repo.get_user_settings(1)
        if not settings:
            raise HTTPException(status_code=404, detail="Configurações não encontradas")
        return {
            "success": True,
            "data": settings
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/")
async def update_settings(settings: SettingsModel, db: DatabaseManager = Depends(get_db)):
    """Atualizar todas as configurações do usuário"""
    try:
        user_repo = UserRepository(db)
        # Assuming a single user system for now, with user_id=1
        updated_settings = user_repo.update_user_settings(1, settings.dict())
        return {
            "success": True,
            "message": "Configurações atualizadas com sucesso",
            "data": updated_settings
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

