"""
Gerenciador central de notificações.
"""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

from .telegram_notifier import TelegramNotifier
from .email_notifier import EmailNotifier
from backend.modules.database.database import db_manager
from backend.modules.database.repositories import NotificationRepository, ActivityLogRepository
from backend.config.settings import settings
from backend.config.logging_config import get_logger


class NotificationManager:
    """Gerenciador central de notificações."""
    
    def __init__(self):
        self.logger = get_logger("notifications.manager")
        self.telegram = TelegramNotifier()
        self.email = EmailNotifier()
        self.executor = ThreadPoolExecutor(max_workers=3)
        
    def send_notification(self, notification_type: str, message: str, 
                         user_id: str = None, title: str = None,
                         priority: str = "normal", metadata: Dict = None) -> bool:
        """Envia notificação através dos canais configurados."""
        try:
            success = False
            
            # Telegram (prioritário)
            if self.telegram.bot_token and self.telegram.chat_id:
                if notification_type in ["job_alert", "application_update", "error", "daily_summary"]:
                    success = self.telegram.send_message(message)
            
            # Email (backup ou específico)
            if notification_type in ["daily_summary", "application_materials"] and settings.EMAIL_ADDRESS:
                success = self.email.send_email(
                    to_email=settings.EMAIL_ADDRESS,
                    subject=title or "Notificação do Sistema",
                    body=message
                ) or success
            
            # Log da atividade
            with db_manager.session_scope() as session:
                log_repo = ActivityLogRepository(session)
                log_repo.log_activity(
                    action="send_notification",
                    category="notification",
                    description=f"Notificação {notification_type} enviada",
                    user_id=user_id,
                    extra_data={
                        "type": notification_type,
                        "priority": priority,
                        "success": success,
                        **(metadata or {})
                    },
                    success=success
                )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar notificação: {e}")
            return False
    
    def process_notification_queue(self) -> int:
        """Processa fila de notificações pendentes."""
        try:
            processed = 0
            
            with db_manager.session_scope() as session:
                notification_repo = NotificationRepository(session)
                pending_notifications = notification_repo.get_pending_notifications(limit=50)
                
                for notification in pending_notifications:
                    try:
                        success = False
                        
                        if notification.type == "telegram":
                            success = self.telegram.send_message(notification.message)
                        elif notification.type == "email":
                            success = self.email.send_email(
                                to_email=settings.EMAIL_ADDRESS,
                                subject=notification.title or "Notificação",
                                body=notification.message
                            )
                        
                        if success:
                            notification_repo.mark_notification_sent(notification.id)
                            processed += 1
                        else:
                            notification_repo.mark_notification_failed(
                                notification.id, 
                                "Falha no envio"
                            )
                            
                    except Exception as e:
                        notification_repo.mark_notification_failed(
                            notification.id, 
                            str(e)
                        )
                        self.logger.error(f"Erro ao processar notificação {notification.id}: {e}")
            
            if processed > 0:
                self.logger.info(f"Processadas {processed} notificações")
            
            return processed
            
        except Exception as e:
            self.logger.error(f"Erro ao processar fila de notificações: {e}")
            return 0
    
    def notify_new_jobs(self, jobs: List[Dict], analysis_summary: Dict = None) -> bool:
        """Notifica sobre novas vagas encontradas."""
        try:
            if not jobs:
                return True
            
            # Telegram
            telegram_success = self.telegram.send_job_alert(jobs, analysis_summary)
            
            # Email (se configurado)
            email_success = True
            if settings.EMAIL_ADDRESS:
                email_success = self.email.send_job_alert_email(
                    settings.EMAIL_ADDRESS, jobs, analysis_summary
                )
            
            return telegram_success or email_success
            
        except Exception as e:
            self.logger.error(f"Erro ao notificar novas vagas: {e}")
            return False
    
    def notify_application_update(self, job_title: str, company: str, 
                                status: str, user_id: str = None) -> bool:
        """Notifica sobre atualização de aplicação."""
        try:
            return self.telegram.send_application_update(job_title, company, status)
        except Exception as e:
            self.logger.error(f"Erro ao notificar atualização de aplicação: {e}")
            return False
    
    def notify_error(self, error_type: str, error_message: str, 
                    module: str = None) -> bool:
        """Notifica sobre erros do sistema."""
        try:
            return self.telegram.send_error_alert(error_type, error_message, module)
        except Exception as e:
            self.logger.error(f"Erro ao notificar erro: {e}")
            return False
    
    def send_daily_summary(self, summary_data: Dict) -> bool:
        """Envia resumo diário."""
        try:
            # Telegram
            telegram_success = self.telegram.send_daily_summary(summary_data)
            
            # Email
            email_success = True
            if settings.EMAIL_ADDRESS:
                email_success = self.email.send_daily_summary_email(
                    settings.EMAIL_ADDRESS, summary_data
                )
            
            return telegram_success or email_success
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar resumo diário: {e}")
            return False
    
    def notify_questionnaire_attention(self, job_title: str, company: str, 
                                     complex_questions_count: int) -> bool:
        """Notifica sobre questionário que precisa de atenção."""
        try:
            return self.telegram.send_questionnaire_alert(
                job_title, company, complex_questions_count
            )
        except Exception as e:
            self.logger.error(f"Erro ao notificar questionário: {e}")
            return False
    
    def test_all_channels(self) -> Dict[str, bool]:
        """Testa todos os canais de notificação."""
        try:
            results = {}
            
            # Telegram
            results["telegram"] = self.telegram.test_connection()
            
            # Email
            results["email"] = self.email.test_connection()
            
            self.logger.info(f"Teste de canais: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"Erro ao testar canais: {e}")
            return {"telegram": False, "email": False}
    
    def get_notification_stats(self) -> Dict:
        """Retorna estatísticas de notificações."""
        try:
            with db_manager.session_scope() as session:
                notification_repo = NotificationRepository(session)
                
                # Últimas 24 horas
                since = datetime.utcnow() - timedelta(hours=24)
                recent_notifications = notification_repo.session.query(
                    notification_repo.model_class
                ).filter(
                    notification_repo.model_class.created_at >= since
                ).all()
                
                stats = {
                    "total_24h": len(recent_notifications),
                    "sent_24h": len([n for n in recent_notifications if n.status == "sent"]),
                    "failed_24h": len([n for n in recent_notifications if n.status == "failed"]),
                    "pending": len([n for n in recent_notifications if n.status == "pending"]),
                    "by_type": {}
                }
                
                # Por tipo
                for notification in recent_notifications:
                    type_name = notification.type
                    if type_name not in stats["by_type"]:
                        stats["by_type"][type_name] = 0
                    stats["by_type"][type_name] += 1
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas: {e}")
            return {}


# Instância global
notification_manager = NotificationManager()

