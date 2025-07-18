"""
Respondedor automático de questionários de vagas.
"""
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from .base_ai import BaseAI
from backend.config.settings import settings


class QuestionnaireResponder(BaseAI):
    """Responde automaticamente questionários de vagas usando IA."""
    
    def __init__(self):
        super().__init__("questionnaire_responder")
        
        # Respostas padrão por categoria
        self.standard_responses = {
            "experience": {
                "pt": {
                    "yes": "Sim, tenho experiência na área",
                    "no": "Não tenho experiência específica, mas estou disposto a aprender",
                    "learning": "Estou em processo de aprendizado"
                },
                "en": {
                    "yes": "Yes, I have experience in this area",
                    "no": "I don't have specific experience, but I'm willing to learn",
                    "learning": "I'm currently learning"
                }
            },
            "availability": {
                "pt": {
                    "immediate": "Disponibilidade imediata",
                    "two_weeks": "Disponível em 2 semanas",
                    "flexible": "Horários flexíveis"
                },
                "en": {
                    "immediate": "Immediate availability",
                    "two_weeks": "Available in 2 weeks",
                    "flexible": "Flexible schedule"
                }
            },
            "motivation": {
                "pt": {
                    "growth": "Busco crescimento profissional e novos desafios",
                    "company": "Tenho interesse na empresa e na vaga",
                    "remote": "Valorizo a oportunidade de trabalho remoto"
                },
                "en": {
                    "growth": "I seek professional growth and new challenges",
                    "company": "I'm interested in the company and the position",
                    "remote": "I value the remote work opportunity"
                }
            }
        }
    
    def process(self, questions: List[Dict], job_data: Dict = None, job_analysis: Dict = None) -> Dict:
        """Processa lista de questões e gera respostas."""
        try:
            # Detectar idioma das questões
            language = self._detect_questions_language(questions)
            
            # Processar cada questão
            responses = []
            complex_questions = []
            
            for i, question in enumerate(questions):
                try:
                    response = self._process_single_question(question, job_data, job_analysis, language)
                    
                    if response["needs_human_review"]:
                        complex_questions.append({
                            "index": i,
                            "question": question,
                            "reason": response.get("review_reason", "Questão complexa")
                        })
                    
                    responses.append(response)
                    
                except Exception as e:
                    self.logger.warning(f"Erro ao processar questão {i}: {e}")
                    responses.append({
                        "question_id": question.get("id", i),
                        "answer": "",
                        "confidence": 0.0,
                        "needs_human_review": True,
                        "review_reason": f"Erro no processamento: {e}"
                    })
            
            return {
                "language": language,
                "total_questions": len(questions),
                "auto_answered": len([r for r in responses if not r["needs_human_review"]]),
                "needs_review": len(complex_questions),
                "responses": responses,
                "complex_questions": complex_questions,
                "processed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro no processamento do questionário: {e}")
            return {"error": str(e)}
    
    def _detect_questions_language(self, questions: List[Dict]) -> str:
        """Detecta idioma predominante das questões."""
        try:
            all_text = ""
            for question in questions:
                text = question.get("text", "") or question.get("question", "")
                all_text += " " + text
            
            return self.detect_language(all_text)
            
        except Exception as e:
            self.logger.warning(f"Erro na detecção de idioma: {e}")
            return "pt"
    
    def _process_single_question(self, question: Dict, job_data: Dict, 
                                job_analysis: Dict, language: str) -> Dict:
        """Processa uma única questão."""
        try:
            question_text = question.get("text", "") or question.get("question", "")
            question_type = question.get("type", "text")
            question_id = question.get("id", "")
            options = question.get("options", [])
            required = question.get("required", False)
            
            # Classificar tipo de questão
            question_category = self._classify_question(question_text, language)
            
            # Determinar se precisa de revisão humana
            needs_review, review_reason = self._needs_human_review(
                question_text, question_type, question_category, required
            )
            
            if needs_review:
                return {
                    "question_id": question_id,
                    "answer": "",
                    "confidence": 0.0,
                    "needs_human_review": True,
                    "review_reason": review_reason,
                    "question_category": question_category
                }
            
            # Gerar resposta automática
            answer, confidence = self._generate_answer(
                question_text, question_type, question_category, 
                options, job_data, job_analysis, language
            )
            
            return {
                "question_id": question_id,
                "answer": answer,
                "confidence": confidence,
                "needs_human_review": False,
                "question_category": question_category,
                "question_type": question_type
            }
            
        except Exception as e:
            self.logger.warning(f"Erro ao processar questão individual: {e}")
            return {
                "question_id": question.get("id", ""),
                "answer": "",
                "confidence": 0.0,
                "needs_human_review": True,
                "review_reason": f"Erro: {e}"
            }
    
    def _classify_question(self, question_text: str, language: str) -> str:
        """Classifica o tipo/categoria da questão."""
        try:
            text = question_text.lower()
            
            # Padrões por categoria
            patterns = {
                "experience": [
                    "experiência", "experience", "anos", "years", "tempo", "time",
                    "trabalhou", "worked", "conhecimento", "knowledge"
                ],
                "availability": [
                    "disponibilidade", "availability", "horário", "schedule", 
                    "quando", "when", "início", "start", "imediato", "immediate"
                ],
                "motivation": [
                    "por que", "why", "motivo", "reason", "interesse", "interest",
                    "escolheu", "chose", "empresa", "company"
                ],
                "salary": [
                    "salário", "salary", "remuneração", "compensation", 
                    "pretensão", "expectation", "valor", "amount"
                ],
                "personal": [
                    "nome", "name", "idade", "age", "endereço", "address",
                    "telefone", "phone", "email", "cpf", "rg"
                ],
                "technical": [
                    "tecnologia", "technology", "ferramenta", "tool",
                    "linguagem", "language", "framework", "banco", "database"
                ],
                "education": [
                    "formação", "education", "curso", "course", "faculdade",
                    "university", "graduação", "degree"
                ],
                "yes_no": [
                    "você tem", "do you have", "possui", "have you",
                    "já trabalhou", "have worked", "conhece", "know"
                ]
            }
            
            # Verificar padrões
            for category, keywords in patterns.items():
                if any(keyword in text for keyword in keywords):
                    return category
            
            return "general"
            
        except Exception as e:
            self.logger.warning(f"Erro na classificação da questão: {e}")
            return "general"
    
    def _needs_human_review(self, question_text: str, question_type: str, 
                           category: str, required: bool) -> Tuple[bool, str]:
        """Determina se a questão precisa de revisão humana."""
        try:
            text = question_text.lower()
            
            # Sempre revisar questões sensíveis
            sensitive_keywords = [
                "salário", "salary", "remuneração", "pretensão salarial",
                "cpf", "rg", "documento", "endereço completo",
                "por que você", "why do you", "conte sobre",
                "descreva uma situação", "describe a situation",
                "maior desafio", "biggest challenge",
                "ponto fraco", "weakness", "defeito"
            ]
            
            if any(keyword in text for keyword in sensitive_keywords):
                return True, "Questão sensível que requer resposta personalizada"
            
            # Revisar questões muito específicas
            if len(question_text) > 200:
                return True, "Questão muito longa e específica"
            
            # Revisar questões abertas complexas
            if question_type in ["textarea", "long_text"] and category in ["motivation", "personal"]:
                return True, "Questão aberta que requer resposta personalizada"
            
            # Revisar se obrigatória e não conseguimos classificar
            if required and category == "general":
                return True, "Questão obrigatória não classificada"
            
            return False, ""
            
        except Exception as e:
            self.logger.warning(f"Erro na verificação de revisão: {e}")
            return True, f"Erro na análise: {e}"
    
    def _generate_answer(self, question_text: str, question_type: str, category: str,
                        options: List, job_data: Dict, job_analysis: Dict, language: str) -> Tuple[str, float]:
        """Gera resposta automática para a questão."""
        try:
            # Respostas baseadas no tipo de questão
            if question_type in ["select", "radio", "checkbox"] and options:
                return self._handle_multiple_choice(question_text, options, category, language)
            
            elif question_type in ["yes_no", "boolean"]:
                return self._handle_yes_no(question_text, category, job_data, language)
            
            elif question_type in ["number", "integer"]:
                return self._handle_numeric(question_text, category, language)
            
            elif question_type in ["text", "input"]:
                return self._handle_text_input(question_text, category, job_data, language)
            
            else:
                # Tentar gerar com IA para tipos desconhecidos
                return self._generate_with_ai(question_text, job_data, job_analysis, language)
                
        except Exception as e:
            self.logger.warning(f"Erro na geração de resposta: {e}")
            return "", 0.0
    
    def _handle_multiple_choice(self, question_text: str, options: List, 
                               category: str, language: str) -> Tuple[str, float]:
        """Trata questões de múltipla escolha."""
        try:
            text = question_text.lower()
            
            # Lógica baseada na categoria
            if category == "experience":
                # Procurar opções que indiquem experiência júnior/iniciante
                for option in options:
                    option_text = str(option).lower()
                    if any(word in option_text for word in ["júnior", "junior", "iniciante", "entry", "1-2", "0-1"]):
                        return str(option), 0.8
                
                # Se não encontrar, pegar primeira opção
                return str(options[0]) if options else "", 0.5
            
            elif category == "availability":
                # Procurar disponibilidade imediata ou flexível
                for option in options:
                    option_text = str(option).lower()
                    if any(word in option_text for word in ["imediato", "immediate", "flexível", "flexible"]):
                        return str(option), 0.9
                
                return str(options[0]) if options else "", 0.6
            
            elif category == "education":
                # Procurar opções de ensino superior
                for option in options:
                    option_text = str(option).lower()
                    if any(word in option_text for word in ["superior", "graduação", "tecnólogo", "bachelor"]):
                        return str(option), 0.8
                
                return str(options[-1]) if options else "", 0.5
            
            else:
                # Para outras categorias, escolher primeira opção válida
                return str(options[0]) if options else "", 0.5
                
        except Exception as e:
            self.logger.warning(f"Erro em múltipla escolha: {e}")
            return str(options[0]) if options else "", 0.3
    
    def _handle_yes_no(self, question_text: str, category: str, 
                      job_data: Dict, language: str) -> Tuple[str, float]:
        """Trata questões sim/não."""
        try:
            text = question_text.lower()
            
            # Respostas baseadas no contexto
            if category == "experience":
                # Se pergunta sobre tecnologia específica, verificar se está na vaga
                job_description = job_data.get("description", "").lower() if job_data else ""
                
                # Extrair tecnologias da pergunta
                tech_keywords = ["python", "javascript", "react", "sql", "git", "docker", "aws"]
                mentioned_tech = [tech for tech in tech_keywords if tech in text]
                
                if mentioned_tech and job_description:
                    # Se a tecnologia está na vaga, responder sim
                    if any(tech in job_description for tech in mentioned_tech):
                        return "Sim" if language == "pt" else "Yes", 0.7
                
                # Para experiência geral, responder sim com confiança moderada
                if any(word in text for word in ["experiência", "experience", "trabalhou", "worked"]):
                    return "Sim" if language == "pt" else "Yes", 0.6
            
            elif category == "availability":
                # Sempre disponível para trabalho remoto
                return "Sim" if language == "pt" else "Yes", 0.9
            
            elif category == "technical":
                # Para questões técnicas, responder sim se for tecnologia básica
                basic_tech = ["computador", "computer", "internet", "email", "office"]
                if any(tech in text for tech in basic_tech):
                    return "Sim" if language == "pt" else "Yes", 0.9
            
            # Padrão: responder sim para a maioria das questões
            return "Sim" if language == "pt" else "Yes", 0.5
            
        except Exception as e:
            self.logger.warning(f"Erro em questão sim/não: {e}")
            return "Sim" if language == "pt" else "Yes", 0.3
    
    def _handle_numeric(self, question_text: str, category: str, language: str) -> Tuple[str, float]:
        """Trata questões numéricas."""
        try:
            text = question_text.lower()
            
            if category == "experience":
                # Anos de experiência - responder baseado no nível
                if any(word in text for word in ["anos", "years"]):
                    return "1", 0.7  # 1 ano de experiência
            
            elif "idade" in text or "age" in text:
                return "25", 0.8  # Idade padrão
            
            elif "salário" in text or "salary" in text:
                return "", 0.0  # Não responder questões de salário automaticamente
            
            return "1", 0.4  # Valor padrão baixo
            
        except Exception as e:
            self.logger.warning(f"Erro em questão numérica: {e}")
            return "0", 0.2
    
    def _handle_text_input(self, question_text: str, category: str, 
                          job_data: Dict, language: str) -> Tuple[str, float]:
        """Trata questões de texto livre."""
        try:
            text = question_text.lower()
            
            # Informações pessoais básicas
            if "nome" in text or "name" in text:
                return settings.USER_FULL_NAME or "Nome do Candidato", 0.9
            
            elif "email" in text:
                return settings.EMAIL_ADDRESS or "email@exemplo.com", 0.9
            
            elif "telefone" in text or "phone" in text:
                return settings.USER_PHONE or "(11) 99999-9999", 0.9
            
            elif "cidade" in text or "city" in text:
                return settings.USER_LOCATION or "São Paulo, SP", 0.8
            
            # Para outras questões de texto, usar respostas padrão
            elif category == "motivation":
                responses = self.standard_responses["motivation"][language]
                return responses["growth"], 0.6
            
            elif category == "availability":
                responses = self.standard_responses["availability"][language]
                return responses["immediate"], 0.7
            
            return "", 0.0  # Não responder questões de texto complexas
            
        except Exception as e:
            self.logger.warning(f"Erro em questão de texto: {e}")
            return "", 0.0
    
    def _generate_with_ai(self, question_text: str, job_data: Dict, 
                         job_analysis: Dict, language: str) -> Tuple[str, float]:
        """Gera resposta usando IA para questões complexas."""
        try:
            if not settings.OPENAI_API_KEY:
                return "", 0.0
            
            # Criar contexto
            job_title = job_data.get("title", "") if job_data else ""
            company = job_data.get("company", "") if job_data else ""
            
            if language == "en":
                prompt = f"""Answer this job application question professionally and concisely:

Question: {question_text}
Job: {job_title} at {company}

Provide a brief, professional answer (1-2 sentences max):"""
            else:
                prompt = f"""Responda esta pergunta de candidatura profissionalmente e de forma concisa:

Pergunta: {question_text}
Vaga: {job_title} na {company}

Forneça uma resposta breve e profissional (máximo 1-2 frases):"""
            
            # Chamar IA
            ai_response = self.call_openai_api(prompt, max_tokens=100, temperature=0.5)
            
            if ai_response and len(ai_response.strip()) > 5:
                return ai_response.strip(), 0.6
            
            return "", 0.0
            
        except Exception as e:
            self.logger.warning(f"Erro na geração com IA: {e}")
            return "", 0.0
    
    def create_telegram_notification(self, complex_questions: List[Dict], 
                                   job_data: Dict = None) -> str:
        """Cria notificação para Telegram sobre questões que precisam de revisão."""
        try:
            job_title = job_data.get("title", "Vaga") if job_data else "Vaga"
            company = job_data.get("company", "Empresa") if job_data else "Empresa"
            
            message = f"🤖 *Questionário requer atenção*\n\n"
            message += f"📋 *Vaga:* {job_title}\n"
            message += f"🏢 *Empresa:* {company}\n\n"
            message += f"❓ *Questões que precisam de resposta manual:*\n\n"
            
            for i, item in enumerate(complex_questions[:5], 1):  # Máximo 5 questões
                question = item["question"]
                question_text = question.get("text", "") or question.get("question", "")
                reason = item.get("reason", "Questão complexa")
                
                message += f"{i}. *Questão:* {question_text[:100]}...\n"
                message += f"   *Motivo:* {reason}\n\n"
            
            if len(complex_questions) > 5:
                message += f"... e mais {len(complex_questions) - 5} questões\n\n"
            
            message += "⚡ *Ação necessária:* Acesse o sistema para responder manualmente"
            
            return message
            
        except Exception as e:
            self.logger.error(f"Erro na criação de notificação: {e}")
            return "Erro ao criar notificação de questionário"

