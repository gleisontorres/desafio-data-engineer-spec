"""
API REST Pokemon - FastAPI.

Expõe os dados processados da pipeline ETL via endpoints REST.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from database import check_database_connection
from routers import pokemon_router

# Configuração do structlog
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(module="main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Gerencia ciclo de vida da aplicação.

    Executa verificações na inicialização e cleanup no shutdown.
    """
    logger.info("api_startup_started")

    # Verifica conexão com banco
    if check_database_connection():
        logger.info("api_startup_database_ok")
    else:
        logger.warning("api_startup_database_unavailable")

    logger.info("api_startup_completed")

    yield

    logger.info("api_shutdown_completed")


# Instância do FastAPI
app = FastAPI(
    title="Pokemon API",
    description="""
API REST para consulta de dados de Pokemon.

## Funcionalidades

- Listagem de Pokemons com paginação
- Busca por nome ou ID
- Filtro por tipo
- Ranking por stats
- Comparação entre Pokemons

## Dados

Os dados são extraídos da PokéAPI e processados por uma pipeline ETL.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Registro de routers
app.include_router(pokemon_router)


@app.get("/health", tags=["Health"])
def health_check() -> dict:
    """
    Endpoint de health check.

    Retorna status da API e conexão com o banco.
    """
    db_ok = check_database_connection()

    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
    }


@app.get("/", tags=["Root"])
def root() -> dict:
    """
    Endpoint raiz.

    Retorna informações básicas da API.
    """
    return {
        "name": "Pokemon API",
        "version": "1.0.0",
        "docs": "/docs",
    }
