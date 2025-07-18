"""
Notificador via email.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List, Dict
from datetime import datetime
import os

from backend.config.settings import settings
from backend.config.logging_config import get_logger


class EmailNotifier:
    """Notificador via email."""
    
    def __init__(self):
        self.logger = get_logger("notifications.email")
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME or settings.EMAIL_ADDRESS
        self.password = settings.SMTP_PASSWORD or settings.EMAIL_PASSWORD
        self.from_email = settings.EMAIL_ADDRESS
        self.use_tls = getattr(settings, 'SMTP_USE_TLS', True)
        
        if not all([self.smtp_server, self.username, self.password, self.from_email]):
            self.logger.warning("Configurações de email incompletas")
    
    def send_email(self, to_email: str, subject: str, body: str, 
                  html_body: str = None, attachments: List[str] = None) -> bool:
        """Envia email."""
        try:
            if not all([self.username, self.password, self.from_email]):
                self.logger.error("Email não configurado")
                return False
            
            # Criar mensagem
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Adicionar corpo do email
            if body:
                text_part = MIMEText(body, 'plain', 'utf-8')
                msg.attach(text_part)
            
            if html_body:
                html_part = MIMEText(html_body, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Adicionar anexos
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {os.path.basename(file_path)}'
                            )
                            msg.attach(part)
            
            # Enviar email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            self.logger.info(f"Email enviado com sucesso para {to_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar email: {e}")
            return False
    
    def send_job_alert_email(self, to_email: str, jobs: List[Dict], 
                           analysis_summary: Dict = None) -> bool:
        """Envia alerta de vagas por email."""
        try:
            subject = f"🎯 {len(jobs)} Novas Vagas Encontradas!"
            
            # Corpo em texto
            body = f"Olá!\n\nEncontramos {len(jobs)} novas vagas que podem interessar você:\n\n"
            
            # Corpo em HTML
            html_body = f"""
            <html>
            <body>
                <h2>🎯 Novas Vagas Encontradas!</h2>
                <p>Olá!</p>
                <p>Encontramos <strong>{len(jobs)}</strong> novas vagas que podem interessar você:</p>
            """
            
            # Resumo
            if analysis_summary:
                total = analysis_summary.get("total_jobs", len(jobs))
                avg_score = analysis_summary.get("average_score", 0)
                should_apply = analysis_summary.get("recommendations", {}).get("should_apply", 0)
                
                body += f"Resumo:\n"
                body += f"- Total de vagas: {total}\n"
                body += f"- Pontuação média: {avg_score:.1f}%\n"
                body += f"- Recomendadas para aplicação: {should_apply}\n\n"
                
                html_body += f"""
                <div style="background-color: #f0f0f0; padding: 15px; margin: 10px 0; border-radius: 5px;">
                    <h3>📊 Resumo</h3>
                    <ul>
                        <li>Total de vagas: {total}</li>
                        <li>Pontuação média: {avg_score:.1f}%</li>
                        <li>Recomendadas para aplicação: {should_apply}</li>
                    </ul>
                </div>
                """
            
            # Lista de vagas
            body += "Melhores vagas:\n\n"
            html_body += "<h3>🏆 Melhores Vagas</h3><div>"
            
            for i, job in enumerate(jobs[:10], 1):
                title = job.get("title", "N/A")
                company = job.get("company", "N/A")
                platform = job.get("platform", "N/A")
                url = job.get("url", "")
                
                analysis = job.get("analysis", {})
                score = analysis.get("compatibility_score", 0)
                
                # Texto
                body += f"{i}. {title}\n"
                body += f"   Empresa: {company}\n"
                body += f"   Plataforma: {platform}\n"
                body += f"   Compatibilidade: {score:.0f}%\n"
                if url:
                    body += f"   Link: {url}\n"
                body += "\n"
                
                # HTML
                score_color = "#28a745" if score >= 80 else "#ffc107" if score >= 60 else "#dc3545"
                html_body += f"""
                <div style="border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px;">
                    <h4 style="margin: 0 0 10px 0; color: #333;">{i}. {title}</h4>
                    <p style="margin: 5px 0;"><strong>Empresa:</strong> {company}</p>
                    <p style="margin: 5px 0;"><strong>Plataforma:</strong> {platform}</p>
                    <p style="margin: 5px 0;">
                        <strong>Compatibilidade:</strong> 
                        <span style="color: {score_color}; font-weight: bold;">{score:.0f}%</span>
                    </p>
                """
                
                if url:
                    html_body += f'<p style="margin: 5px 0;"><a href="{url}" target="_blank">Ver Vaga</a></p>'
                
                html_body += "</div>"
            
            if len(jobs) > 10:
                body += f"... e mais {len(jobs) - 10} vagas disponíveis no dashboard.\n\n"
                html_body += f"<p><em>... e mais {len(jobs) - 10} vagas disponíveis no dashboard.</em></p>"
            
            body += "Acesse o dashboard para mais detalhes e para aplicar nas vagas!\n\n"
            body += f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
            
            html_body += """
                </div>
                <p>Acesse o dashboard para mais detalhes e para aplicar nas vagas!</p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    Sistema de Automação de Vagas - """ + datetime.now().strftime('%d/%m/%Y %H:%M:%S') + """
                </p>
            </body>
            </html>
            """
            
            return self.send_email(to_email, subject, body, html_body)
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar alerta de vagas por email: {e}")
            return False
    
    def send_application_materials_email(self, to_email: str, job_title: str, 
                                       company: str, resume_path: str = None, 
                                       cover_letter_path: str = None) -> bool:
        """Envia materiais de aplicação por email."""
        try:
            subject = f"📄 Materiais para {job_title} - {company}"
            
            body = f"""Olá!

