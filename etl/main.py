"""
Orquestrador principal da pipeline ETL.

Executa as 3 etapas em sequência:
1. Extract — busca dados da PokéAPI
2. Transform — limpa e normaliza os dados
3. Load — persiste no PostgreSQL
"""

import os
import sys
import time
from typing import Any

import structlog

from extract import fetch_all_pokemons, ExtractionError
from transform import transform_pokemons, TransformationError
from load import run_load, LoadError

# Configuração do structlog para JSON estruturado
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


def run_pipeline(limit: int = 151) -> dict[str, Any]:
    """
    Executa a pipeline ETL completa.

    Args:
        limit: Quantidade de Pokémon a extrair (padrão: 151 - geração 1).

    Returns:
        Dict com estatísticas de execução:
        - extract_count: quantidade extraída
        - transform_counts: contagens por entidade
        - load_counts: registros persistidos por entidade
        - total_elapsed_ms: tempo total de execução

    Raises:
        ExtractionError: Se falhar na extração.
        TransformationError: Se falhar na transformação.
        LoadError: Se falhar na carga.
    """
    pipeline_start = time.perf_counter()

    logger.info(
        "pipeline_started",
        limit=limit,
    )

    result: dict[str, Any] = {}

    # =========================================
    # ETAPA 1: EXTRACT
    # =========================================
    logger.info("stage_started", stage="extract")
    extract_start = time.perf_counter()

    raw_data = fetch_all_pokemons(limit=limit)

    extract_elapsed_ms = (time.perf_counter() - extract_start) * 1000
    result["extract_count"] = len(raw_data)

    logger.info(
        "stage_completed",
        stage="extract",
        count=len(raw_data),
        elapsed_ms=round(extract_elapsed_ms, 2),
    )

    # =========================================
    # ETAPA 2: TRANSFORM
    # =========================================
    logger.info("stage_started", stage="transform")
    transform_start = time.perf_counter()

    transformed_data = transform_pokemons(raw_data)

    transform_elapsed_ms = (time.perf_counter() - transform_start) * 1000
    result["transform_counts"] = {
        "pokemons": len(transformed_data["pokemons"]),
        "types": len(transformed_data["types"]),
        "abilities": len(transformed_data["abilities"]),
        "stats": len(transformed_data["stats"]),
        "pokemon_types": len(transformed_data["pokemon_types"]),
        "pokemon_abilities": len(transformed_data["pokemon_abilities"]),
    }

    logger.info(
        "stage_completed",
        stage="transform",
        elapsed_ms=round(transform_elapsed_ms, 2),
        **result["transform_counts"],
    )

    # =========================================
    # ETAPA 3: LOAD
    # =========================================
    logger.info("stage_started", stage="load")
    load_start = time.perf_counter()

    load_counts = run_load(transformed_data)

    load_elapsed_ms = (time.perf_counter() - load_start) * 1000
    result["load_counts"] = load_counts

    logger.info(
        "stage_completed",
        stage="load",
        elapsed_ms=round(load_elapsed_ms, 2),
        **load_counts,
    )

    # =========================================
    # RESUMO FINAL
    # =========================================
    total_elapsed_ms = (time.perf_counter() - pipeline_start) * 1000
    result["total_elapsed_ms"] = round(total_elapsed_ms, 2)
    result["stages_elapsed_ms"] = {
        "extract": round(extract_elapsed_ms, 2),
        "transform": round(transform_elapsed_ms, 2),
        "load": round(load_elapsed_ms, 2),
    }

    logger.info(
        "pipeline_completed",
        total_elapsed_ms=result["total_elapsed_ms"],
        extract_count=result["extract_count"],
        pokemons_loaded=result["load_counts"]["pokemons"],
        types_loaded=result["load_counts"]["types"],
        abilities_loaded=result["load_counts"]["abilities"],
    )

    return result


def main() -> int:
    """
    Entry point da pipeline.

    Lê configurações de variáveis de ambiente e executa a pipeline.

    Returns:
        Código de saída (0 = sucesso, 1 = erro).
    """
    try:
        # Permite configurar limite via variável de ambiente
        limit = int(os.getenv("POKEMON_LIMIT", "151"))

        logger.info(
            "etl_main_started",
            pokemon_limit=limit,
        )

        result = run_pipeline(limit=limit)

        logger.info(
            "etl_main_completed",
            total_elapsed_ms=result["total_elapsed_ms"],
        )

        return 0

    except ExtractionError as e:
        logger.error(
            "etl_main_failed",
            stage="extract",
            error=str(e),
        )
        return 1

    except TransformationError as e:
        logger.error(
            "etl_main_failed",
            stage="transform",
            error=str(e),
        )
        return 1

    except LoadError as e:
        logger.error(
            "etl_main_failed",
            stage="load",
            error=str(e),
        )
        return 1

    except Exception as e:
        logger.error(
            "etl_main_failed",
            stage="unknown",
            error=str(e),
            error_type=type(e).__name__,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
