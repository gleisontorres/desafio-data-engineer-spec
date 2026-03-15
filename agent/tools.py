"""
Tools do Agente de IA para consulta de dados de Pokemon.

Cada tool consulta a API REST e retorna dados estruturados.
Todas as tools tratam erros e retornam mensagens amigáveis.
"""

import os
import time
from typing import Any

import httpx

from logger import get_logger, log_tool_call

logger = get_logger("tools")

# URL base da API REST
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

# Stats válidos para consulta
VALID_STATS = {"hp", "attack", "defense", "special_attack", "special_defense", "speed"}

# Timeout para requisições HTTP
REQUEST_TIMEOUT = 30.0


def _make_api_request(
    endpoint: str,
    params: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, int, str | None]:
    """
    Faz uma requisição à API REST.

    Args:
        endpoint: Endpoint da API (ex: "/pokemons/pikachu").
        params: Query params opcionais.

    Returns:
        Tupla com (dados, status_code, mensagem_erro).
    """
    url = f"{API_BASE_URL}{endpoint}"

    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.get(url, params=params)

            if response.status_code == 200:
                return response.json(), 200, None
            elif response.status_code == 404:
                return None, 404, "Recurso nao encontrado"
            elif response.status_code == 400:
                detail = response.json().get("detail", "Requisicao invalida")
                return None, 400, detail
            else:
                return None, response.status_code, f"Erro HTTP {response.status_code}"

    except httpx.TimeoutException:
        return None, 0, "Timeout na requisicao"
    except httpx.RequestError as e:
        return None, 0, f"Erro de conexao: {str(e)}"


def buscar_pokemon(nome_ou_id: str) -> dict[str, Any]:
    """
    Busca informacoes detalhadas de um Pokemon pelo nome ou ID.

    Use esta ferramenta quando o usuario perguntar sobre um Pokemon especifico,
    querendo saber seus stats, tipos, habilidades ou outras caracteristicas.

    Args:
        nome_ou_id: Nome do Pokemon (ex: "pikachu") ou ID numerico (ex: "25").

    Returns:
        Dicionario com informacoes completas do Pokemon incluindo:
        - id, name, height, weight, base_experience
        - stats (hp, attack, defense, special_attack, special_defense, speed)
        - types (lista de tipos)
        - abilities (lista de habilidades)
        Ou mensagem de erro se o Pokemon nao for encontrado.
    """
    start_time = time.perf_counter()
    params = {"nome_ou_id": nome_ou_id}

    data, status_code, error = _make_api_request(f"/pokemons/{nome_ou_id}")

    latency_ms = (time.perf_counter() - start_time) * 1000

    if data:
        log_tool_call(logger, "buscar_pokemon", params, data, latency_ms, "success")
        return {
            "status": "success",
            "pokemon": data,
        }
    else:
        result = {
            "status": "error",
            "message": f"Pokemon '{nome_ou_id}' nao encontrado"
            if status_code == 404
            else error,
        }
        log_tool_call(logger, "buscar_pokemon", params, result, latency_ms, "error")
        return result


def listar_por_tipo(tipo: str) -> dict[str, Any]:
    """
    Lista todos os Pokemons de um tipo especifico.

    Use esta ferramenta quando o usuario perguntar quais Pokemons sao de um
    determinado tipo (ex: "quais Pokemons sao do tipo fogo?").

    Args:
        tipo: Nome do tipo em ingles (ex: "fire", "water", "electric", "grass").

    Returns:
        Dicionario com lista de Pokemons do tipo especificado.
        Cada Pokemon inclui id, name, height, weight e lista de tipos.
        Ou mensagem de erro se o tipo nao existir.
    """
    start_time = time.perf_counter()
    params = {"tipo": tipo}

    data, status_code, error = _make_api_request(f"/pokemons/type/{tipo}")

    latency_ms = (time.perf_counter() - start_time) * 1000

    if data:
        log_tool_call(
            logger,
            "listar_por_tipo",
            params,
            {"count": len(data.get("items", []))},
            latency_ms,
            "success",
        )
        return {
            "status": "success",
            "tipo": tipo,
            "total": data.get("total", 0),
            "pokemons": data.get("items", []),
        }
    else:
        result = {
            "status": "error",
            "message": f"Tipo '{tipo}' nao encontrado" if status_code == 404 else error,
        }
        log_tool_call(logger, "listar_por_tipo", params, result, latency_ms, "error")
        return result


