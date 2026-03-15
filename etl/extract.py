"""
Módulo de extração de dados da PokéAPI.

Responsabilidade: Apenas chamadas HTTP à PokéAPI.
Sem transformação, sem persistência.
"""

import os
import time
from typing import Any

import httpx
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

logger = structlog.get_logger(module="extract")

# Configurações
POKEAPI_BASE_URL = os.getenv("POKEAPI_BASE_URL", "https://pokeapi.co/api/v2")
REQUEST_DELAY_SECONDS = 0.2
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 1.0
REQUEST_TIMEOUT_SECONDS = 30.0


class ExtractionError(Exception):
    """Exceção customizada para erros de extração."""

    pass


def _make_request(url: str, client: httpx.Client) -> dict[str, Any]:
    """
    Realiza uma requisição HTTP com retry e logging.

    Args:
        url: URL completa para a requisição.
        client: Cliente httpx reutilizável.

    Returns:
        Dados JSON da resposta.

    Raises:
        ExtractionError: Se todas as tentativas falharem.
    """
    last_exception: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        start_time = time.perf_counter()

        try:
            response = client.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
            latency_ms = (time.perf_counter() - start_time) * 1000

            logger.info(
                "http_request_completed",
                url=url,
                status_code=response.status_code,
                latency_ms=round(latency_ms, 2),
                attempt=attempt,
            )

            if response.status_code == 200:
                return response.json()

            if response.status_code == 404:
                raise ExtractionError(f"Recurso nao encontrado: {url}")

            raise ExtractionError(
                f"Status inesperado {response.status_code} para {url}"
            )

        except httpx.TimeoutException as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            last_exception = e
            logger.warning(
                "http_request_timeout",
                url=url,
                latency_ms=round(latency_ms, 2),
                attempt=attempt,
                max_retries=MAX_RETRIES,
            )

        except httpx.RequestError as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            last_exception = e
            logger.warning(
                "http_request_error",
                url=url,
                error=str(e),
                latency_ms=round(latency_ms, 2),
                attempt=attempt,
                max_retries=MAX_RETRIES,
            )

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY_SECONDS)

    raise ExtractionError(
        f"Falha apos {MAX_RETRIES} tentativas para {url}: {last_exception}"
    )


def fetch_pokemon(
    pokemon_id: int, client: httpx.Client | None = None
) -> dict[str, Any]:
    """
    Busca dados de um Pokemon pelo ID na PokéAPI.

    Args:
        pokemon_id: ID do Pokemon (1-151 para geração 1).
        client: Cliente httpx opcional (para reutilização de conexão).

    Returns:
        Dicionário com dados brutos do Pokemon contendo:
        - id, name, height, weight, base_experience
        - stats: lista de stats base
        - types: lista de tipos
        - abilities: lista de habilidades

    Raises:
        ExtractionError: Se a requisição falhar.
    """
    url = f"{POKEAPI_BASE_URL}/pokemon/{pokemon_id}"
    should_close_client = client is None

    if client is None:
        client = httpx.Client()

    try:
        data = _make_request(url, client)

        return {
            "id": data["id"],
            "name": data["name"],
            "height": data["height"],
            "weight": data["weight"],
            "base_experience": data.get("base_experience"),
            "stats": [
                {
                    "name": stat["stat"]["name"],
                    "base_stat": stat["base_stat"],
                }
                for stat in data["stats"]
            ],
            "types": [
                {
                    "slot": t["slot"],
                    "type_id": _extract_id_from_url(t["type"]["url"]),
                    "type_name": t["type"]["name"],
                }
                for t in data["types"]
            ],
            "abilities": [
                {
                    "slot": a["slot"],
                    "is_hidden": a["is_hidden"],
                    "ability_id": _extract_id_from_url(a["ability"]["url"]),
                    "ability_name": a["ability"]["name"],
                    "ability_url": a["ability"]["url"],
                }
                for a in data["abilities"]
            ],
        }

    finally:
        if should_close_client:
            client.close()


