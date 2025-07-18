"""
Analisador de compatibilidade entre vagas e perfil do usuário.
"""
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .base_ai import BaseAI
from backend.config.settings import settings


class JobAnalyzer(BaseAI):
    """Analisa compatibilidade entre vagas e perfil do usuário."""
    
    def __init__(self):
        super().__init__("job_analyzer")
        
        # Perfis de competências
        self.skill_profiles = {
            "dev": {
                "technical_skills": [
                    "python", "javascript", "typescript", "java", "go", "rust",
                    "react", "vue", "angular", "node.js", "django", "flask",
                    "sql", "postgresql", "mysql", "mongodb", "redis",
                    "docker", "kubernetes", "aws", "azure", "gcp",
                    "git", "linux", "api", "rest", "graphql",
                    "salesforce", "apex", "lightning", "soql"
                ],
                "soft_skills": [
                    "comunicação", "trabalho em equipe", "resolução de problemas",
                    "aprendizado rápido", "adaptabilidade", "criatividade"
                ],
                "experience_levels": ["júnior", "trainee", "estágio", "junior", "entry level", "pcd"]
            },
            "admin": {
                "technical_skills": [
                    "excel", "word", "powerpoint", "crm", "erp",
                    "atendimento ao cliente", "suporte técnico", "call center",
                    "chat", "email", "telefone", "helpdesk"
                ],
                "soft_skills": [
                    "comunicação", "paciência", "empatia", "organização",
                    "multitarefa", "resolução de conflitos", "proatividade"
                ],
                "experience_levels": ["júnior", "trainee", "estágio", "junior", "entry level", "pcd"]
            }
        }
    
    def process(self, job_data: Dict) -> Dict:
        """Processa análise completa de uma vaga."""
        try:
            # Extrair informações da vaga
            job_info = self._extract_job_info(job_data)
            
            # Determinar tipo de vaga
            job_type = self._classify_job_type(job_info)
            
            # Calcular pontuação de compatibilidade
            compatibility_score = self._calculate_compatibility(job_info, job_type)
            
            # Analisar requisitos
            requirements_analysis = self._analyze_requirements(job_info)
            
            # Extrair informações importantes
            key_info = self._extract_key_information(job_info)
            
            # Gerar recomendações
            recommendations = self._generate_recommendations(job_info, job_type, compatibility_score)
            
            return {
                "job_type": job_type,
                "compatibility_score": compatibility_score,
                "requirements_analysis": requirements_analysis,
                "key_information": key_info,
                "recommendations": recommendations,
                "language": self.detect_language(job_info.get("description", "")),
                "analyzed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro na análise da vaga: {e}")
            return {
                "job_type": "unknown",
                "compatibility_score": 0.0,
                "error": str(e)
            }
    
    def _extract_job_info(self, job_data: Dict) -> Dict:
        """Extrai e normaliza informações da vaga."""
        try:
            title = job_data.get("title", "").lower()
            description = job_data.get("description", "").lower()
            requirements = job_data.get("requirements", "").lower()
            company = job_data.get("company", "").lower()
            
            # Combinar todos os textos
            full_text = f"{title} {description} {requirements}".strip()
            
            return {
                "title": title,
                "description": description,
                "requirements": requirements,
                "company": company,
                "full_text": full_text,
                "original_data": job_data
            }
            
        except Exception as e:
            self.logger.warning(f"Erro ao extrair informações da vaga: {e}")
            return {"full_text": "", "original_data": job_data}
    
    def _classify_job_type(self, job_info: Dict) -> str:
        """Classifica o tipo de vaga (dev ou admin)."""
        try:
            text = job_info.get("full_text", "")
            
            # Pontuação para cada tipo
            dev_score = 0
            admin_score = 0
            
            # Verificar palavras-chave de desenvolvimento
            dev_keywords = self.skill_profiles["dev"]["technical_skills"]
            for keyword in dev_keywords:
                if keyword in text:
                    dev_score += 1
            
            # Verificar palavras-chave de atendimento/admin
            admin_keywords = self.skill_profiles["admin"]["technical_skills"]
            for keyword in admin_keywords:
                if keyword in text:
                    admin_score += 1
            
            # Palavras-chave específicas com peso maior
            high_weight_dev = ["desenvolvedor", "developer", "programador", "programmer", "software engineer"]
            high_weight_admin = ["atendimento", "customer service", "call center", "suporte", "support", "assistente"]
            
            for keyword in high_weight_dev:
                if keyword in text:
                    dev_score += 3
            
            for keyword in high_weight_admin:
                if keyword in text:
                    admin_score += 3
            
            # Determinar tipo
            if dev_score > admin_score:
                return "dev"
            elif admin_score > dev_score:
                return "admin"
            else:
                # Em caso de empate, usar título para desempate
                title = job_info.get("title", "")
                if any(word in title for word in high_weight_dev):
                    return "dev"
                elif any(word in title for word in high_weight_admin):
                    return "admin"
                else:
                    return "dev"  # Padrão
                    
        except Exception as e:
            self.logger.warning(f"Erro na classificação do tipo de vaga: {e}")
            return "dev"
    
    def _calculate_compatibility(self, job_info: Dict, job_type: str) -> float:
        """Calcula pontuação de compatibilidade (0-100)."""
        try:
            text = job_info.get("full_text", "")
            profile = self.skill_profiles.get(job_type, self.skill_profiles["dev"])
            
            total_score = 0
            max_score = 0
            
            # Verificar competências técnicas (peso 40%)
            technical_matches = 0
            for skill in profile["technical_skills"]:
                max_score += 4
                if skill in text:
                    technical_matches += 1
                    total_score += 4
            
            # Verificar competências comportamentais (peso 20%)
            soft_matches = 0
            for skill in profile["soft_skills"]:
                max_score += 2
                if skill in text:
                    soft_matches += 1
                    total_score += 2
            
            # Verificar nível de experiência (peso 30%)
            experience_match = False
            for level in profile["experience_levels"]:
                max_score += 3
                if level in text:
                    experience_match = True
                    total_score += 3
                    break
            
            # Verificar se é remoto (peso 10%)
            remote_keywords = ["remoto", "remote", "home office", "homeoffice"]
            max_score += 1
            if any(keyword in text for keyword in remote_keywords):
                total_score += 1
            
            # Calcular pontuação final
            if max_score > 0:
                compatibility = (total_score / max_score) * 100
            else:
                compatibility = 0
            
            # Ajustar pontuação baseado em fatores adicionais
            compatibility = self._adjust_compatibility_score(compatibility, job_info, job_type)
            
            return min(100, max(0, compatibility))
            
        except Exception as e:
            self.logger.warning(f"Erro no cálculo de compatibilidade: {e}")
            return 0.0
    
    def _adjust_compatibility_score(self, base_score: float, job_info: Dict, job_type: str) -> float:
        """Ajusta pontuação baseado em fatores adicionais."""
        try:
            text = job_info.get("full_text", "")
            adjusted_score = base_score
            
            # Penalizar vagas com requisitos muito altos
            senior_keywords = ["sênior", "senior", "pleno", "especialista", "expert", "lead"]
            if any(keyword in text for keyword in senior_keywords):
                adjusted_score *= 0.7
            
            # Bonificar vagas PCD
            pcd_keywords = ["pcd", "pessoa com deficiência", "inclusão", "diversidade"]
            if any(keyword in text for keyword in pcd_keywords):
                adjusted_score *= 1.2
            
            # Penalizar empresas da lista negra
            company = job_info.get("company", "")
            for blacklisted in settings.BLACKLIST_COMPANIES:
                if blacklisted.lower() in company:
                    adjusted_score *= 0.3
                    break
            
            # Penalizar palavras-chave da lista negra
            for blacklisted in settings.BLACKLIST_KEYWORDS:
                if blacklisted.lower() in text:
                    adjusted_score *= 0.2
                    break
            
            return adjusted_score
            
        except Exception as e:
            self.logger.warning(f"Erro no ajuste de pontuação: {e}")
            return base_score
    
    def _analyze_requirements(self, job_info: Dict) -> Dict:
        """Analisa requisitos específicos da vaga."""
        try:
            text = job_info.get("full_text", "")
            
            # Extrair requisitos obrigatórios vs desejáveis
            mandatory_patterns = [
                r"obrigatório[:\s]*([^.!?\n]+)",
                r"requisitos[:\s]*([^.!?\n]+)",
                r"necessário[:\s]*([^.!?\n]+)",
                r"required[:\s]*([^.!?\n]+)",
                r"must have[:\s]*([^.!?\n]+)"
            ]
            
            desired_patterns = [
                r"desejável[:\s]*([^.!?\n]+)",
                r"diferencial[:\s]*([^.!?\n]+)",
                r"plus[:\s]*([^.!?\n]+)",
                r"nice to have[:\s]*([^.!?\n]+)",
                r"preferred[:\s]*([^.!?\n]+)"
            ]
            
            mandatory_requirements = []
            desired_requirements = []
            
            for pattern in mandatory_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                mandatory_requirements.extend(matches)
            
            for pattern in desired_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                desired_requirements.extend(matches)
            
            # Extrair experiência necessária
            experience_patterns = [
                r"(\d+)\s*anos?\s*de\s*experiência",
                r"(\d+)\s*years?\s*of\s*experience",
                r"experiência\s*de\s*(\d+)\s*anos?",
                r"experience\s*of\s*(\d+)\s*years?"
            ]
            
            experience_years = []
            for pattern in experience_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                experience_years.extend([int(match) for match in matches])
            
            # Extrair tecnologias mencionadas
            technologies = self.extract_keywords(text, max_keywords=15)
            
            return {
                "mandatory_requirements": mandatory_requirements[:5],  # Limitar
                "desired_requirements": desired_requirements[:5],
                "experience_years": experience_years,
                "technologies": technologies,
                "has_clear_requirements": len(mandatory_requirements) > 0
            }
            
        except Exception as e:
            self.logger.warning(f"Erro na análise de requisitos: {e}")
            return {}
    
    def _extract_key_information(self, job_info: Dict) -> Dict:
        """Extrai informações-chave da vaga."""
        try:
            text = job_info.get("full_text", "")
            original_data = job_info.get("original_data", {})
            
            # Extrair salário
            salary_patterns = [
                r"r\$\s*(\d+(?:\.\d{3})*(?:,\d{2})?)",
                r"salário[:\s]*r\$\s*(\d+(?:\.\d{3})*(?:,\d{2})?)",
                r"(\d+(?:\.\d{3})*(?:,\d{2})?)\s*reais",
                r"\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)",
                r"usd\s*(\d+(?:,\d{3})*(?:\.\d{2})?)"
            ]
            
            salary_info = []
            for pattern in salary_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                salary_info.extend(matches)
            
            # Extrair benefícios
            benefits_keywords = [
                "vale refeição", "vale alimentação", "plano de saúde", "plano odontológico",
                "gympass", "home office", "flexibilidade", "férias", "13º salário",
                "participação nos lucros", "ppr", "seguro de vida", "day off"
            ]
            
            benefits = []
            for benefit in benefits_keywords:
                if benefit in text:
                    benefits.append(benefit)
            
            # Extrair modalidade de trabalho
            work_mode = "remoto"  # Padrão (já filtrado)
            if "híbrido" in text or "hybrid" in text:
                work_mode = "híbrido"
            elif "presencial" in text or "on-site" in text:
                work_mode = "presencial"
            
            # Extrair horário
            schedule_patterns = [
                r"(\d{1,2}h?\s*às?\s*\d{1,2}h?)",
                r"(\d{1,2}:\d{2}\s*às?\s*\d{1,2}:\d{2})",
                r"carga\s*horária[:\s]*(\d+h?)",
                r"(\d+)\s*horas?\s*semanais?"
            ]
            
            schedule_info = []
            for pattern in schedule_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                schedule_info.extend(matches)
            
            return {
                "salary_info": salary_info[:3],  # Limitar
                "benefits": benefits[:10],
                "work_mode": work_mode,
                "schedule_info": schedule_info[:3],
                "company": original_data.get("company", "N/A"),
                "location": original_data.get("location", "Remoto"),
                "platform": original_data.get("platform", "unknown")
            }
            
        except Exception as e:
            self.logger.warning(f"Erro na extração de informações-chave: {e}")
            return {}
    
    def _generate_recommendations(self, job_info: Dict, job_type: str, compatibility_score: float) -> Dict:
        """Gera recomendações baseadas na análise."""
        try:
            recommendations = {
                "should_apply": compatibility_score >= 60,
                "priority": self._calculate_priority(compatibility_score),
                "action_items": [],
                "concerns": [],
                "strengths": []
            }
            
            # Recomendações baseadas na pontuação
            if compatibility_score >= 80:
                recommendations["action_items"].append("Aplicar imediatamente - alta compatibilidade")
                recommendations["strengths"].append("Perfil muito alinhado com a vaga")
            elif compatibility_score >= 60:
                recommendations["action_items"].append("Aplicar - boa compatibilidade")
                recommendations["strengths"].append("Perfil adequado para a vaga")
            elif compatibility_score >= 40:
                recommendations["action_items"].append("Considerar aplicar após melhorar currículo")
                recommendations["concerns"].append("Compatibilidade moderada")
            else:
                recommendations["action_items"].append("Não recomendado - baixa compatibilidade")
                recommendations["concerns"].append("Perfil não alinhado com requisitos")
            
            # Análise específica do tipo de vaga
            text = job_info.get("full_text", "")
            profile = self.skill_profiles.get(job_type, self.skill_profiles["dev"])
            
            # Verificar competências em falta
            missing_skills = []
            for skill in profile["technical_skills"][:10]:  # Top 10 skills
                if skill not in text:
                    missing_skills.append(skill)
            
            if missing_skills:
                recommendations["action_items"].append(f"Destacar experiência em: {', '.join(missing_skills[:3])}")
            
            # Verificar nível de experiência
            experience_levels = profile["experience_levels"]
            has_junior_level = any(level in text for level in experience_levels)
            
            if not has_junior_level:
                recommendations["concerns"].append("Vaga pode exigir mais experiência")
            else:
                recommendations["strengths"].append("Nível de experiência adequado")
            
            return recommendations
            
        except Exception as e:
            self.logger.warning(f"Erro na geração de recomendações: {e}")
            return {"should_apply": False, "priority": "low"}
    
    def _calculate_priority(self, compatibility_score: float) -> str:
        """Calcula prioridade da vaga."""
        if compatibility_score >= 80:
            return "high"
        elif compatibility_score >= 60:
            return "medium"
        elif compatibility_score >= 40:
            return "low"
        else:
            return "very_low"
    
    def analyze_multiple_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Analisa múltiplas vagas e retorna ordenadas por compatibilidade."""
        try:
            analyzed_jobs = []
            
            for job in jobs:
                analysis = self.process(job)
                job_with_analysis = {**job, "analysis": analysis}
                analyzed_jobs.append(job_with_analysis)
            
            # Ordenar por pontuação de compatibilidade
            analyzed_jobs.sort(
                key=lambda x: x.get("analysis", {}).get("compatibility_score", 0),
                reverse=True
            )
            
            self.logger.info(f"Analisadas {len(analyzed_jobs)} vagas")
            return analyzed_jobs
            
        except Exception as e:
            self.logger.error(f"Erro na análise múltipla: {e}")
            return jobs