def top_n_por_stat(stat: str, n: int = 10) -> dict[str, Any]:
    """
    Retorna o ranking dos Pokemons com os maiores valores em um stat especifico.

    Use esta ferramenta quando o usuario perguntar sobre os Pokemons mais fortes,
    mais rapidos, com mais HP, etc. Os stats disponiveis sao:
    - hp: pontos de vida
    - attack: ataque fisico
    - defense: defesa fisica
    - special_attack: ataque especial
    - special_defense: defesa especial
    - speed: velocidade

    Args:
        stat: Nome do stat (hp, attack, defense, special_attack, special_defense, speed).
        n: Quantidade de Pokemons no ranking (padrao: 10, maximo: 50).

    Returns:
        Dicionario com lista ordenada dos Pokemons com maiores valores no stat.
        Cada item inclui rank, id, name, stat_name e stat_value.
        Ou mensagem de erro se o stat for invalido.
    """
    start_time = time.perf_counter()
    params = {"stat": stat, "n": n}

    # Validação do stat antes de chamar a API
    if stat not in VALID_STATS:
        result = {
            "status": "error",
            "message": f"Stat '{stat}' invalido. Stats validos: {', '.join(sorted(VALID_STATS))}",
        }
        latency_ms = (time.perf_counter() - start_time) * 1000
        log_tool_call(logger, "top_n_por_stat", params, result, latency_ms, "error")
        return result

    # Limita n para evitar sobrecarga
    n = min(max(1, n), 50)

    data, status_code, error = _make_api_request(
        "/pokemons/stats/top",
        params={"stat": stat, "limit": n},
    )

    latency_ms = (time.perf_counter() - start_time) * 1000

    if data:
        log_tool_call(
            logger,
            "top_n_por_stat",
            params,
            {"count": len(data.get("items", []))},
            latency_ms,
            "success",
        )
        return {
            "status": "success",
            "stat": stat,
            "ranking": data.get("items", []),
        }
    else:
        result = {
            "status": "error",
            "message": error or "Erro ao buscar ranking",
        }
        log_tool_call(logger, "top_n_por_stat", params, result, latency_ms, "error")
        return result


def comparar_pokemons(pokemon_a: str, pokemon_b: str) -> dict[str, Any]:
    """
    Compara dois Pokemons lado a lado, mostrando stats e qual e superior em cada categoria.

    Use esta ferramenta quando o usuario quiser comparar dois Pokemons especificos
    (ex: "quem e mais forte, Pikachu ou Raichu?", "compare Charizard com Blastoise").

    Args:
        pokemon_a: Nome ou ID do primeiro Pokemon.
        pokemon_b: Nome ou ID do segundo Pokemon.

    Returns:
        Dicionario com comparacao detalhada incluindo:
        - pokemon_a: dados completos do primeiro Pokemon
        - pokemon_b: dados completos do segundo Pokemon
        - stat_comparison: comparacao stat a stat com vencedor de cada
        - summary: resumo de quem vence em mais categorias
        Ou mensagem de erro se algum Pokemon nao for encontrado.
    """
    start_time = time.perf_counter()
    params = {"pokemon_a": pokemon_a, "pokemon_b": pokemon_b}

    data, status_code, error = _make_api_request(
        "/pokemons/compare",
        params={"pokemon_a": pokemon_a, "pokemon_b": pokemon_b},
    )

    latency_ms = (time.perf_counter() - start_time) * 1000

    if data:
        log_tool_call(
            logger,
            "comparar_pokemons",
            params,
            {"summary": data.get("summary")},
            latency_ms,
            "success",
        )
        return {
            "status": "success",
            "pokemon_a": data.get("pokemon_a"),
            "pokemon_b": data.get("pokemon_b"),
            "comparacao": data.get("stat_comparison", []),
            "resumo": data.get("summary", ""),
        }
    else:
        # Identifica qual Pokemon não foi encontrado
        if status_code == 404:
            message = f"Um ou ambos os Pokemons nao foram encontrados: {pokemon_a}, {pokemon_b}"
        else:
            message = error or "Erro ao comparar Pokemons"

        result = {
            "status": "error",
            "message": message,
        }
        log_tool_call(logger, "comparar_pokemons", params, result, latency_ms, "error")
        return result


# Lista de tools para exportação
TOOLS = [
    buscar_pokemon,
    listar_por_tipo,
    top_n_por_stat,
    comparar_pokemons,
]