Aqui estão os materiais personalizados para a vaga:

Vaga: {job_title}
Empresa: {company}
Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

Os arquivos estão anexados a este email.

Boa sorte na aplicação!
"""
            
            html_body = f"""
            <html>
            <body>
                <h2>📄 Materiais de Aplicação</h2>
                <p>Olá!</p>
                <p>Aqui estão os materiais personalizados para a vaga:</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px;">
                    <p><strong>Vaga:</strong> {job_title}</p>
                    <p><strong>Empresa:</strong> {company}</p>
                    <p><strong>Data:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                </div>
                
                <p>Os arquivos estão anexados a este email.</p>
                <p><strong>Boa sorte na aplicação!</strong></p>
                
                <hr>
                <p style="color: #666; font-size: 12px;">
                    Sistema de Automação de Vagas
                </p>
            </body>
            </html>
            """
            
            attachments = []
            if resume_path and os.path.exists(resume_path):
                attachments.append(resume_path)
            if cover_letter_path and os.path.exists(cover_letter_path):
                attachments.append(cover_letter_path)
            
            return self.send_email(to_email, subject, body, html_body, attachments)
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar materiais por email: {e}")
            return False
    
    def send_daily_summary_email(self, to_email: str, summary_data: Dict) -> bool:
        """Envia resumo diário por email."""
        try:
            date_str = datetime.now().strftime('%d/%m/%Y')
            subject = f"📊 Resumo Diário - {date_str}"
            
            body = f"Resumo Diário - {date_str}\n\n"
            
            html_body = f"""
            <html>
            <body>
                <h2>📊 Resumo Diário - {date_str}</h2>
            """
            
            # Estatísticas de scraping
            if "scraping" in summary_data:
                scraping = summary_data["scraping"]
                body += f"Scraping:\n"
                body += f"- Vagas encontradas: {scraping.get('total_jobs', 0)}\n"
                body += f"- Novas vagas: {scraping.get('new_jobs', 0)}\n"
                body += f"- Plataformas: {scraping.get('platforms_count', 0)}\n\n"
                
                html_body += f"""
                <div style="background-color: #e3f2fd; padding: 15px; margin: 10px 0; border-radius: 5px;">
                    <h3>🔍 Scraping</h3>
                    <ul>
                        <li>Vagas encontradas: {scraping.get('total_jobs', 0)}</li>
                        <li>Novas vagas: {scraping.get('new_jobs', 0)}</li>
                        <li>Plataformas: {scraping.get('platforms_count', 0)}</li>
                    </ul>
                </div>
                """
            
            # Estatísticas de aplicações
            if "applications" in summary_data:
                apps = summary_data["applications"]
                body += f"Aplicações:\n"
                body += f"- Aplicações enviadas: {apps.get('sent', 0)}\n"
                body += f"- Respostas recebidas: {apps.get('responses', 0)}\n"
                body += f"- Taxa de sucesso: {apps.get('success_rate', 0):.1f}%\n\n"
                
                html_body += f"""
                <div style="background-color: #f3e5f5; padding: 15px; margin: 10px 0; border-radius: 5px;">
                    <h3>📝 Aplicações</h3>
                    <ul>
                        <li>Aplicações enviadas: {apps.get('sent', 0)}</li>
                        <li>Respostas recebidas: {apps.get('responses', 0)}</li>
                        <li>Taxa de sucesso: {apps.get('success_rate', 0):.1f}%</li>
                    </ul>
                </div>
                """
            
            # Análises de IA
            if "analysis" in summary_data:
                analysis = summary_data["analysis"]
                body += f"Análises de IA:\n"
                body += f"- Vagas analisadas: {analysis.get('analyzed', 0)}\n"
                body += f"- Pontuação média: {analysis.get('avg_score', 0):.1f}%\n"
                body += f"- Recomendadas: {analysis.get('recommended', 0)}\n\n"
                
                html_body += f"""
                <div style="background-color: #e8f5e8; padding: 15px; margin: 10px 0; border-radius: 5px;">
                    <h3>🤖 Análises de IA</h3>
                    <ul>
                        <li>Vagas analisadas: {analysis.get('analyzed', 0)}</li>
                        <li>Pontuação média: {analysis.get('avg_score', 0):.1f}%</li>
                        <li>Recomendadas: {analysis.get('recommended', 0)}</li>
                    </ul>
                </div>
                """
            
            html_body += """
                <hr>
                <p style="color: #666; font-size: 12px;">
                    Sistema de Automação de Vagas
                </p>
            </body>
            </html>
            """
            
            return self.send_email(to_email, subject, body, html_body)
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar resumo diário por email: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Testa conexão SMTP."""
        try:
            if not all([self.username, self.password]):
                return False
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
            
            self.logger.info("Conexão SMTP testada com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro no teste de conexão SMTP: {e}")
            return False

