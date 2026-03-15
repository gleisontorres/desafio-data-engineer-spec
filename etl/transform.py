"""
Módulo de transformação de dados da pipeline ETL.

Responsabilidade: Apenas limpeza e transformação dos dados brutos.
Sem chamadas HTTP, sem acesso ao banco.
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

logger = structlog.get_logger(module="transform")

# Constantes para normalização
STAT_MAX_VALUE = 255
DEFAULT_BASE_EXPERIENCE = 0

# Mapeamento de nomes de stats da API para nomes das colunas do banco
STAT_NAME_MAPPING = {
    "hp": "hp",
    "attack": "attack",
    "defense": "defense",
    "special-attack": "special_attack",
    "special-defense": "special_defense",
    "speed": "speed",
}


class TransformationError(Exception):
    """Exceção customizada para erros de transformação."""

    pass


def normalize_stat(value: int, max_value: int = STAT_MAX_VALUE) -> float:
    """
    Normaliza um valor de stat para escala 0-1.

    Útil para comparações relativas entre Pokémon no agente de IA.

    Args:
        value: Valor do stat (0-255 tipicamente).
        max_value: Valor máximo para normalização (padrão: 255).

    Returns:
        Valor normalizado entre 0.0 e 1.0.

    Examples:
        >>> normalize_stat(0)
        0.0
        >>> normalize_stat(255)
        1.0
        >>> normalize_stat(127)
        0.498
    """
    if max_value <= 0:
        return 0.0

    if value < 0:
        value = 0

    if value > max_value:
        value = max_value

    return round(value / max_value, 3)


def _safe_int(value: Any, default: int = 0) -> int:
    """
    Converte valor para inteiro de forma segura.

    Args:
        value: Valor a converter.
        default: Valor padrão se conversão falhar.

    Returns:
        Valor inteiro ou default.
    """
    if value is None:
        return default

    try:
        return int(value)
    except (ValueError, TypeError):
        # Tenta converter via float (para strings como "60.5")
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return default


def _safe_str(value: Any, default: str = "") -> str:
    """
    Converte valor para string de forma segura.

    Args:
        value: Valor a converter.
        default: Valor padrão se conversão falhar.

    Returns:
        Valor string ou default.
    """
    if value is None:
        return default

    try:
        return str(value).strip()
    except (ValueError, TypeError):
        return default


def _safe_bool(value: Any, default: bool = False) -> bool:
    """
    Converte valor para boolean de forma segura.

    Args:
        value: Valor a converter.
        default: Valor padrão se conversão falhar.

    Returns:
        Valor boolean ou default.
    """
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")

    try:
        return bool(value)
    except (ValueError, TypeError):
        return default


def clean_pokemon(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Limpa e valida dados de um Pokémon individual.

    Trata campos nulos, garante tipos corretos e aplica valores padrão.

    Args:
        raw: Dicionário com dados brutos do Pokémon (do extract.py).

    Returns:
        Dicionário limpo com estrutura garantida:
        - id: int
        - name: str
        - height: int
        - weight: int
        - base_experience: int
        - stats: dict com hp, attack, defense, special_attack, special_defense, speed
        - stats_normalized: dict com os mesmos stats normalizados (0-1)
        - types: list de dicts com type_id, type_name, slot
        - abilities: list de dicts com ability_id, ability_name, description, is_hidden, slot
    """
    pokemon_id = _safe_int(raw.get("id"))
    name = _safe_str(raw.get("name"))

    if pokemon_id <= 0 or not name:
        raise TransformationError(f"Pokemon invalido: id={pokemon_id}, name={name}")

    # Processa stats
    raw_stats = raw.get("stats", [])
    stats = {}
    stats_normalized = {}

    for stat in raw_stats:
        stat_name = _safe_str(stat.get("name"))
        base_stat = _safe_int(stat.get("base_stat"))

        if stat_name in STAT_NAME_MAPPING:
            column_name = STAT_NAME_MAPPING[stat_name]
            stats[column_name] = base_stat
            stats_normalized[column_name] = normalize_stat(base_stat)

    # Garante que todos os stats existam
    for column_name in STAT_NAME_MAPPING.values():
        if column_name not in stats:
            stats[column_name] = 0
            stats_normalized[column_name] = 0.0

    # Processa types
    raw_types = raw.get("types", [])
    types = [
        {
            "type_id": _safe_int(t.get("type_id")),
            "type_name": _safe_str(t.get("type_name")),
            "slot": _safe_int(t.get("slot"), default=1),
        }
        for t in raw_types
        if _safe_int(t.get("type_id")) > 0
    ]

    # Processa abilities
    raw_abilities = raw.get("abilities", [])
    abilities = [
        {
            "ability_id": _safe_int(a.get("ability_id")),
            "ability_name": _safe_str(a.get("ability_name")),
            "description": _safe_str(a.get("description")),
            "is_hidden": _safe_bool(a.get("is_hidden")),
            "slot": _safe_int(a.get("slot"), default=1),
        }
        for a in raw_abilities
        if _safe_int(a.get("ability_id")) > 0
    ]

    return {
        "id": pokemon_id,
        "name": name,
        "height": _safe_int(raw.get("height")),
        "weight": _safe_int(raw.get("weight")),
        "base_experience": _safe_int(
            raw.get("base_experience"), DEFAULT_BASE_EXPERIENCE
        ),
        "stats": stats,
        "stats_normalized": stats_normalized,
        "types": types,
        "abilities": abilities,
    }


