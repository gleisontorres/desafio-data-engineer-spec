"""
Módulo de logging para o Agente de IA.

Configura structlog com output JSON e funções auxiliares para logging de tool calls.
"""

from typing import Any

import structlog

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


def get_logger(module: str) -> structlog.BoundLogger:
    """
    Retorna um logger configurado para o módulo especificado.

    Args:
        module: Nome do módulo para identificação no log.

    Returns:
        Logger structlog configurado.
    """
    return structlog.get_logger(module=module)


def log_tool_call(
    logger: structlog.BoundLogger,
    tool_name: str,
    params: dict[str, Any],
    result: dict[str, Any] | None,
    latency_ms: float,
    status: str,
) -> None:
    """
    Loga a execução de uma tool do agente.

    Args:
        logger: Logger structlog a ser usado.
        tool_name: Nome da tool executada.
        params: Parâmetros passados para a tool.
        result: Resultado da execução (pode ser None em caso de erro).
        latency_ms: Tempo de execução em milissegundos.
        status: Status da execução ("success" ou "error").
    """
    logger.info(
        "tool_call_executed",
        tool_name=tool_name,
        params=params,
        latency_ms=round(latency_ms, 2),
        status=status,
        has_result=result is not None,
    )
