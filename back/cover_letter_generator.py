"""
Gerador de cartas de apresentação personalizadas.
"""
from typing import Dict, List, Optional
from datetime import datetime

from .base_ai import BaseAI
from backend.config.settings import settings


class CoverLetterGenerator(BaseAI):
    """Gera cartas de apresentação personalizadas para vagas específicas."""
    
    def __init__(self):
        super().__init__("cover_letter_generator")
        
        # Templates de carta base
        self.letter_templates = {
            "dev": {
                "pt": self._get_dev_template_pt(),
                "en": self._get_dev_template_en()
            },
            "admin": {
                "pt": self._get_admin_template_pt(),
                "en": self._get_admin_template_en()
            }
        }
    
    def process(self, job_data: Dict, job_analysis: Dict = None, resume_data: Dict = None) -> Dict:
        """Gera carta de apresentação personalizada."""
        try:
            # Determinar tipo de vaga e idioma
            job_type = job_analysis.get("job_type", "dev") if job_analysis else "dev"
            language = job_analysis.get("language", "pt") if job_analysis else self.detect_language(
                job_data.get("description", "")
            )
            
            # Gerar carta usando IA
            ai_generated = self._generate_with_ai(job_data, job_analysis, resume_data, job_type, language)
            
            # Gerar carta usando template
            template_generated = self._generate_with_template(job_data, job_analysis, job_type, language)
            
            # Escolher melhor versão ou combinar
            final_letter = self._select_best_version(ai_generated, template_generated)
            
            return {
                "job_type": job_type,
                "language": language,
                "cover_letter": final_letter,
                "ai_version": ai_generated,
                "template_version": template_generated,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro na geração da carta: {e}")
            return {"error": str(e)}
    
    def _generate_with_ai(self, job_data: Dict, job_analysis: Dict, resume_data: Dict, 
                         job_type: str, language: str) -> Optional[str]:
        """Gera carta usando modelos de IA."""
        try:
            # Preparar contexto
            job_title = job_data.get("title", "")
            company = job_data.get("company", "")
            job_description = job_data.get("description", "")
            
            # Extrair informações relevantes
            key_requirements = self._extract_key_requirements(job_description)
            user_skills = self._extract_user_skills(resume_data) if resume_data else []
            
            # Criar prompt baseado no idioma
            if language == "en":
                prompt = self._create_english_prompt(job_title, company, job_description, 
                                                   key_requirements, user_skills, job_type)
            else:
                prompt = self._create_portuguese_prompt(job_title, company, job_description, 
                                                       key_requirements, user_skills, job_type)
            
            # Tentar OpenAI primeiro
            if settings.OPENAI_API_KEY:
                ai_letter = self.call_openai_api(prompt, max_tokens=800, temperature=0.7)
                if ai_letter:
                    return self._clean_and_format_letter(ai_letter)
            
            # Fallback para Hugging Face
            hf_letter = self.call_huggingface_generation(
                "microsoft/DialoGPT-medium", 
                prompt, 
                max_length=600
            )
            
            if hf_letter:
                return self._clean_and_format_letter(hf_letter)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erro na geração com IA: {e}")
            return None
    
    def _create_portuguese_prompt(self, job_title: str, company: str, job_description: str,
                                key_requirements: List[str], user_skills: List[str], job_type: str) -> str:
        """Cria prompt em português para geração da carta."""
        
        prompt = f"""Escreva uma carta de apresentação profissional e personalizada para a seguinte vaga:

Vaga: {job_title}
Empresa: {company}

Requisitos principais da vaga:
{chr(10).join(f"- {req}" for req in key_requirements[:5])}

Minhas principais competências:
{chr(10).join(f"- {skill}" for skill in user_skills[:8])}

A carta deve:
1. Ser dirigida à empresa {company}
2. Demonstrar interesse específico na vaga de {job_title}
3. Destacar como minhas competências se alinham com os requisitos
4. Ser profissional mas não formal demais
5. Ter entre 200-300 palavras
6. Mencionar que estou disponível para trabalho remoto
7. Incluir uma chamada para ação no final

Carta de apresentação:"""

        return prompt
    
    def _create_english_prompt(self, job_title: str, company: str, job_description: str,
                             key_requirements: List[str], user_skills: List[str], job_type: str) -> str:
        """Cria prompt em inglês para geração da carta."""
        
        prompt = f"""Write a professional and personalized cover letter for the following job:

Position: {job_title}
Company: {company}

Main job requirements:
{chr(10).join(f"- {req}" for req in key_requirements[:5])}

My main skills:
{chr(10).join(f"- {skill}" for skill in user_skills[:8])}

The cover letter should:
1. Be addressed to {company}
2. Show specific interest in the {job_title} position
3. Highlight how my skills align with the requirements
4. Be professional but not overly formal
5. Be 200-300 words long
6. Mention availability for remote work
7. Include a call to action at the end

Cover letter:"""

        return prompt
    
    def _generate_with_template(self, job_data: Dict, job_analysis: Dict, 
                              job_type: str, language: str) -> str:
        """Gera carta usando template personalizado."""
        try:
            # Obter template base
            template = self.letter_templates.get(job_type, {}).get(language, "")
            if not template:
                template = self.letter_templates["dev"]["pt"]
            
            # Extrair informações da vaga
            job_title = job_data.get("title", "Vaga")
            company = job_data.get("company", "Empresa")
            job_description = job_data.get("description", "")
            
            # Extrair tecnologias/skills relevantes
            relevant_skills = self._extract_relevant_skills(job_description, job_type)
            
            # Personalizar template
            personalized_letter = template.format(
                company=company,
                job_title=job_title,
                user_name=settings.USER_FULL_NAME or "Candidato",
                relevant_skills=", ".join(relevant_skills[:3]),
                main_skill=relevant_skills[0] if relevant_skills else "tecnologias modernas",
                user_phone=settings.USER_PHONE,
                user_email=settings.EMAIL_ADDRESS
            )
            
            return personalized_letter
            
        except Exception as e:
            self.logger.error(f"Erro na geração com template: {e}")
            return self._get_fallback_letter(job_data, language)
    
    def _get_dev_template_pt(self) -> str:
        """Template de carta para desenvolvedor em português."""
        return """Prezados recrutadores da {company},

Venho por meio desta demonstrar meu interesse na vaga de {job_title} anunciada por vocês. Como desenvolvedor apaixonado por tecnologia, acredito que meu perfil se alinha perfeitamente com os requisitos da posição.

Tenho experiência sólida em {relevant_skills}, tecnologias que identifiquei como fundamentais para o sucesso nesta função. Minha abordagem combina conhecimento técnico com capacidade de resolução de problemas, sempre buscando soluções eficientes e inovadoras.

Destaco minha experiência em {main_skill}, que considero um diferencial importante para contribuir com os projetos da {company}. Além disso, tenho facilidade para aprender novas tecnologias e me adaptar rapidamente a diferentes ambientes de desenvolvimento.

Estou totalmente disponível para trabalho remoto e possuo excelentes habilidades de comunicação para colaboração em equipes distribuídas. Minha proatividade e comprometimento me permitem entregar resultados de qualidade dentro dos prazos estabelecidos.

Gostaria muito de ter a oportunidade de conversar sobre como posso contribuir para o crescimento da {company}. Estou disponível para uma entrevista a qualquer momento.

Atenciosamente,
{user_name}
Telefone: {user_phone}
Email: {user_email}"""
    
    def _get_dev_template_en(self) -> str:
        """Template de carta para desenvolvedor em inglês."""
        return """Dear {company} Hiring Team,

I am writing to express my strong interest in the {job_title} position advertised by your company. As a passionate developer with a love for technology, I believe my profile aligns perfectly with the requirements of this role.

I have solid experience in {relevant_skills}, technologies that I identified as fundamental for success in this position. My approach combines technical knowledge with problem-solving capabilities, always seeking efficient and innovative solutions.

I would like to highlight my experience in {main_skill}, which I consider an important differentiator to contribute to {company}'s projects. Additionally, I have the ability to quickly learn new technologies and adapt to different development environments.

I am fully available for remote work and possess excellent communication skills for collaboration in distributed teams. My proactivity and commitment enable me to deliver quality results within established deadlines.

I would very much like the opportunity to discuss how I can contribute to {company}'s growth. I am available for an interview at any time.

Best regards,
{user_name}
Phone: {user_phone}
Email: {user_email}"""
    
    def _get_admin_template_pt(self) -> str:
        """Template de carta para atendimento/admin em português."""
        return """Prezados recrutadores da {company},

É com grande interesse que me candidato à vaga de {job_title} em sua empresa. Meu perfil profissional está alinhado com os requisitos da posição, e acredito poder contribuir significativamente para a excelência no atendimento da {company}.

Possuo experiência em {relevant_skills}, competências essenciais para oferecer um atendimento de qualidade e resolver eficientemente as demandas dos clientes. Minha abordagem é sempre focada na satisfação do cliente e na resolução rápida de problemas.

Destaco minha habilidade em {main_skill}, que me permite lidar com situações diversas mantendo sempre a qualidade e profissionalismo no atendimento. Tenho facilidade para trabalhar com diferentes sistemas e ferramentas, adaptando-me rapidamente às necessidades da empresa.

Estou totalmente disponível para trabalho remoto e possuo excelentes habilidades de comunicação, tanto escrita quanto verbal. Minha paciência, empatia e proatividade são características que considero fundamentais para o sucesso nesta função.

Gostaria muito de ter a oportunidade de contribuir para o sucesso da {company} e demonstrar meu comprometimento com a excelência no atendimento. Estou disponível para uma conversa a qualquer momento.

Atenciosamente,
{user_name}
Telefone: {user_phone}
Email: {user_email}"""
    
    def _get_admin_template_en(self) -> str:
        """Template de carta para atendimento/admin em inglês."""
        return """Dear {company} Hiring Team,

I am writing to express my strong interest in the {job_title} position at your company. My professional profile aligns with the position requirements, and I believe I can contribute significantly to {company}'s customer service excellence.

I have experience in {relevant_skills}, essential competencies for providing quality service and efficiently resolving customer demands. My approach is always focused on customer satisfaction and quick problem resolution.

I would like to highlight my skill in {main_skill}, which allows me to handle diverse situations while maintaining quality and professionalism in service. I have the ability to work with different systems and tools, quickly adapting to company needs.

I am fully available for remote work and possess excellent communication skills, both written and verbal. My patience, empathy, and proactivity are characteristics I consider fundamental for success in this role.

I would very much like the opportunity to contribute to {company}'s success and demonstrate my commitment to service excellence. I am available for a conversation at any time.

Best regards,
{user_name}
Phone: {user_phone}
Email: {user_email}"""
    
    def _extract_key_requirements(self, job_description: str) -> List[str]:
        """Extrai requisitos principais da descrição da vaga."""
        try:
            # Usar regex para encontrar requisitos
            import re
            
            requirements = []
            
            # Padrões para requisitos
            patterns = [
                r"requisitos?[:\s]*([^.!?\n]+)",
                r"requirements?[:\s]*([^.!?\n]+)",
                r"necessário[:\s]*([^.!?\n]+)",
                r"required[:\s]*([^.!?\n]+)",
                r"experiência em[:\s]*([^.!?\n]+)",
                r"experience in[:\s]*([^.!?\n]+)"
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, job_description, re.IGNORECASE)
                requirements.extend(matches)
            
            # Limpar e filtrar
            cleaned_requirements = []
            for req in requirements:
                cleaned = req.strip().strip(",;")
                if len(cleaned) > 5 and len(cleaned) < 100:
                    cleaned_requirements.append(cleaned)
            
            return cleaned_requirements[:5]
            
        except Exception as e:
            self.logger.warning(f"Erro ao extrair requisitos: {e}")
            return []
    
    def _extract_user_skills(self, resume_data: Dict) -> List[str]:
        """Extrai skills do usuário do currículo."""
        try:
            if not resume_data:
                return []
            
            skills = []
            
            # Extrair skills técnicas
            resume_content = resume_data.get("resume_data", {})
            if "skills" in resume_content:
                technical_skills = resume_content["skills"].get("technical", [])
                skills.extend(technical_skills[:8])
            
            return skills
            
        except Exception as e:
            self.logger.warning(f"Erro ao extrair skills do usuário: {e}")
            return []
    
    def _extract_relevant_skills(self, job_description: str, job_type: str) -> List[str]:
        """Extrai skills relevantes baseado no tipo de vaga."""
        try:
            job_description = job_description.lower()
            
            if job_type == "dev":
                dev_skills = [
                    "python", "javascript", "typescript", "react", "node.js",
                    "sql", "postgresql", "mongodb", "git", "docker",
                    "api", "rest", "html", "css", "linux", "aws",
                    "salesforce", "apex", "lightning"
                ]
                
                relevant = []
                for skill in dev_skills:
                    if skill in job_description:
                        relevant.append(skill.title())
                
                return relevant[:5]
                
            else:  # admin
                admin_skills = [
                    "atendimento ao cliente", "customer service", "suporte técnico",
                    "excel", "crm", "chat", "email", "telefone",
                    "helpdesk", "resolução de problemas"
                ]
                
                relevant = []
                for skill in admin_skills:
                    if skill in job_description:
                        relevant.append(skill.title())
                
                return relevant[:5]
                
        except Exception as e:
            self.logger.warning(f"Erro ao extrair skills relevantes: {e}")
            return ["tecnologias modernas"]
    
    def _select_best_version(self, ai_version: Optional[str], template_version: str) -> str:
        """Seleciona a melhor versão da carta."""
        try:
            # Se IA gerou uma carta válida, usar ela
            if ai_version and len(ai_version) > 100:
                # Verificar qualidade básica
                if self._validate_letter_quality(ai_version):
                    return ai_version
            
            # Fallback para template
            return template_version
            
        except Exception as e:
            self.logger.warning(f"Erro na seleção da melhor versão: {e}")
            return template_version
    
    def _validate_letter_quality(self, letter: str) -> bool:
        """Valida qualidade básica da carta."""
        try:
            # Verificações básicas
            if len(letter) < 100 or len(letter) > 2000:
                return False
            
            # Verificar se tem estrutura básica
            has_greeting = any(word in letter.lower() for word in ["prezados", "dear", "olá", "hello"])
            has_closing = any(word in letter.lower() for word in ["atenciosamente", "regards", "cordialmente"])
            
            return has_greeting and has_closing
            
        except Exception as e:
            self.logger.warning(f"Erro na validação da carta: {e}")
            return False
    
    def _clean_and_format_letter(self, letter: str) -> str:
        """Limpa e formata a carta gerada."""
        try:
            # Remover caracteres desnecessários
            letter = letter.strip()
            
            # Normalizar quebras de linha
            import re
            letter = re.sub(r'\n\s*\n\s*\n', '\n\n', letter)
            
            # Limitar tamanho
            if len(letter) > 1500:
                sentences = letter.split('.')
                letter = '.'.join(sentences[:10]) + '.'
            
            return letter
            
        except Exception as e:
            self.logger.warning(f"Erro na limpeza da carta: {e}")
            return letter
    
    def _get_fallback_letter(self, job_data: Dict, language: str) -> str:
        """Carta de fallback em caso de erro."""
        company = job_data.get("company", "Empresa")
        job_title = job_data.get("title", "Vaga")
        
        if language == "en":
            return f"""Dear {company} Hiring Team,

I am writing to express my interest in the {job_title} position. I believe my skills and experience make me a strong candidate for this role.

I am available for remote work and committed to delivering quality results. I would welcome the opportunity to discuss how I can contribute to your team.

Best regards,
{settings.USER_FULL_NAME or 'Candidate'}"""
        else:
            return f"""Prezados recrutadores da {company},

Venho demonstrar meu interesse na vaga de {job_title}. Acredito que meu perfil e experiência me tornam um candidato adequado para esta posição.

Estou disponível para trabalho remoto e comprometido em entregar resultados de qualidade. Gostaria da oportunidade de conversar sobre como posso contribuir com a equipe.

Atenciosamente,
{settings.USER_FULL_NAME or 'Candidato'}"""
    
    def generate_multiple_letters(self, jobs_with_analysis: List[Dict], resumes: List[Dict] = None) -> List[Dict]:
        """Gera cartas para múltiplas vagas."""
        try:
            letters = []
            
            for i, job_data in enumerate(jobs_with_analysis):
                analysis = job_data.get("analysis", {})
                resume_data = resumes[i] if resumes and i < len(resumes) else None
                
                letter = self.process(job_data, analysis, resume_data)
                
                letter_with_job = {
                    "job_id": job_data.get("id"),
                    "job_title": job_data.get("title"),
                    "job_company": job_data.get("company"),
                    "letter": letter
                }
                
                letters.append(letter_with_job)
            
            self.logger.info(f"Geradas {len(letters)} cartas de apresentação")
            return letters
            
        except Exception as e:
            self.logger.error(f"Erro na geração múltipla de cartas: {e}")
            return []

