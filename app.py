"""
API Flask simplificada para integração com o frontend Vue.js
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import json

app = Flask(__name__)
CORS(app)  # Permitir CORS para todas as rotas

# Dados mock para demonstração
mock_jobs = [
    {
        "id": "1",
        "title": "Desenvolvedor Python Júnior",
        "company": "TechCorp",
        "location": "São Paulo, SP",
        "type": "Remoto",
        "level": "Júnior",
        "compatibility": 85,
        "description": "Vaga para desenvolvedor Python júnior com experiência em Django e FastAPI.",
        "skills": ["Python", "Backend", "Remote"],
        "platform": "LinkedIn",
        "posted_date": "2025-07-13",
        "salary_range": "R$ 4.000 - R$ 6.000",
        "status": "nova"
    },
    {
        "id": "2",
        "title": "Desenvolvedor TypeScript",
        "company": "StartupXYZ",
        "location": "Rio de Janeiro, RJ",
        "type": "Remoto",
        "level": "Pleno",
        "compatibility": 92,
        "description": "Desenvolvedor TypeScript para trabalhar com Vue.js e Node.js.",
        "skills": ["TypeScript", "Frontend", "Remote"],
        "platform": "Gupy",
        "posted_date": "2025-07-12",
        "salary_range": "R$ 6.000 - R$ 8.000",
        "status": "candidatada"
    },
    {
        "id": "3",
        "title": "Assistente Administrativo Remoto",
        "company": "AdminCorp",
        "location": "Belo Horizonte, MG",
        "type": "Remoto",
        "level": "Júnior",
        "compatibility": 78,
        "description": "Assistente administrativo para trabalho 100% remoto.",
        "skills": ["Administrativo", "Remote"],
        "platform": "Catho",
        "posted_date": "2025-07-11",
        "salary_range": "R$ 2.500 - R$ 3.500",
        "status": "entrevista"
    }
]

mock_applications = [
    {
        "id": "1",
        "job_id": "1",
        "job_title": "Desenvolvedor Python Júnior",
        "company": "TechCorp",
        "platform": "LinkedIn",
        "status": "Enviada",
        "applied_date": "2025-07-13T10:30:00",
        "documents": {
            "cv": True,
            "cover_letter": True,
            "questionnaire": True
        }
    },
    {
        "id": "2",
        "job_id": "2",
        "job_title": "Desenvolvedor TypeScript",
        "company": "StartupXYZ",
        "platform": "Gupy",
        "status": "Entrevista",
        "applied_date": "2025-07-12T14:20:00",
        "documents": {
            "cv": True,
            "cover_letter": True,
            "questionnaire": False
        }
    },
    {
        "id": "3",
        "job_id": "3",
        "job_title": "Assistente Administrativo Remoto",
        "company": "AdminCorp",
        "platform": "Catho",
        "status": "Pendente",
        "applied_date": "2025-07-11T09:15:00",
        "documents": {
            "cv": True,
            "cover_letter": False,
            "questionnaire": False
        }
    }
]

mock_settings = {
    "profile": {
        "fullName": "",
        "email": "",
        "phone": "",
        "linkedin": "",
        "jobAreas": [],
        "experienceLevel": "junior",
        "workMode": "remote",
        "keywords": ""
    },
    "automation": {
        "autoSearch": True,
        "autoApply": False,
        "minCompatibility": 80,
        "searchSchedule": "daily",
        "maxApplicationsPerDay": 10
    },
    "platforms": [
        {
            "name": "LinkedIn",
            "connected": False,
            "credentials": {"email": "", "password": ""}
        },
        {
            "name": "Gupy",
            "connected": False,
            "credentials": {"email": "", "password": ""}
        },
        {
            "name": "Catho",
            "connected": False,
            "credentials": {"email": "", "password": ""}
        }
    ],
    "apiSettings": {
        "openaiKey": "",
        "telegramToken": "",
        "telegramChatId": ""
    },
    "notifications": {
        "newJobs": True,
        "applications": True,
        "errors": True,
        "dailySummary": False
    }
}

# Rotas da API

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Retorna lista de vagas"""
    platform = request.args.get('platform')
    status = request.args.get('status')
    
    jobs = mock_jobs.copy()
    
    if platform and platform != 'all':
        jobs = [job for job in jobs if job['platform'].lower() == platform.lower()]
    
    if status and status != 'all':
        jobs = [job for job in jobs if job['status'] == status]
    
    return jsonify(jobs)