def fetch_ability_detail(
    ability_url: str, client: httpx.Client | None = None
) -> dict[str, Any]:
    """
    Busca detalhes de uma habilidade pelo URL.

    Args:
        ability_url: URL completa da habilidade na PokéAPI.
        client: Cliente httpx opcional (para reutilização de conexão).

    Returns:
        Dicionário com dados da habilidade:
        - id, name, description (em inglês)

    Raises:
        ExtractionError: Se a requisição falhar.
    """
    should_close_client = client is None

    if client is None:
        client = httpx.Client()

    try:
        data = _make_request(ability_url, client)

        description = _extract_english_description(data.get("effect_entries", []))

        return {
            "id": data["id"],
            "name": data["name"],
            "description": description,
        }

    finally:
        if should_close_client:
            client.close()


def fetch_all_pokemons(limit: int = 151) -> list[dict[str, Any]]:
    """
    Busca dados de múltiplos Pokemons iterando pelos IDs.

    Args:
        limit: Quantidade de Pokemons a buscar (padrão: 151 para geração 1).

    Returns:
        Lista de dicionários com dados brutos de cada Pokemon.

    Raises:
        ExtractionError: Se alguma requisição crítica falhar.
    """
    logger.info(
        "extraction_started",
        limit=limit,
    )

    pokemons: list[dict[str, Any]] = []
    abilities_cache: dict[str, dict[str, Any]] = {}
    start_time = time.perf_counter()

    with httpx.Client() as client:
        for pokemon_id in range(1, limit + 1):
            try:
                pokemon_data = fetch_pokemon(pokemon_id, client)

                # Busca detalhes das habilidades (com cache)
                for ability in pokemon_data["abilities"]:
                    ability_url = ability["ability_url"]

                    if ability_url not in abilities_cache:
                        time.sleep(REQUEST_DELAY_SECONDS)
                        ability_detail = fetch_ability_detail(ability_url, client)
                        abilities_cache[ability_url] = ability_detail

                    ability["description"] = abilities_cache[ability_url]["description"]

                    # Remove URL do retorno final (não necessário para transform)
                    del ability["ability_url"]

                pokemons.append(pokemon_data)

                logger.info(
                    "pokemon_extracted",
                    pokemon_id=pokemon_id,
                    pokemon_name=pokemon_data["name"],
                    progress=f"{pokemon_id}/{limit}",
                )

                time.sleep(REQUEST_DELAY_SECONDS)

            except ExtractionError as e:
                logger.error(
                    "pokemon_extraction_failed",
                    pokemon_id=pokemon_id,
                    error=str(e),
                )
                raise

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    logger.info(
        "extraction_completed",
        total_pokemons=len(pokemons),
        total_abilities_fetched=len(abilities_cache),
        elapsed_ms=round(elapsed_ms, 2),
    )

    return pokemons


def _extract_id_from_url(url: str) -> int:
    """
    Extrai o ID numérico de uma URL da PokéAPI.

    Args:
        url: URL no formato https://pokeapi.co/api/v2/resource/123/

    Returns:
        ID numérico extraído da URL.
    """
    parts = url.rstrip("/").split("/")
    return int(parts[-1])


def _extract_english_description(effect_entries: list[dict[str, Any]]) -> str | None:
    """
    Extrai a descrição em inglês de uma lista de effect_entries.

    Args:
        effect_entries: Lista de entradas de efeito da PokéAPI.

    Returns:
        Descrição em inglês ou None se não encontrada.
    """
    for entry in effect_entries:
        if entry.get("language", {}).get("name") == "en":
            return entry.get("effect")
    return None


if __name__ == "__main__":
    # Permite execução direta para teste
    import json

    result = fetch_all_pokemons(limit=3)
    logger.info("test_extraction_result", count=len(result))
    print(json.dumps(result, indent=2))