def transform_pokemons(
    raw_list: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """
    Transforma lista bruta de Pokémon em estruturas prontas para o banco.

    Args:
        raw_list: Lista de dicts retornados por fetch_all_pokemons().

    Returns:
        Dicionário com 6 listas separadas:
        - pokemons: dados base de cada Pokémon
        - types: tipos únicos (sem duplicatas)
        - pokemon_types: relações N:N entre pokemon e types
        - stats: estatísticas de cada Pokémon
        - abilities: habilidades únicas (sem duplicatas)
        - pokemon_abilities: relações N:N entre pokemon e abilities
    """
    logger.info(
        "transformation_started",
        input_count=len(raw_list),
    )

    pokemons: list[dict[str, Any]] = []
    stats_list: list[dict[str, Any]] = []
    pokemon_types: list[dict[str, Any]] = []
    pokemon_abilities: list[dict[str, Any]] = []

    # Sets para deduplicação (usando id como chave)
    types_map: dict[int, dict[str, Any]] = {}
    abilities_map: dict[int, dict[str, Any]] = {}

    errors_count = 0

    for raw in raw_list:
        try:
            cleaned = clean_pokemon(raw)

            # Dados base do Pokémon
            pokemons.append(
                {
                    "id": cleaned["id"],
                    "name": cleaned["name"],
                    "height": cleaned["height"],
                    "weight": cleaned["weight"],
                    "base_experience": cleaned["base_experience"],
                }
            )

            # Stats do Pokémon
            stats_list.append(
                {
                    "pokemon_id": cleaned["id"],
                    **cleaned["stats"],
                }
            )

            # Types (coleta únicos e cria relações)
            for t in cleaned["types"]:
                type_id = t["type_id"]

                if type_id not in types_map:
                    types_map[type_id] = {
                        "id": type_id,
                        "name": t["type_name"],
                    }

                pokemon_types.append(
                    {
                        "pokemon_id": cleaned["id"],
                        "type_id": type_id,
                        "slot": t["slot"],
                    }
                )

            # Abilities (coleta únicas e cria relações)
            for a in cleaned["abilities"]:
                ability_id = a["ability_id"]

                if ability_id not in abilities_map:
                    abilities_map[ability_id] = {
                        "id": ability_id,
                        "name": a["ability_name"],
                        "description": a["description"],
                    }

                pokemon_abilities.append(
                    {
                        "pokemon_id": cleaned["id"],
                        "ability_id": ability_id,
                        "is_hidden": a["is_hidden"],
                        "slot": a["slot"],
                    }
                )

        except TransformationError as e:
            errors_count += 1
            logger.warning(
                "pokemon_transformation_skipped",
                error=str(e),
                raw_id=raw.get("id"),
            )

    # Converte maps para listas ordenadas por id
    types_list = sorted(types_map.values(), key=lambda x: x["id"])
    abilities_list = sorted(abilities_map.values(), key=lambda x: x["id"])

    result = {
        "pokemons": pokemons,
        "types": types_list,
        "pokemon_types": pokemon_types,
        "stats": stats_list,
        "abilities": abilities_list,
        "pokemon_abilities": pokemon_abilities,
    }

    logger.info(
        "transformation_completed",
        pokemons_count=len(pokemons),
        types_count=len(types_list),
        pokemon_types_count=len(pokemon_types),
        stats_count=len(stats_list),
        abilities_count=len(abilities_list),
        pokemon_abilities_count=len(pokemon_abilities),
        errors_count=errors_count,
    )

    return result


if __name__ == "__main__":
    # Permite execução direta para teste
    import json

    sample_data = [
        {
            "id": 25,
            "name": "pikachu",
            "height": 4,
            "weight": 60,
            "base_experience": 112,
            "stats": [
                {"name": "hp", "base_stat": 35},
                {"name": "attack", "base_stat": 55},
                {"name": "defense", "base_stat": 40},
                {"name": "special-attack", "base_stat": 50},
                {"name": "special-defense", "base_stat": 50},
                {"name": "speed", "base_stat": 90},
            ],
            "types": [
                {"slot": 1, "type_id": 13, "type_name": "electric"},
            ],
            "abilities": [
                {
                    "slot": 1,
                    "is_hidden": False,
                    "ability_id": 9,
                    "ability_name": "static",
                    "description": "Has a 30% chance of paralyzing attacking Pokemon on contact.",
                },
                {
                    "slot": 3,
                    "is_hidden": True,
                    "ability_id": 31,
                    "ability_name": "lightning-rod",
                    "description": "Draws in all Electric-type moves to up Special Attack one stage.",
                },
            ],
        },
    ]

    result = transform_pokemons(sample_data)
    print(json.dumps(result, indent=2))
