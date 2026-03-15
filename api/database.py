"""
Módulo de conexão com o banco de dados PostgreSQL.

Configura SQLAlchemy para uso com FastAPI dependency injection.
"""

import os
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
import structlog

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

logger = structlog.get_logger(module="database")


def get_database_url() -> str:
    """
    Constrói a URL de conexão com o banco a partir de variáveis de ambiente.

    Returns:
        URL de conexão no formato postgresql://user:pass@host:port/db
    """
    user = os.getenv("POSTGRES_USER", "pokemon_user")
    password = os.getenv("POSTGRES_PASSWORD", "")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "pokemon_db")

    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


# Engine SQLAlchemy
DATABASE_URL = get_database_url()
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection para obter sessão do banco.

    Uso no FastAPI:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...

    Yields:
        Sessão SQLAlchemy ativa.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> bool:
    """
    Verifica se a conexão com o banco está funcionando.

    Returns:
        True se conectou com sucesso, False caso contrário.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("database_connection_check_success")
        return True
    except Exception as e:
        logger.error(
            "database_connection_check_failed",
            error=str(e),
        )
        return False
