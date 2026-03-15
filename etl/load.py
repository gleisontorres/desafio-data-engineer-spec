"""
Módulo de carga de dados no PostgreSQL.

Responsabilidade: Apenas persistência no banco de dados.
Sem lógica de negócio, sem transformação.
"""

import os
from typing import Any

import psycopg2
from psycopg2.extensions import connection as PgConnection
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

logger = structlog.get_logger(module="load")


class LoadError(Exception):
    """Exceção customizada para erros de carga."""

    pass


def get_connection() -> PgConnection:
    """
    Cria e retorna uma conexão com o PostgreSQL.

    Usa variáveis de ambiente para configuração.
    Nunca hardcoda credenciais.

    Returns:
        Conexão psycopg2 ativa.

    Raises:
        LoadError: Se não conseguir conectar ao banco.
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "pokemon_db"),
            user=os.getenv("POSTGRES_USER", "pokemon_user"),
            password=os.getenv("POSTGRES_PASSWORD", ""),
        )
        conn.autocommit = False
        logger.info("database_connection_established")
        return conn

    except psycopg2.Error as e:
        logger.error(
            "database_connection_failed",
            error=str(e),
        )
        raise LoadError(f"Falha ao conectar ao banco: {e}") from e


def upsert_pokemons(conn: PgConnection, pokemons: list[dict[str, Any]]) -> int:
    """
    Insere ou atualiza registros na tabela pokemon.

    Usa INSERT ... ON CONFLICT DO UPDATE para idempotência.

    Args:
        conn: Conexão psycopg2 ativa.
        pokemons: Lista de dicts com dados dos Pokémon.

    Returns:
        Quantidade de registros processados.
    """
    if not pokemons:
        logger.info("upsert_pokemons_skipped", reason="empty_list")
        return 0

    query = """
        INSERT INTO pokemon (id, name, height, weight, base_experience)
        VALUES (%(id)s, %(name)s, %(height)s, %(weight)s, %(base_experience)s)
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            height = EXCLUDED.height,
            weight = EXCLUDED.weight,
            base_experience = EXCLUDED.base_experience,
            updated_at = NOW()
    """

    with conn.cursor() as cursor:
        cursor.executemany(query, pokemons)

    logger.info(
        "upsert_pokemons_completed",
        count=len(pokemons),
    )

    return len(pokemons)


def upsert_types(conn: PgConnection, types: list[dict[str, Any]]) -> int:
    """
    Insere ou atualiza registros na tabela types.

    Usa INSERT ... ON CONFLICT DO UPDATE para idempotência.

    Args:
        conn: Conexão psycopg2 ativa.
        types: Lista de dicts com dados dos tipos.

    Returns:
        Quantidade de registros processados.
    """
    if not types:
        logger.info("upsert_types_skipped", reason="empty_list")
        return 0

    query = """
        INSERT INTO types (id, name)
        VALUES (%(id)s, %(name)s)
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            updated_at = NOW()
    """

    with conn.cursor() as cursor:
        cursor.executemany(query, types)

    logger.info(
        "upsert_types_completed",
        count=len(types),
    )

    return len(types)


def upsert_abilities(conn: PgConnection, abilities: list[dict[str, Any]]) -> int:
    """
    Insere ou atualiza registros na tabela abilities.

    Usa INSERT ... ON CONFLICT DO UPDATE para idempotência.

    Args:
        conn: Conexão psycopg2 ativa.
        abilities: Lista de dicts com dados das habilidades.

    Returns:
        Quantidade de registros processados.
    """
    if not abilities:
        logger.info("upsert_abilities_skipped", reason="empty_list")
        return 0

    query = """
        INSERT INTO abilities (id, name, description)
        VALUES (%(id)s, %(name)s, %(description)s)
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            description = EXCLUDED.description,
            updated_at = NOW()
    """

    with conn.cursor() as cursor:
        cursor.executemany(query, abilities)

    logger.info(
        "upsert_abilities_completed",
        count=len(abilities),
    )

    return len(abilities)


def upsert_stats(conn: PgConnection, stats: list[dict[str, Any]]) -> int:
    """
    Insere ou atualiza registros na tabela stats.

    Usa INSERT ... ON CONFLICT DO UPDATE para idempotência.

    Args:
        conn: Conexão psycopg2 ativa.
        stats: Lista de dicts com stats dos Pokémon.

    Returns:
        Quantidade de registros processados.
    """
    if not stats:
        logger.info("upsert_stats_skipped", reason="empty_list")
        return 0

    query = """
        INSERT INTO stats (pokemon_id, hp, attack, defense, special_attack, special_defense, speed)
        VALUES (%(pokemon_id)s, %(hp)s, %(attack)s, %(defense)s, %(special_attack)s, %(special_defense)s, %(speed)s)
        ON CONFLICT (pokemon_id) DO UPDATE SET
            hp = EXCLUDED.hp,
            attack = EXCLUDED.attack,
            defense = EXCLUDED.defense,
            special_attack = EXCLUDED.special_attack,
            special_defense = EXCLUDED.special_defense,
            speed = EXCLUDED.speed,
            updated_at = NOW()
    """

    with conn.cursor() as cursor:
        cursor.executemany(query, stats)

    logger.info(
        "upsert_stats_completed",
        count=len(stats),
    )

    return len(stats)


def upsert_pokemon_types(
    conn: PgConnection, pokemon_types: list[dict[str, Any]]
) -> int:
    """
    Insere relações pokemon_types.

    Usa INSERT ... ON CONFLICT DO NOTHING para evitar duplicatas.

    Args:
        conn: Conexão psycopg2 ativa.
        pokemon_types: Lista de dicts com relações pokemon-type.

    Returns:
        Quantidade de registros processados.
    """
    if not pokemon_types:
        logger.info("upsert_pokemon_types_skipped", reason="empty_list")
        return 0

    query = """
        INSERT INTO pokemon_types (pokemon_id, type_id, slot)
        VALUES (%(pokemon_id)s, %(type_id)s, %(slot)s)
        ON CONFLICT (pokemon_id, type_id) DO NOTHING
    """

    with conn.cursor() as cursor:
        cursor.executemany(query, pokemon_types)

    logger.info(
        "upsert_pokemon_types_completed",
        count=len(pokemon_types),
    )

    return len(pokemon_types)


def upsert_pokemon_abilities(
    conn: PgConnection, pokemon_abilities: list[dict[str, Any]]
) -> int:
    """
    Insere relações pokemon_abilities.

    Usa INSERT ... ON CONFLICT DO NOTHING para evitar duplicatas.

    Args:
        conn: Conexão psycopg2 ativa.
        pokemon_abilities: Lista de dicts com relações pokemon-ability.

    Returns:
        Quantidade de registros processados.
    """
    if not pokemon_abilities:
        logger.info("upsert_pokemon_abilities_skipped", reason="empty_list")
        return 0

    query = """
        INSERT INTO pokemon_abilities (pokemon_id, ability_id, is_hidden, slot)
        VALUES (%(pokemon_id)s, %(ability_id)s, %(is_hidden)s, %(slot)s)
        ON CONFLICT (pokemon_id, ability_id) DO NOTHING
    """

    with conn.cursor() as cursor:
        cursor.executemany(query, pokemon_abilities)

    logger.info(
        "upsert_pokemon_abilities_completed",
        count=len(pokemon_abilities),
    )

    return len(pokemon_abilities)


def run_load(data: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    """
    Função principal que orquestra todas as inserções.

    Executa todas as operações dentro de uma única transação.
    Commit apenas no final; rollback em caso de qualquer erro.

    Ordem de inserção (respeitando FKs):
    1. pokemon (sem FK)
    2. types (sem FK)
    3. abilities (sem FK)
    4. stats (FK -> pokemon)
    5. pokemon_types (FK -> pokemon, types)
    6. pokemon_abilities (FK -> pokemon, abilities)

    Args:
        data: Dict com as 6 listas retornadas por transform_pokemons().

    Returns:
        Dict com contagem de registros processados por entidade.

    Raises:
        LoadError: Se ocorrer erro durante a carga.
    """
    logger.info("load_started")

    conn = None
    counts: dict[str, int] = {}

    try:
        conn = get_connection()

        # Ordem importa por causa das FKs
        counts["pokemons"] = upsert_pokemons(conn, data.get("pokemons", []))
        counts["types"] = upsert_types(conn, data.get("types", []))
        counts["abilities"] = upsert_abilities(conn, data.get("abilities", []))
        counts["stats"] = upsert_stats(conn, data.get("stats", []))
        counts["pokemon_types"] = upsert_pokemon_types(
            conn, data.get("pokemon_types", [])
        )
        counts["pokemon_abilities"] = upsert_pokemon_abilities(
            conn, data.get("pokemon_abilities", [])
        )

        conn.commit()

        logger.info(
            "load_completed",
            **counts,
        )

        return counts

    except Exception as e:
        if conn:
            conn.rollback()
            logger.error(
                "load_failed_rollback_executed",
                error=str(e),
            )
        raise LoadError(f"Falha na carga de dados: {e}") from e

    finally:
        if conn:
            conn.close()
            logger.info("database_connection_closed")


if __name__ == "__main__":
    # Permite execução direta para teste
    sample_data = {
        "pokemons": [
            {
                "id": 25,
                "name": "pikachu",
                "height": 4,
                "weight": 60,
                "base_experience": 112,
            }
        ],
        "types": [{"id": 13, "name": "electric"}],
        "pokemon_types": [{"pokemon_id": 25, "type_id": 13, "slot": 1}],
        "stats": [
            {
                "pokemon_id": 25,
                "hp": 35,
                "attack": 55,
                "defense": 40,
                "special_attack": 50,
                "special_defense": 50,
                "speed": 90,
            }
        ],
        "abilities": [
            {"id": 9, "name": "static", "description": "May cause paralysis."}
        ],
        "pokemon_abilities": [
            {"pokemon_id": 25, "ability_id": 9, "is_hidden": False, "slot": 1}
        ],
    }

    result = run_load(sample_data)
    logger.info("test_load_result", **result)
