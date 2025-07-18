"""
Gerenciador central para todos os módulos de IA.
"""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from .job_analyzer import JobAnalyzer
from .resume_generator import ResumeGenerator
from .cover_letter_generator import CoverLetterGenerator
from .questionnaire_responder import QuestionnaireResponder
from backend.config.settings import settings
from backend.config.logging_config import get_logger


class AIManager:
    """Gerenciador central para coordenar todos os módulos de IA."""
    
    def __init__(self):
        self.logger = get_logger("ai.manager")
        
        # Inicializar módulos de IA
        self.job_analyzer = JobAnalyzer()
        self.resume_generator = ResumeGenerator()
        self.cover_letter_generator = CoverLetterGenerator()
        self.questionnaire_responder = QuestionnaireResponder()
        
        self.logger.info("AIManager inicializado com todos os módulos")
    
    def analyze_jobs_batch(self, jobs: List[Dict], max_workers: int = 3) -> List[Dict]:
        """Analisa múltiplas vagas em paralelo."""
        try:
            self.logger.info(f"Iniciando análise de {len(jobs)} vagas")
            
            analyzed_jobs = []
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_job = {
                    executor.submit(self.job_analyzer.process, job): job
                    for job in jobs
                }
                
                for future in as_completed(future_to_job):
                    job = future_to_job[future]
                    try:
                        analysis = future.result()
                        job_with_analysis = {**job, "analysis": analysis}
                        analyzed_jobs.append(job_with_analysis)
                    except Exception as e:
                        self.logger.warning(f"Erro na análise da vaga {job.get('title', 'N/A')}: {e}")
                        job_with_analysis = {**job, "analysis": {"error": str(e)}}
                        analyzed_jobs.append(job_with_analysis)
            
            # Ordenar por pontuação de compatibilidade
            analyzed_jobs.sort(
                key=lambda x: x.get("analysis", {}).get("compatibility_score", 0),
                reverse=True
            )
            
            self.logger.info(f"Análise concluída para {len(analyzed_jobs)} vagas")
            return analyzed_jobs
            
        except Exception as e:
            self.logger.error(f"Erro na análise em lote: {e}")
            return jobs
    
    def generate_application_materials(self, jobs_with_analysis: List[Dict], 
                                     max_workers: int = 2) -> Dict[str, List[Dict]]:
        """Gera currículos e cartas para múltiplas vagas."""
        try:
            self.logger.info(f"Gerando materiais para {len(jobs_with_analysis)} vagas")
            
            # Filtrar apenas vagas com boa compatibilidade
            good_jobs = [
                job for job in jobs_with_analysis
                if job.get("analysis", {}).get("compatibility_score", 0) >= 60
            ]
            
            if not good_jobs:
                self.logger.warning("Nenhuma vaga com compatibilidade >= 60%")
                return {"resumes": [], "cover_letters": []}
            
            self.logger.info(f"Gerando materiais para {len(good_jobs)} vagas compatíveis")
            
            # Gerar currículos
            resumes = self._generate_resumes_parallel(good_jobs, max_workers)
            
            # Gerar cartas de apresentação
            cover_letters = self._generate_cover_letters_parallel(good_jobs, resumes, max_workers)
            
            return {
                "resumes": resumes,
                "cover_letters": cover_letters,
                "total_generated": len(resumes)
            }
            
        except Exception as e:
            self.logger.error(f"Erro na geração de materiais: {e}")
            return {"resumes": [], "cover_letters": []}
    
    def _generate_resumes_parallel(self, jobs: List[Dict], max_workers: int) -> List[Dict]:
        """Gera currículos em paralelo."""
        try:
            resumes = []
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_job = {
                    executor.submit(self._generate_single_resume, job): job
                    for job in jobs
                }
                
                for future in as_completed(future_to_job):
                    job = future_to_job[future]
                    try:
                        resume = future.result()
                        resumes.append(resume)
                    except Exception as e:
                        self.logger.warning(f"Erro na geração de currículo para {job.get('title', 'N/A')}: {e}")
            
            return resumes
            
        except Exception as e:
            self.logger.error(f"Erro na geração paralela de currículos: {e}")
            return []
    
    def _generate_cover_letters_parallel(self, jobs: List[Dict], resumes: List[Dict], 
                                       max_workers: int) -> List[Dict]:
        """Gera cartas de apresentação em paralelo."""
        try:
            cover_letters = []
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                
                for i, job in enumerate(jobs):
                    resume_data = resumes[i] if i < len(resumes) else None
                    future = executor.submit(self._generate_single_cover_letter, job, resume_data)
                    futures.append((future, job))
                
                for future, job in futures:
                    try:
                        cover_letter = future.result()
                        cover_letters.append(cover_letter)
                    except Exception as e:
                        self.logger.warning(f"Erro na geração de carta para {job.get('title', 'N/A')}: {e}")
            
            return cover_letters
            
        except Exception as e:
            self.logger.error(f"Erro na geração paralela de cartas: {e}")
            return []
    
    def _generate_single_resume(self, job_with_analysis: Dict) -> Dict:
        """Gera currículo para uma vaga específica."""
        try:
            analysis = job_with_analysis.get("analysis", {})
            resume = self.resume_generator.process(job_with_analysis, analysis)
            
            return {
                "job_id": job_with_analysis.get("id"),
                "job_title": job_with_analysis.get("title"),
                "job_company": job_with_analysis.get("company"),
                "compatibility_score": analysis.get("compatibility_score", 0),
                "resume": resume
            }
            
        except Exception as e:
            self.logger.error(f"Erro na geração de currículo individual: {e}")
            return {"error": str(e)}
    
    def _generate_single_cover_letter(self, job_with_analysis: Dict, resume_data: Dict = None) -> Dict:
        """Gera carta de apresentação para uma vaga específica."""
        try:
            analysis = job_with_analysis.get("analysis", {})
            cover_letter = self.cover_letter_generator.process(
                job_with_analysis, analysis, resume_data
            )
            
            return {
                "job_id": job_with_analysis.get("id"),
                "job_title": job_with_analysis.get("title"),
                "job_company": job_with_analysis.get("company"),
                "compatibility_score": analysis.get("compatibility_score", 0),
                "cover_letter": cover_letter
            }
            
        except Exception as e:
            self.logger.error(f"Erro na geração de carta individual: {e}")
            return {"error": str(e)}
    
    def process_questionnaire(self, questions: List[Dict], job_data: Dict = None, 
                            job_analysis: Dict = None) -> Dict:
        """Processa questionário de uma vaga."""
        try:
            self.logger.info(f"Processando questionário com {len(questions)} questões")
            
            result = self.questionnaire_responder.process(questions, job_data, job_analysis)
            
            # Log estatísticas
            total = result.get("total_questions", 0)
            auto_answered = result.get("auto_answered", 0)
            needs_review = result.get("needs_review", 0)
            
            self.logger.info(f"Questionário processado: {auto_answered}/{total} respondidas automaticamente, {needs_review} precisam revisão")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro no processamento de questionário: {e}")
            return {"error": str(e)}
    
    def get_top_jobs(self, analyzed_jobs: List[Dict], limit: int = 10) -> List[Dict]:
        """Retorna as melhores vagas baseado na análise."""
        try:
            # Filtrar vagas com análise válida
            valid_jobs = [
                job for job in analyzed_jobs
                if job.get("analysis", {}).get("compatibility_score", 0) > 0
            ]
            
            # Ordenar por pontuação
            sorted_jobs = sorted(
                valid_jobs,
                key=lambda x: x.get("analysis", {}).get("compatibility_score", 0),
                reverse=True
            )
            
            return sorted_jobs[:limit]
            
        except Exception as e:
            self.logger.error(f"Erro ao obter top vagas: {e}")
            return analyzed_jobs[:limit]
    
    def create_analysis_summary(self, analyzed_jobs: List[Dict]) -> Dict:
        """Cria resumo da análise de vagas."""
        try:
            total_jobs = len(analyzed_jobs)
            
            # Estatísticas de compatibilidade
            scores = [
                job.get("analysis", {}).get("compatibility_score", 0)
                for job in analyzed_jobs
            ]
            
            high_compatibility = len([s for s in scores if s >= 80])
            medium_compatibility = len([s for s in scores if 60 <= s < 80])
            low_compatibility = len([s for s in scores if 40 <= s < 60])
            very_low_compatibility = len([s for s in scores if s < 40])
            
            # Tipos de vaga
            job_types = {}
            for job in analyzed_jobs:
                job_type = job.get("analysis", {}).get("job_type", "unknown")
                job_types[job_type] = job_types.get(job_type, 0) + 1
            
            # Plataformas
            platforms = {}
            for job in analyzed_jobs:
                platform = job.get("platform", "unknown")
                platforms[platform] = platforms.get(platform, 0) + 1
            
            # Recomendações
            should_apply = len([
                job for job in analyzed_jobs
                if job.get("analysis", {}).get("recommendations", {}).get("should_apply", False)
            ])
            
            return {
                "total_jobs": total_jobs,
                "compatibility_distribution": {
                    "high (80-100%)": high_compatibility,
                    "medium (60-79%)": medium_compatibility,
                    "low (40-59%)": low_compatibility,
                    "very_low (0-39%)": very_low_compatibility
                },
                "job_types": job_types,
                "platforms": platforms,
                "recommendations": {
                    "should_apply": should_apply,
                    "should_not_apply": total_jobs - should_apply
                },
                "average_score": sum(scores) / len(scores) if scores else 0,
                "max_score": max(scores) if scores else 0,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro na criação do resumo: {e}")
            return {"error": str(e)}
    
    def create_telegram_summary(self, analysis_summary: Dict, top_jobs: List[Dict]) -> str:
        """Cria resumo para notificação no Telegram."""
        try:
            total = analysis_summary.get("total_jobs", 0)
            avg_score = analysis_summary.get("average_score", 0)
            should_apply = analysis_summary.get("recommendations", {}).get("should_apply", 0)
            
            message = f"🎯 *Análise de Vagas Concluída*\n\n"
            message += f"📊 *Estatísticas:*\n"
            message += f"• Total de vagas: {total}\n"
            message += f"• Pontuação média: {avg_score:.1f}%\n"
            message += f"• Recomendadas: {should_apply}\n\n"
            
            # Distribuição de compatibilidade
            dist = analysis_summary.get("compatibility_distribution", {})
            message += f"📈 *Compatibilidade:*\n"
            message += f"• Alta (80-100%): {dist.get('high (80-100%)', 0)}\n"
            message += f"• Média (60-79%): {dist.get('medium (60-79%)', 0)}\n"
            message += f"• Baixa (40-59%): {dist.get('low (40-59%)', 0)}\n\n"
            
            # Top 3 vagas
            if top_jobs:
                message += f"🏆 *Top 3 Vagas:*\n"
                for i, job in enumerate(top_jobs[:3], 1):
                    title = job.get("title", "N/A")[:30]
                    company = job.get("company", "N/A")[:20]
                    score = job.get("analysis", {}).get("compatibility_score", 0)
                    message += f"{i}. {title} - {company} ({score:.0f}%)\n"
            
            message += f"\n⚡ Acesse o dashboard para mais detalhes!"
            
            return message
            
        except Exception as e:
            self.logger.error(f"Erro na criação de resumo Telegram: {e}")
            return "Erro ao criar resumo da análise"
    
    def cleanup_resources(self):
        """Limpa recursos dos módulos de IA."""
        try:
            # Limpar caches dos modelos
            for module in [self.job_analyzer, self.resume_generator, 
                          self.cover_letter_generator, self.questionnaire_responder]:
                if hasattr(module, '_model_cache'):
                    module._model_cache.clear()
            
            self.logger.info("Recursos de IA limpos")
            
        except Exception as e:
            self.logger.warning(f"Erro na limpeza de recursos: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup_resources()

