"""
Gerador de currículos personalizados baseado em análise de vagas.
"""
import json
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from .base_ai import BaseAI
from backend.config.settings import settings


class ResumeGenerator(BaseAI):
    """Gera currículos personalizados para vagas específicas."""
    
    def __init__(self):
        super().__init__("resume_generator")
        
        # Templates de currículo base
        self.resume_templates = {
            "dev": {
                "pt": self._load_dev_template_pt(),
                "en": self._load_dev_template_en()
            },
            "admin": {
                "pt": self._load_admin_template_pt(),
                "en": self._load_admin_template_en()
            }
        }
    
    def process(self, job_data: Dict, job_analysis: Dict = None) -> Dict:
        """Gera currículo personalizado para uma vaga específica."""
        try:
            # Determinar tipo de vaga e idioma
            job_type = job_analysis.get("job_type", "dev") if job_analysis else "dev"
            language = job_analysis.get("language", "pt") if job_analysis else self.detect_language(
                job_data.get("description", "")
            )
            
            # Obter template base
            base_template = self.resume_templates.get(job_type, {}).get(language)
            if not base_template:
                # Fallback para template padrão
                base_template = self.resume_templates["dev"]["pt"]
            
            # Personalizar currículo
            personalized_resume = self._personalize_resume(base_template, job_data, job_analysis)
            
            # Gerar versões em diferentes formatos
            resume_formats = self._generate_formats(personalized_resume)
            
            return {
                "job_type": job_type,
                "language": language,
                "resume_data": personalized_resume,
                "formats": resume_formats,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro na geração do currículo: {e}")
            return {"error": str(e)}
    
    def _load_dev_template_pt(self) -> Dict:
        """Template de currículo para desenvolvedor em português."""
        return {
            "personal_info": {
                "name": settings.USER_FULL_NAME,
                "phone": settings.USER_PHONE,
                "email": settings.EMAIL_ADDRESS,
                "location": settings.USER_LOCATION,
                "linkedin": settings.USER_LINKEDIN_PROFILE
            },
            "objective": "Desenvolvedor {level} em busca de oportunidades para aplicar conhecimentos em {technologies} e contribuir para projetos inovadores em ambiente {work_mode}.",
            "skills": {
                "technical": [
                    "Python", "JavaScript", "TypeScript", "React", "Node.js",
                    "SQL", "PostgreSQL", "MongoDB", "Git", "Docker",
                    "API REST", "HTML/CSS", "Linux", "AWS"
                ],
                "soft": [
                    "Comunicação eficaz", "Trabalho em equipe", "Resolução de problemas",
                    "Aprendizado rápido", "Adaptabilidade", "Proatividade"
                ]
            },
            "experience": [
                {
                    "title": "Desenvolvedor {level}",
                    "company": "Projetos Pessoais e Freelances",
                    "period": "2023 - Presente",
                    "description": [
                        "Desenvolvimento de aplicações web utilizando {main_tech}",
                        "Implementação de APIs RESTful e integração com bancos de dados",
                        "Colaboração em projetos utilizando metodologias ágeis",
                        "Resolução de problemas complexos e otimização de performance"
                    ]
                }
            ],
            "education": [
                {
                    "degree": "Tecnólogo em Análise e Desenvolvimento de Sistemas",
                    "institution": "Instituição de Ensino",
                    "period": "2022 - 2024",
                    "status": "Em andamento"
                }
            ],
            "projects": [
                {
                    "name": "Sistema de Automação de Vagas",
                    "description": "Aplicação completa para automação de busca e aplicação em vagas de emprego",
                    "technologies": ["Python", "FastAPI", "PostgreSQL", "React", "Docker"]
                }
            ],
            "certifications": [
                "Certificação em {relevant_tech}",
                "Curso de {job_specific_skill}"
            ],
            "languages": [
                {"language": "Português", "level": "Nativo"},
                {"language": "Inglês", "level": "Intermediário"}
            ]
        }
    
    def _load_dev_template_en(self) -> Dict:
        """Template de currículo para desenvolvedor em inglês."""
        return {
            "personal_info": {
                "name": settings.USER_FULL_NAME,
                "phone": settings.USER_PHONE,
                "email": settings.EMAIL_ADDRESS,
                "location": settings.USER_LOCATION,
                "linkedin": settings.USER_LINKEDIN_PROFILE
            },
            "objective": "{level} Developer seeking opportunities to apply knowledge in {technologies} and contribute to innovative projects in {work_mode} environment.",
            "skills": {
                "technical": [
                    "Python", "JavaScript", "TypeScript", "React", "Node.js",
                    "SQL", "PostgreSQL", "MongoDB", "Git", "Docker",
                    "REST API", "HTML/CSS", "Linux", "AWS"
                ],
                "soft": [
                    "Effective communication", "Teamwork", "Problem solving",
                    "Fast learning", "Adaptability", "Proactivity"
                ]
            },
            "experience": [
                {
                    "title": "{level} Developer",
                    "company": "Personal Projects and Freelance",
                    "period": "2023 - Present",
                    "description": [
                        "Web application development using {main_tech}",
                        "RESTful API implementation and database integration",
                        "Collaboration on projects using agile methodologies",
                        "Complex problem solving and performance optimization"
                    ]
                }
            ],
            "education": [
                {
                    "degree": "Technology in Systems Analysis and Development",
                    "institution": "Educational Institution",
                    "period": "2022 - 2024",
                    "status": "In progress"
                }
            ],
            "projects": [
                {
                    "name": "Job Automation System",
                    "description": "Complete application for automating job search and application",
                    "technologies": ["Python", "FastAPI", "PostgreSQL", "React", "Docker"]
                }
            ],
            "certifications": [
                "Certification in {relevant_tech}",
                "Course in {job_specific_skill}"
            ],
            "languages": [
                {"language": "Portuguese", "level": "Native"},
                {"language": "English", "level": "Intermediate"}
            ]
        }
    
    def _load_admin_template_pt(self) -> Dict:
        """Template de currículo para atendimento/admin em português."""
        return {
            "personal_info": {
                "name": settings.USER_FULL_NAME,
                "phone": settings.USER_PHONE,
                "email": settings.EMAIL_ADDRESS,
                "location": settings.USER_LOCATION,
                "linkedin": settings.USER_LINKEDIN_PROFILE
            },
            "objective": "Profissional de atendimento {level} com foco em excelência no atendimento ao cliente e suporte técnico em ambiente {work_mode}.",
            "skills": {
                "technical": [
                    "Atendimento ao cliente", "Suporte técnico", "CRM",
                    "Excel avançado", "Chat online", "E-mail profissional",
                    "Telefonia", "Helpdesk", "Resolução de problemas"
                ],
                "soft": [
                    "Comunicação excelente", "Paciência", "Empatia",
                    "Organização", "Multitarefa", "Proatividade"
                ]
            },
            "experience": [
                {
                    "title": "Assistente de Atendimento {level}",
                    "company": "Experiência em Atendimento",
                    "period": "2023 - Presente",
                    "description": [
                        "Atendimento ao cliente via chat, e-mail e telefone",
                        "Resolução de dúvidas e problemas técnicos",
                        "Suporte em sistemas CRM e ferramentas internas",
                        "Manutenção de alto nível de satisfação do cliente"
                    ]
                }
            ],
            "education": [
                {
                    "degree": "Ensino Médio Completo",
                    "institution": "Instituição de Ensino",
                    "period": "2020 - 2022",
                    "status": "Concluído"
                }
            ],
            "certifications": [
                "Curso de Atendimento ao Cliente",
                "Certificação em {relevant_skill}"
            ],
            "languages": [
                {"language": "Português", "level": "Nativo"},
                {"language": "Inglês", "level": "Básico"}
            ]
        }
    
    def _load_admin_template_en(self) -> Dict:
        """Template de currículo para atendimento/admin em inglês."""
        return {
            "personal_info": {
                "name": settings.USER_FULL_NAME,
                "phone": settings.USER_PHONE,
                "email": settings.EMAIL_ADDRESS,
                "location": settings.USER_LOCATION,
                "linkedin": settings.USER_LINKEDIN_PROFILE
            },
            "objective": "{level} Customer service professional focused on excellence in customer support and technical assistance in {work_mode} environment.",
            "skills": {
                "technical": [
                    "Customer service", "Technical support", "CRM",
                    "Advanced Excel", "Online chat", "Professional email",
                    "Phone support", "Helpdesk", "Problem solving"
                ],
                "soft": [
                    "Excellent communication", "Patience", "Empathy",
                    "Organization", "Multitasking", "Proactivity"
                ]
            },
            "experience": [
                {
                    "title": "{level} Customer Service Assistant",
                    "company": "Customer Service Experience",
                    "period": "2023 - Present",
                    "description": [
                        "Customer service via chat, email and phone",
                        "Resolution of questions and technical problems",
                        "Support in CRM systems and internal tools",
                        "Maintaining high level of customer satisfaction"
                    ]
                }
            ],
            "education": [
                {
                    "degree": "High School Diploma",
                    "institution": "Educational Institution",
                    "period": "2020 - 2022",
                    "status": "Completed"
                }
            ],
            "certifications": [
                "Customer Service Course",
                "Certification in {relevant_skill}"
            ],
            "languages": [
                {"language": "Portuguese", "level": "Native"},
                {"language": "English", "level": "Basic"}
            ]
        }
    
    def _personalize_resume(self, template: Dict, job_data: Dict, job_analysis: Dict = None) -> Dict:
        """Personaliza template baseado na vaga específica."""
        try:
            personalized = json.loads(json.dumps(template))  # Deep copy
            
            # Extrair informações da vaga
            job_title = job_data.get("title", "")
            job_description = job_data.get("description", "")
            job_requirements = job_data.get("requirements", "")
            
            # Determinar nível (júnior, trainee, etc.)
            level = self._extract_level(job_title + " " + job_description)
            
            # Extrair tecnologias principais
            main_technologies = self._extract_main_technologies(job_description + " " + job_requirements)
            
            # Determinar modalidade de trabalho
            work_mode = "remoto"
            if "híbrido" in job_description.lower():
                work_mode = "híbrido"
            elif "presencial" in job_description.lower():
                work_mode = "presencial"
            
            # Personalizar objetivo
            if "{level}" in personalized.get("objective", ""):
                personalized["objective"] = personalized["objective"].format(
                    level=level,
                    technologies=", ".join(main_technologies[:3]),
                    work_mode=work_mode
                )
            
            # Reorganizar skills técnicas baseado na relevância
            if "skills" in personalized and "technical" in personalized["skills"]:
                personalized["skills"]["technical"] = self._reorder_skills(
                    personalized["skills"]["technical"],
                    job_description + " " + job_requirements
                )
            
            # Personalizar experiência
            if "experience" in personalized:
                for exp in personalized["experience"]:
                    if "{level}" in exp.get("title", ""):
                        exp["title"] = exp["title"].format(level=level)
                    if "{main_tech}" in str(exp.get("description", [])):
                        exp["description"] = [
                            desc.format(main_tech=main_technologies[0] if main_technologies else "tecnologias modernas")
                            for desc in exp["description"]
                        ]
            
            # Personalizar certificações
            if "certifications" in personalized:
                relevant_tech = main_technologies[0] if main_technologies else "tecnologia relevante"
                job_specific_skill = self._extract_job_specific_skill(job_description)
                
                personalized["certifications"] = [
                    cert.format(relevant_tech=relevant_tech, job_specific_skill=job_specific_skill)
                    for cert in personalized["certifications"]
                ]
            
            # Adicionar palavras-chave relevantes
            personalized = self._inject_keywords(personalized, job_description + " " + job_requirements)
            
            return personalized
            
        except Exception as e:
            self.logger.error(f"Erro na personalização do currículo: {e}")
            return template
    
    def _extract_level(self, text: str) -> str:
        """Extrai nível da vaga (júnior, trainee, etc.)."""
        text = text.lower()
        
        if any(word in text for word in ["trainee", "estagiário", "estágio"]):
            return "Trainee"
        elif any(word in text for word in ["júnior", "junior", "jr"]):
            return "Júnior"
        elif any(word in text for word in ["pleno", "mid-level"]):
            return "Pleno"
        elif any(word in text for word in ["sênior", "senior", "sr"]):
            return "Sênior"
        else:
            return "Júnior"  # Padrão
    
    def _extract_main_technologies(self, text: str) -> List[str]:
        """Extrai principais tecnologias mencionadas na vaga."""
        text = text.lower()
        
        # Lista de tecnologias comuns
        technologies = [
            "python", "javascript", "typescript", "java", "go", "rust", "php",
            "react", "vue", "angular", "node.js", "django", "flask", "spring",
            "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
            "docker", "kubernetes", "aws", "azure", "gcp", "git", "linux",
            "salesforce", "apex", "lightning", "soql"
        ]
        
        found_technologies = []
        for tech in technologies:
            if tech in text:
                found_technologies.append(tech.title())
        
        return found_technologies[:5]  # Top 5
    
    def _extract_job_specific_skill(self, text: str) -> str:
        """Extrai habilidade específica da vaga."""
        text = text.lower()
        
        # Padrões comuns
        if "salesforce" in text:
            return "Salesforce Administration"
        elif "customer service" in text or "atendimento" in text:
            return "Atendimento ao Cliente"
        elif "api" in text:
            return "Desenvolvimento de APIs"
        elif "frontend" in text or "front-end" in text:
            return "Desenvolvimento Frontend"
        elif "backend" in text or "back-end" in text:
            return "Desenvolvimento Backend"
        else:
            return "Tecnologia Relevante"
    
    def _reorder_skills(self, skills: List[str], job_text: str) -> List[str]:
        """Reordena skills baseado na relevância para a vaga."""
        job_text = job_text.lower()
        
        # Calcular pontuação de relevância para cada skill
        skill_scores = []
        for skill in skills:
            score = 0
            if skill.lower() in job_text:
                score = job_text.count(skill.lower())
            skill_scores.append((skill, score))
        
        # Ordenar por relevância
        skill_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [skill for skill, score in skill_scores]
    
    def _inject_keywords(self, resume: Dict, job_text: str) -> Dict:
        """Injeta palavras-chave relevantes no currículo."""
        try:
            keywords = self.extract_keywords(job_text, max_keywords=10)
            
            # Adicionar keywords relevantes às skills técnicas
            if "skills" in resume and "technical" in resume["skills"]:
                current_skills = [skill.lower() for skill in resume["skills"]["technical"]]
                
                for keyword in keywords:
                    if (keyword.lower() not in current_skills and 
                        len(keyword) > 2 and 
                        keyword.lower() not in ["vaga", "empresa", "trabalho", "job", "company"]):
                        resume["skills"]["technical"].append(keyword.title())
                
                # Limitar número total de skills
                resume["skills"]["technical"] = resume["skills"]["technical"][:15]
            
            return resume
            
        except Exception as e:
            self.logger.warning(f"Erro ao injetar palavras-chave: {e}")
            return resume
    
    def _generate_formats(self, resume_data: Dict) -> Dict:
        """Gera currículo em diferentes formatos."""
        try:
            formats = {
                "json": resume_data,
                "text": self._generate_text_format(resume_data),
                "markdown": self._generate_markdown_format(resume_data)
            }
            
            return formats
            
        except Exception as e:
            self.logger.error(f"Erro na geração de formatos: {e}")
            return {"json": resume_data}
    
    def _generate_text_format(self, resume_data: Dict) -> str:
        """Gera currículo em formato texto."""
        try:
            lines = []
            
            # Informações pessoais
            personal = resume_data.get("personal_info", {})
            lines.append(f"Nome: {personal.get('name', '')}")
            lines.append(f"Telefone: {personal.get('phone', '')}")
            lines.append(f"Email: {personal.get('email', '')}")
            lines.append(f"Localização: {personal.get('location', '')}")
            if personal.get('linkedin'):
                lines.append(f"LinkedIn: {personal.get('linkedin')}")
            lines.append("")
            
            # Objetivo
            if resume_data.get("objective"):
                lines.append("OBJETIVO")
                lines.append(resume_data["objective"])
                lines.append("")
            
            # Skills
            if resume_data.get("skills"):
                lines.append("COMPETÊNCIAS")
                if resume_data["skills"].get("technical"):
                    lines.append("Técnicas:")
                    lines.append(", ".join(resume_data["skills"]["technical"]))
                if resume_data["skills"].get("soft"):
                    lines.append("Comportamentais:")
                    lines.append(", ".join(resume_data["skills"]["soft"]))
                lines.append("")
            
            # Experiência
            if resume_data.get("experience"):
                lines.append("EXPERIÊNCIA")
                for exp in resume_data["experience"]:
                    lines.append(f"{exp.get('title', '')} - {exp.get('company', '')}")
                    lines.append(f"Período: {exp.get('period', '')}")
                    if exp.get("description"):
                        for desc in exp["description"]:
                            lines.append(f"• {desc}")
                    lines.append("")
            
            # Educação
            if resume_data.get("education"):
                lines.append("EDUCAÇÃO")
                for edu in resume_data["education"]:
                    lines.append(f"{edu.get('degree', '')} - {edu.get('institution', '')}")
                    lines.append(f"Período: {edu.get('period', '')} ({edu.get('status', '')})")
                lines.append("")
            
            return "\n".join(lines)
            
        except Exception as e:
            self.logger.error(f"Erro na geração de formato texto: {e}")
            return str(resume_data)
    
    def _generate_markdown_format(self, resume_data: Dict) -> str:
        """Gera currículo em formato Markdown."""
        try:
            lines = []
            
            # Informações pessoais
            personal = resume_data.get("personal_info", {})
            lines.append(f"# {personal.get('name', 'Nome')}")
            lines.append("")
            lines.append(f"**Telefone:** {personal.get('phone', '')}")
            lines.append(f"**Email:** {personal.get('email', '')}")
            lines.append(f"**Localização:** {personal.get('location', '')}")
            if personal.get('linkedin'):
                lines.append(f"**LinkedIn:** {personal.get('linkedin')}")
            lines.append("")
            
            # Objetivo
            if resume_data.get("objective"):
                lines.append("## Objetivo")
                lines.append(resume_data["objective"])
                lines.append("")
            
            # Skills
            if resume_data.get("skills"):
                lines.append("## Competências")
                if resume_data["skills"].get("technical"):
                    lines.append("### Técnicas")
                    for skill in resume_data["skills"]["technical"]:
                        lines.append(f"- {skill}")
                    lines.append("")
                if resume_data["skills"].get("soft"):
                    lines.append("### Comportamentais")
                    for skill in resume_data["skills"]["soft"]:
                        lines.append(f"- {skill}")
                    lines.append("")
            
            # Experiência
            if resume_data.get("experience"):
                lines.append("## Experiência")
                for exp in resume_data["experience"]:
                    lines.append(f"### {exp.get('title', '')} - {exp.get('company', '')}")
                    lines.append(f"**Período:** {exp.get('period', '')}")
                    if exp.get("description"):
                        for desc in exp["description"]:
                            lines.append(f"- {desc}")
                    lines.append("")
            
            # Educação
            if resume_data.get("education"):
                lines.append("## Educação")
                for edu in resume_data["education"]:
                    lines.append(f"### {edu.get('degree', '')}")
                    lines.append(f"**Instituição:** {edu.get('institution', '')}")
                    lines.append(f"**Período:** {edu.get('period', '')} ({edu.get('status', '')})")
                    lines.append("")
            
            return "\n".join(lines)
            
        except Exception as e:
            self.logger.error(f"Erro na geração de formato Markdown: {e}")
            return str(resume_data)
    
    def generate_multiple_resumes(self, jobs_with_analysis: List[Dict]) -> List[Dict]:
        """Gera currículos personalizados para múltiplas vagas."""
        try:
            resumes = []
            
            for job_data in jobs_with_analysis:
                analysis = job_data.get("analysis", {})
                resume = self.process(job_data, analysis)
                
                resume_with_job = {
                    "job_id": job_data.get("id"),
                    "job_title": job_data.get("title"),
                    "job_company": job_data.get("company"),
                    "resume": resume
                }
                
                resumes.append(resume_with_job)
            
            self.logger.info(f"Gerados {len(resumes)} currículos personalizados")
            return resumes
            
        except Exception as e:
            self.logger.error(f"Erro na geração múltipla de currículos: {e}")
            return []

