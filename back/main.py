"""
Aplicação principal FastAPI.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente do .env
load_dotenv()

from backend.modules.database.database import db_manager
from backend.app.api.jobs import router as jobs_router
from backend.app.api.applications import router as applications_router
from backend.app.api.settings import router as settings_router

# Inicializar o FastAPI
app = FastAPI(
    title="Job Automation API",
    description="API para automação de vagas de emprego e gestão de candidaturas.",
    version="0.1.0",
)

# Configurar CORS
origins = [
    "http://localhost:5173",  # Frontend development server
    "http://localhost:8000",  # Backend development server
    # Adicione outras origens permitidas em produção
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers da API
app.include_router(jobs_router, prefix="/api/jobs", tags=["jobs"])
app.include_router(applications_router, prefix="/api/applications", tags=["applications"])
app.include_router(settings_router, prefix="/api/settings", tags=["settings"])

# Eventos de inicialização e desligamento
@app.on_event("startup")
async def startup_event():
    db_manager.create_tables()
    print("Database tables created/checked.")

@app.on_event("shutdown")
async def shutdown_event():
    print("Application shutting down.")

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Job Automation API"}


