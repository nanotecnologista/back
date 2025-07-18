"""
Notificador via Telegram.
"""
import asyncio
import requests
from typing import Optional, Dict, Any
from datetime import datetime

from backend.config.settings import settings
from backend.config.logging_config import get_logger


class TelegramNotifier:
    """Notificador via Telegram Bot."""
    
    def __init__(self):
        self.logger = get_logger("notifications.telegram")
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        if not self.bot_token or not self.chat_id:
            self.logger.warning("Token do bot ou chat ID não configurados")
    
    def send_message(self, message: str, parse_mode: str = "Markdown", 
                    disable_notification: bool = False) -> bool:
        """Envia mensagem via Telegram."""
        try:
            if not self.bot_token or not self.chat_id:
                self.logger.error("Telegram não configurado")
                return False
            
            url = f"{self.base_url}/sendMessage"
            
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode,
                "disable_notification": disable_notification
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                self.logger.info("Mensagem enviada com sucesso via Telegram")
                return True
            else:
                self.logger.error(f"Erro ao enviar mensagem: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro no envio via Telegram: {e}")
            return False
    
    def send_job_alert(self, jobs: list, analysis_summary: Dict = None) -> bool:
        """Envia alerta sobre novas vagas."""
        try:
            if not jobs:
                return True
            
            message = "🎯 *Novas Vagas Encontradas!*\n\n"
            
            # Resumo
            if analysis_summary:
                total = analysis_summary.get("total_jobs", len(jobs))
                avg_score = analysis_summary.get("average_score", 0)
                should_apply = analysis_summary.get("recommendations", {}).get("should_apply", 0)
                
                message += f"📊 *Resumo:*\n"
                message += f"• Total: {total} vagas\n"
                message += f"• Pontuação média: {avg_score:.1f}%\n"
                message += f"• Recomendadas: {should_apply}\n\n"
            
            # Top vagas
            message += "🏆 *Melhores Vagas:*\n"
            
            for i, job in enumerate(jobs[:5], 1):
                title = job.get("title", "N/A")[:40]
                company = job.get("company", "N/A")[:25]
                platform = job.get("platform", "N/A")
                
                analysis = job.get("analysis", {})
                score = analysis.get("compatibility_score", 0)
                
                message += f"{i}. *{title}*\n"
                message += f"   🏢 {company} | 📱 {platform}\n"
                message += f"   📈 Compatibilidade: {score:.0f}%\n\n"
            
            if len(jobs) > 5:
                message += f"... e mais {len(jobs) - 5} vagas\n\n"
            
            message += "⚡ Acesse o dashboard para mais detalhes!"
            
            return self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar alerta de vagas: {e}")
            return False
    
    def send_application_update(self, job_title: str, company: str, status: str) -> bool:
        """Envia atualização sobre aplicação."""
        try:
            status_icons = {
                "applied": "✅",
                "rejected": "❌", 
                "interview": "📞",
                "hired": "🎉"
            }
            
            icon = status_icons.get(status, "ℹ️")
            
            message = f"{icon} *Atualização de Aplicação*\n\n"
            message += f"📋 *Vaga:* {job_title}\n"
            message += f"🏢 *Empresa:* {company}\n"
            message += f"📊 *Status:* {status.title()}\n\n"
            
            if status == "applied":
                message += "Aplicação realizada com sucesso!"
            elif status == "rejected":
                message += "Não foi dessa vez, mas continue tentando!"
            elif status == "interview":
                message += "Parabéns! Você foi chamado para entrevista!"
            elif status == "hired":
                message += "🎉 PARABÉNS! Você foi contratado!"
            
            return self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar atualização de aplicação: {e}")
            return False
    
    def send_error_alert(self, error_type: str, error_message: str, module: str = None) -> bool:
        """Envia alerta de erro."""
        try:
            message = "🚨 *Alerta de Erro*\n\n"
            message += f"⚠️ *Tipo:* {error_type}\n"
            
            if module:
                message += f"📦 *Módulo:* {module}\n"
            
            message += f"💬 *Mensagem:* {error_message[:200]}\n"
            message += f"🕐 *Horário:* {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
            message += "Verifique os logs para mais detalhes."
            
            return self.send_message(message, disable_notification=True)
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar alerta de erro: {e}")
            return False
    
    def send_daily_summary(self, summary_data: Dict) -> bool:
        """Envia resumo diário."""
        try:
            message = "📊 *Resumo Diário*\n\n"
            
            # Estatísticas de scraping
            if "scraping" in summary_data:
                scraping = summary_data["scraping"]
                message += f"🔍 *Scraping:*\n"
                message += f"• Vagas encontradas: {scraping.get('total_jobs', 0)}\n"
                message += f"• Novas vagas: {scraping.get('new_jobs', 0)}\n"
                message += f"• Plataformas: {scraping.get('platforms_count', 0)}\n\n"
            
            # Estatísticas de aplicações
            if "applications" in summary_data:
                apps = summary_data["applications"]
                message += f"📝 *Aplicações:*\n"
                message += f"• Aplicações enviadas: {apps.get('sent', 0)}\n"
                message += f"• Respostas recebidas: {apps.get('responses', 0)}\n"
                message += f"• Taxa de sucesso: {apps.get('success_rate', 0):.1f}%\n\n"
            
            # Análises de IA
            if "analysis" in summary_data:
                analysis = summary_data["analysis"]
                message += f"🤖 *Análises de IA:*\n"
                message += f"• Vagas analisadas: {analysis.get('analyzed', 0)}\n"
                message += f"• Pontuação média: {analysis.get('avg_score', 0):.1f}%\n"
                message += f"• Recomendadas: {analysis.get('recommended', 0)}\n\n"
            
            message += f"📅 Data: {datetime.now().strftime('%d/%m/%Y')}"
            
            return self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar resumo diário: {e}")
            return False
    
    def send_questionnaire_alert(self, job_title: str, company: str, 
                               complex_questions_count: int) -> bool:
        """Envia alerta sobre questionário que precisa de atenção."""
        try:
            message = "❓ *Questionário Requer Atenção*\n\n"
            message += f"📋 *Vaga:* {job_title}\n"
            message += f"🏢 *Empresa:* {company}\n"
            message += f"❓ *Questões complexas:* {complex_questions_count}\n\n"
            message += "Algumas questões precisam de resposta manual. "
            message += "Acesse o dashboard para responder."
            
            return self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar alerta de questionário: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Testa conexão com Telegram."""
        try:
            if not self.bot_token:
                return False
            
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get("ok"):
                    self.logger.info(f"Bot conectado: {bot_info['result']['first_name']}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro no teste de conexão Telegram: {e}")
            return False

