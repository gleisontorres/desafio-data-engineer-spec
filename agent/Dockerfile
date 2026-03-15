# ===========================================
# Dockerfile - Agent Service
# Agente de IA para consultas sobre Pokemon
# ===========================================

FROM python:3.11-slim

# Metadados da imagem
LABEL maintainer="TOTVS IDEIA"
LABEL description="Pokemon AI Agent - Data Engineer Challenge"

# Variáveis de ambiente para Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Diretório de trabalho
WORKDIR /app

# Copia e instala dependências Python primeiro (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação
COPY logger.py tools.py agent_app.py ./

# Usuário não-root para segurança
RUN useradd --create-home --shell /bin/bash agentuser
USER agentuser

# Porta exposta (modo API)
EXPOSE 8001

# Entrypoint flexível para suportar CLI e API
# - Sem argumentos ou --api-mode: inicia API via uvicorn
# - Com texto: executa CLI com a pergunta
#
# Exemplos:
#   docker compose up agent              -> Inicia API na porta 8001
#   docker compose run agent "pergunta"  -> Executa CLI
ENTRYPOINT ["python", "agent_app.py"]
