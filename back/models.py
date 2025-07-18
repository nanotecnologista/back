"""
Modelos do banco de dados usando SQLAlchemy.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float, 
    ForeignKey, JSON, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


class User(Base):
    """Modelo para usuários do sistema."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50))
    location = Column(String(255))
    linkedin_profile = Column(String(500))
    
    # Configurações
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    preferences = relationship("UserPreferences", back_populates="user", uselist=False)
    applications = relationship("JobApplication", back_populates="user")
    logs = relationship("ActivityLog", back_populates="user")
    
    def __repr__(self):
        return f"<User(email='{self.email}', name='{self.full_name}')>"


class UserPreferences(Base):
    """Preferências do usuário para busca de vagas."""
    __tablename__ = "user_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Preferências de busca
    job_types = Column(JSON, default=["dev"])  # ["dev", "admin"]
    platforms = Column(JSON, default=["linkedin", "gupy", "catho"])
    keywords = Column(JSON, default=[])
    blacklist_companies = Column(JSON, default=[])
    blacklist_keywords = Column(JSON, default=[])
    
    # Filtros
    min_compatibility_score = Column(Float, default=60.0)
    remote_only = Column(Boolean, default=True)
    max_experience_years = Column(Integer, default=2)
    
    # Configurações de automação
    auto_apply_enabled = Column(Boolean, default=False)
    auto_apply_threshold = Column(Float, default=80.0)
    max_applications_per_day = Column(Integer, default=5)
    
    # Notificações
    telegram_notifications = Column(Boolean, default=True)
    email_notifications = Column(Boolean, default=False)
    daily_summary = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self):
        return f"<UserPreferences(user_id='{self.user_id}')>"


class Job(Base):
    """Modelo para vagas de emprego."""
    __tablename__ = "jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Informações básicas
    title = Column(String(500), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255))
    platform = Column(String(100), nullable=False)
    external_id = Column(String(255))  # ID na plataforma original
    url = Column(Text, nullable=False)
    
    # Conteúdo
    description = Column(Text)
    requirements = Column(Text)
    benefits = Column(Text)
    salary_info = Column(String(255))
    
    # Metadados
    work_mode = Column(String(50))  # remoto, híbrido, presencial
    experience_level = Column(String(50))  # júnior, pleno, sênior
    job_type = Column(String(50))  # dev, admin, etc.
    
    # Status
    is_active = Column(Boolean, default=True)
    is_analyzed = Column(Boolean, default=False)
    
    # Timestamps
    posted_at = Column(DateTime)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    analysis = relationship("JobAnalysis", back_populates="job", uselist=False)
    applications = relationship("JobApplication", back_populates="job")
    questionnaires = relationship("JobQuestionnaire", back_populates="job")
    
    # Índices
    __table_args__ = (
        Index('idx_job_platform_external', 'platform', 'external_id'),
        Index('idx_job_company', 'company'),
        Index('idx_job_scraped_at', 'scraped_at'),
        UniqueConstraint('platform', 'external_id', name='uq_job_platform_external'),
    )
    
    def __repr__(self):
        return f"<Job(title='{self.title}', company='{self.company}')>"


class JobAnalysis(Base):
    """Análise de compatibilidade de vagas."""
    __tablename__ = "job_analyses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    
    # Resultados da análise
    job_type = Column(String(50))
    language = Column(String(10))
    compatibility_score = Column(Float, nullable=False)
    
    # Análise detalhada
    requirements_analysis = Column(JSON)
    key_information = Column(JSON)
    recommendations = Column(JSON)
    
    # Metadados
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    analyzer_version = Column(String(50))
    
    # Relacionamentos
    job = relationship("Job", back_populates="analysis")
    
    def __repr__(self):
        return f"<JobAnalysis(job_id='{self.job_id}', score={self.compatibility_score})>"


class JobApplication(Base):
    """Aplicações em vagas."""
    __tablename__ = "job_applications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    
    # Status da aplicação
    status = Column(String(50), default="pending")  # pending, applied, rejected, interview, hired
    application_method = Column(String(50))  # manual, automatic
    
    # Materiais gerados
    resume_data = Column(JSON)
    cover_letter_data = Column(JSON)
    questionnaire_responses = Column(JSON)
    
    # Timestamps
    applied_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    
    # Índices
    __table_args__ = (
        Index('idx_application_user_job', 'user_id', 'job_id'),
        Index('idx_application_status', 'status'),
        UniqueConstraint('user_id', 'job_id', name='uq_user_job_application'),
    )
    
    def __repr__(self):
        return f"<JobApplication(user_id='{self.user_id}', job_id='{self.job_id}', status='{self.status}')>"


class JobQuestionnaire(Base):
    """Questionários de vagas."""
    __tablename__ = "job_questionnaires"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    
    # Dados do questionário
    questions = Column(JSON, nullable=False)
    responses = Column(JSON)
    
    # Status
    is_completed = Column(Boolean, default=False)
    needs_human_review = Column(Boolean, default=False)
    auto_answered_count = Column(Integer, default=0)
    total_questions_count = Column(Integer, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relacionamentos
    job = relationship("Job", back_populates="questionnaires")
    
    def __repr__(self):
        return f"<JobQuestionnaire(job_id='{self.job_id}', completed={self.is_completed})>"


class ActivityLog(Base):
    """Log de atividades do sistema."""
    __tablename__ = "activity_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Informações do log
    action = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)  # scraping, analysis, application, notification
    description = Column(Text)
    
    # Dados adicionais
    extra_data = Column(JSON)
    
    # Status
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    user = relationship("User", back_populates="logs")
    
    # Índices
    __table_args__ = (
        Index('idx_log_category_created', 'category', 'created_at'),
        Index('idx_log_user_created', 'user_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ActivityLog(action='{self.action}', category='{self.category}')>"


class ScrapingSession(Base):
    """Sessões de scraping."""
    __tablename__ = "scraping_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Informações da sessão
    platforms = Column(JSON, nullable=False)
    job_types = Column(JSON, nullable=False)
    
    # Resultados
    total_jobs_found = Column(Integer, default=0)
    new_jobs_count = Column(Integer, default=0)
    updated_jobs_count = Column(Integer, default=0)
    
    # Status
    status = Column(String(50), default="running")  # running, completed, failed
    error_message = Column(Text)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Metadados
    session_metadata = Column(JSON)
    
    def __repr__(self):
        return f"<ScrapingSession(id='{self.id}', status='{self.status}')>"


class NotificationQueue(Base):
    """Fila de notificações."""
    __tablename__ = "notification_queue"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Informações da notificação
    type = Column(String(50), nullable=False)  # telegram, email, webhook
    title = Column(String(255))
    message = Column(Text, nullable=False)
    
    # Configurações
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    scheduled_for = Column(DateTime, default=datetime.utcnow)
    
    # Status
    status = Column(String(50), default="pending")  # pending, sent, failed, cancelled
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime)
    
    # Metadados
    notification_metadata = Column(JSON)
    error_message = Column(Text)
    
    # Índices
    __table_args__ = (
        Index('idx_notification_status_scheduled', 'status', 'scheduled_for'),
        Index('idx_notification_user_created', 'user_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<NotificationQueue(type='{self.type}', status='{self.status}')>"


class SystemConfig(Base):
    """Configurações do sistema."""
    __tablename__ = "system_config"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Chave e valor
    key = Column(String(255), unique=True, nullable=False)
    value = Column(JSON)
    description = Column(Text)
    
    # Metadados
    category = Column(String(100))
    is_sensitive = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SystemConfig(key='{self.key}')>"

