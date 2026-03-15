# ===========================================
# Dockerfile - API Service
# FastAPI REST API para dados de Pokemon
# ===========================================

FROM python:3.11-slim

# Metadados da imagem
LABEL maintainer="TOTVS IDEIA"
LABEL description="Pokemon REST API - Data Engineer Challenge"

# Variáveis de ambiente para Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Diretório de trabalho
WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copia e instala dependências Python primeiro (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação
COPY main.py database.py ./
COPY routers/ ./routers/
COPY schemas/ ./schemas/

# Usuário não-root para segurança
RUN useradd --create-home --shell /bin/bash apiuser
USER apiuser

# Porta exposta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Comando de execução
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
