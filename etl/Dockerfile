# ===========================================
# Dockerfile - ETL Service
# Pipeline de extração, transformação e carga
# ===========================================

FROM python:3.11-slim

# Metadados da imagem
LABEL maintainer="TOTVS IDEIA"
LABEL description="ETL Pipeline - Pokemon Data Engineer Challenge"

# Variáveis de ambiente para Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Diretório de trabalho
WORKDIR /app

# Instala dependências do sistema necessárias para psycopg2
# (mesmo usando psycopg2-binary, algumas dependências podem ser necessárias)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copia e instala dependências Python primeiro
# (cache layer - só reinstala se requirements.txt mudar)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia os módulos ETL
COPY extract.py transform.py load.py main.py ./

# Usuário não-root para segurança
RUN useradd --create-home --shell /bin/bash etluser
USER etluser

# Comando padrão: executa a pipeline
ENTRYPOINT ["python", "main.py"]
