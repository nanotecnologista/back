# JobBot - Backend API

API REST para sistema de automação de candidaturas para vagas de emprego desenvolvida em Flask.

## 🚀 Tecnologias Utilizadas

- **Flask** - Framework web Python
- **Flask-CORS** - Suporte a CORS
- **Python 3.11+** - Linguagem de programação

## 📁 Estrutura do Projeto

```
back/
├── app.py                 # Aplicação principal Flask
├── requirements.txt       # Dependências Python
├── venv/                 # Ambiente virtual
└── README.md             # Documentação
```

## 🎯 Endpoints da API

### Vagas (Jobs)
- `GET /api/jobs` - Lista todas as vagas
- `GET /api/jobs/<id>` - Detalhes de uma vaga específica
- `POST /api/jobs/search` - Inicia busca por novas vagas
- `POST /api/jobs/<id>/analyze` - Analisa compatibilidade de uma vaga
- `PUT /api/jobs/<id>/status` - Atualiza status de uma vaga

### Candidaturas (Applications)
- `GET /api/applications` - Lista todas as candidaturas
- `GET /api/applications/<id>` - Detalhes de uma candidatura específica
- `POST /api/applications` - Cria nova candidatura
- `PUT /api/applications/<id>/status` - Atualiza status de candidatura
- `POST /api/applications/<id>/generate_resume` - Gera currículo
- `POST /api/applications/<id>/generate_cover_letter` - Gera carta de apresentação
- `POST /api/applications/<id>/respond_questionnaire` - Responde questionário

### Configurações (Settings)
- `GET /api/settings` - Obtém configurações do sistema
- `POST /api/settings` - Atualiza configurações
- `POST /api/settings/test_connection` - Testa conexão com plataforma
- `GET /api/settings/system_info` - Informações do sistema

### Analytics
- `GET /api/analytics/stats` - Estatísticas para analytics

## 🛠️ Instalação e Execução

### Pré-requisitos
- Python 3.11+
- pip

### Instalação
```bash
# Criar ambiente virtual
python3 -m venv venv

# Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt
```

### Execução
```bash
# Ativar ambiente virtual
source venv/bin/activate

# Executar servidor
python app.py

# API disponível em http://localhost:8000
```

## 📊 Dados Mock

A API utiliza dados mock para demonstração:

### Vagas de Exemplo
- Desenvolvedor Python Júnior (TechCorp)
- Desenvolvedor TypeScript (StartupXYZ)
- Assistente Administrativo Remoto (AdminCorp)

### Candidaturas de Exemplo
- 3 candidaturas com diferentes status
- Documentos simulados (CV, carta, questionário)

## 🔧 Configuração

### CORS
Configurado para aceitar requisições de:
- `http://localhost:5173` (Frontend development)
- `http://localhost:8000` (Backend development)

### Estrutura de Resposta

#### Vaga (Job)
```json
{
  "id": "1",
  "title": "Desenvolvedor Python Júnior",
  "company": "TechCorp",
  "location": "São Paulo, SP",
  "type": "Remoto",
  "level": "Júnior",
  "compatibility": 85,
  "description": "Descrição da vaga...",
  "skills": ["Python", "Backend", "Remote"],
  "platform": "LinkedIn",
  "posted_date": "2025-07-13",
  "salary_range": "R$ 4.000 - R$ 6.000",
  "status": "nova"
}
```

#### Candidatura (Application)
```json
{
  "id": "1",
  "job_id": "1",
  "job_title": "Desenvolvedor Python Júnior",
  "company": "TechCorp",
  "platform": "LinkedIn",
  "status": "Enviada",
  "applied_date": "2025-07-13T10:30:00",
  "documents": {
    "cv": true,
    "cover_letter": true,
    "questionnaire": true
  }
}
```

## 🔍 Filtros Disponíveis

### Vagas
- `platform`: Filtra por plataforma (linkedin, gupy, catho)
- `status`: Filtra por status (nova, candidatada, entrevista, rejeitada, ignorada)

### Candidaturas
- `status`: Filtra por status (pendente, enviada, entrevista, rejeitada, aceita)
- `platform`: Filtra por plataforma

## 🚦 Status Codes

- `200` - Sucesso
- `201` - Criado com sucesso
- `404` - Não encontrado
- `500` - Erro interno do servidor

## 🧪 Testando a API

### Usando curl
```bash
# Listar vagas
curl http://localhost:8000/api/jobs

# Obter vaga específica
curl http://localhost:8000/api/jobs/1

# Listar candidaturas
curl http://localhost:8000/api/applications

# Obter configurações
curl http://localhost:8000/api/settings
```

### Usando navegador
Acesse diretamente as URLs no navegador para visualizar as respostas JSON.

## 🔄 Integração com Frontend

A API está configurada para funcionar com o frontend Vue.js:

1. **CORS habilitado** para `localhost:5173`
2. **Endpoints RESTful** seguindo convenções
3. **Respostas JSON** estruturadas
4. **Códigos de status HTTP** apropriados

## 📦 Deploy

Para deploy em produção:

1. Configure variáveis de ambiente
2. Use um servidor WSGI (Gunicorn, uWSGI)
3. Configure proxy reverso (Nginx)
4. Implemente autenticação e autorização

```bash
# Exemplo com Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## 🔒 Segurança

Para produção, implemente:

- Autenticação JWT
- Rate limiting
- Validação de entrada
- HTTPS
- Logs de auditoria

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT.

