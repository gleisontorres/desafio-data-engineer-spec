# ===========================================
# Dockerfile - UI Service
# Interface Web Streamlit para o Pokemon Data Explorer
# ===========================================

FROM python:3.11-slim

# Metadados da imagem
LABEL maintainer="TOTVS IDEIA"
LABEL description="Pokemon Data Explorer UI - Streamlit Interface"

# Variaveis de ambiente para Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Diretorio de trabalho
WORKDIR /app

# Copia e instala dependencias Python primeiro (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia codigo da aplicacao e assets
COPY streamlit_app.py .
COPY assets/ ./assets/

# Usuario nao-root para seguranca
RUN useradd --create-home --shell /bin/bash uiuser
USER uiuser

# Porta exposta (padrao Streamlit)
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

# Comando de execucao
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