@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    """Retorna uma vaga específica"""
    job = next((job for job in mock_jobs if job['id'] == job_id), None)
    if job:
        return jsonify(job)
    return jsonify({"error": "Job not found"}), 404

@app.route('/api/jobs/search', methods=['POST'])
def search_jobs():
    """Inicia busca por novas vagas"""
    return jsonify({"message": "Busca iniciada", "status": "success"})

@app.route('/api/jobs/<job_id>/analyze', methods=['POST'])
def analyze_job(job_id):
    """Analisa compatibilidade de uma vaga"""
    job = next((job for job in mock_jobs if job['id'] == job_id), None)
    if job:
        return jsonify({
            "compatibility": job['compatibility'],
            "analysis": "Análise de compatibilidade baseada no perfil do usuário"
        })
    return jsonify({"error": "Job not found"}), 404

@app.route('/api/applications', methods=['GET'])
def get_applications():
    """Retorna lista de candidaturas"""
    status = request.args.get('status')
    platform = request.args.get('platform')
    
    applications = mock_applications.copy()
    
    if status and status != 'all':
        applications = [app for app in applications if app['status'].lower() == status.lower()]
    
    if platform and platform != 'all':
        applications = [app for app in applications if app['platform'].lower() == platform.lower()]
    
    return jsonify(applications)

@app.route('/api/applications/<app_id>', methods=['GET'])
def get_application(app_id):
    """Retorna uma candidatura específica"""
    application = next((app for app in mock_applications if app['id'] == app_id), None)
    if application:
        return jsonify(application)
    return jsonify({"error": "Application not found"}), 404

@app.route('/api/applications', methods=['POST'])
def create_application():
    """Cria uma nova candidatura"""
    data = request.get_json()
    new_app = {
        "id": str(len(mock_applications) + 1),
        "job_id": data.get('job_id'),
        "job_title": data.get('job_title'),
        "company": data.get('company'),
        "platform": data.get('platform'),
        "status": "Pendente",
        "applied_date": datetime.now().isoformat(),
        "documents": {
            "cv": False,
            "cover_letter": False,
            "questionnaire": False
        }
    }
    mock_applications.append(new_app)
    return jsonify(new_app), 201

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Retorna configurações do sistema"""
    return jsonify(mock_settings)

@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Atualiza configurações do sistema"""
    data = request.get_json()
    mock_settings.update(data)
    return jsonify({"message": "Settings updated successfully"})

@app.route('/api/settings/test_connection', methods=['POST'])
def test_connection():
    """Testa conexão com uma plataforma"""
    data = request.get_json()
    service = data.get('service')
    return jsonify({
        "service": service,
        "status": "success",
        "message": f"Conexão com {service} testada com sucesso"
    })

@app.route('/api/settings/system_info', methods=['GET'])
def get_system_info():
    """Retorna informações do sistema"""
    return jsonify({
        "version": "1.0.0",
        "status": "running",
        "uptime": "2 days, 3 hours",
        "last_search": "2025-07-13T15:30:00",
        "total_jobs": len(mock_jobs),
        "total_applications": len(mock_applications)
    })

@app.route('/api/analytics/stats', methods=['GET'])
def get_analytics_stats():
    """Retorna estatísticas para analytics"""
    return jsonify({
        "jobs_collected": 1247,
        "applications_sent": 89,
        "interviews": 12,
        "success_rate": 13.5,
        "platforms": [
            {"name": "LinkedIn", "jobs": 456, "applications": 34, "conversion": 7.5, "interviews": 5},
            {"name": "Gupy", "jobs": 321, "applications": 28, "conversion": 8.7, "interviews": 4},
            {"name": "Catho", "jobs": 287, "applications": 19, "conversion": 6.6, "interviews": 2},
            {"name": "Himalayas", "jobs": 183, "applications": 8, "conversion": 4.4, "interviews": 1}
        ],
        "ai_performance": {
            "compatibility_accuracy": 87.3,
            "resumes_generated": 89,
            "questionnaires_answered": 156
        }
    })

@app.route('/', methods=['GET'])
def root():
    """Rota raiz da API"""
    return jsonify({
        "message": "Job Automation API",
        "version": "1.0.0",
        "status": "running"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

