"""
Router de endpoints para Pokemon.

Todos os endpoints de leitura de dados de Pokemon.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
import structlog

from database import get_db
from schemas.pokemon import (
    PokemonDetail,
    PokemonListItem,
    PokemonListResponse,
    PokemonStats,
    PokemonType,
    PokemonAbility,
    PokemonCompareResponse,
    StatDiff,
    TopPokemonItem,
    TopPokemonResponse,
)

logger = structlog.get_logger(module="routers.pokemon")

router = APIRouter(prefix="/pokemons", tags=["Pokemon"])

# Stats válidos para consulta
VALID_STATS = {"hp", "attack", "defense", "special_attack", "special_defense", "speed"}


def _get_pokemon_by_id(db: Session, pokemon_id: int) -> dict | None:
    """
    Busca um Pokemon pelo ID.

    Args:
        db: Sessão do banco.
        pokemon_id: ID do Pokemon.

    Returns:
        Dicionário com dados do Pokemon ou None.
    """
    query = text("""
        SELECT p.id, p.name, p.height, p.weight, p.base_experience
        FROM pokemon p
        WHERE p.id = :pokemon_id
    """)
    result = db.execute(query, {"pokemon_id": pokemon_id}).fetchone()

    if result:
        return {
            "id": result[0],
            "name": result[1],
            "height": result[2],
            "weight": result[3],
            "base_experience": result[4],
        }
    return None


def _get_pokemon_by_name(db: Session, name: str) -> dict | None:
    """
    Busca um Pokemon pelo nome.

    Args:
        db: Sessão do banco.
        name: Nome do Pokemon (case insensitive).

    Returns:
        Dicionário com dados do Pokemon ou None.
    """
    query = text("""
        SELECT p.id, p.name, p.height, p.weight, p.base_experience
        FROM pokemon p
        WHERE LOWER(p.name) = LOWER(:name)
    """)
    result = db.execute(query, {"name": name}).fetchone()

    if result:
        return {
            "id": result[0],
            "name": result[1],
            "height": result[2],
            "weight": result[3],
            "base_experience": result[4],
        }
    return None


def _get_pokemon_stats(db: Session, pokemon_id: int) -> PokemonStats | None:
    """Busca stats de um Pokemon."""
    query = text("""
        SELECT hp, attack, defense, special_attack, special_defense, speed
        FROM stats
        WHERE pokemon_id = :pokemon_id
    """)
    result = db.execute(query, {"pokemon_id": pokemon_id}).fetchone()

    if result:
        return PokemonStats(
            hp=result[0],
            attack=result[1],
            defense=result[2],
            special_attack=result[3],
            special_defense=result[4],
            speed=result[5],
        )
    return None


def _get_pokemon_types(db: Session, pokemon_id: int) -> list[PokemonType]:
    """Busca tipos de um Pokemon."""
    query = text("""
        SELECT t.id, t.name
        FROM types t
        JOIN pokemon_types pt ON t.id = pt.type_id
        WHERE pt.pokemon_id = :pokemon_id
        ORDER BY pt.slot
    """)
    results = db.execute(query, {"pokemon_id": pokemon_id}).fetchall()

    return [PokemonType(id=r[0], name=r[1]) for r in results]


def _get_pokemon_abilities(db: Session, pokemon_id: int) -> list[PokemonAbility]:
    """Busca habilidades de um Pokemon."""
    query = text("""
        SELECT a.id, a.name, a.description
        FROM abilities a
        JOIN pokemon_abilities pa ON a.id = pa.ability_id
        WHERE pa.pokemon_id = :pokemon_id
        ORDER BY pa.slot
    """)
    results = db.execute(query, {"pokemon_id": pokemon_id}).fetchall()

    return [PokemonAbility(id=r[0], name=r[1], description=r[2]) for r in results]


def _build_pokemon_detail(db: Session, pokemon_data: dict) -> PokemonDetail:
    """Constrói objeto PokemonDetail completo."""
    pokemon_id = pokemon_data["id"]

    stats = _get_pokemon_stats(db, pokemon_id)
    if not stats:
        stats = PokemonStats(
            hp=0, attack=0, defense=0, special_attack=0, special_defense=0, speed=0
        )

    types = _get_pokemon_types(db, pokemon_id)
    abilities = _get_pokemon_abilities(db, pokemon_id)

    return PokemonDetail(
        id=pokemon_data["id"],
        name=pokemon_data["name"],
        height=pokemon_data["height"],
        weight=pokemon_data["weight"],
        base_experience=pokemon_data["base_experience"],
        stats=stats,
        types=types,
        abilities=abilities,
    )


@router.get("", response_model=PokemonListResponse)
def list_pokemons(
    limit: int = Query(default=20, ge=1, le=100, description="Quantidade de itens"),
    offset: int = Query(default=0, ge=0, description="Offset para paginação"),
    db: Session = Depends(get_db),
) -> PokemonListResponse:
    """
    Lista todos os Pokemons com paginação.

    Retorna versão resumida de cada Pokemon para listagem.
    """
    logger.info(
        "list_pokemons_request",
        limit=limit,
        offset=offset,
    )

    # Conta total
    count_query = text("SELECT COUNT(*) FROM pokemon")
    total = db.execute(count_query).scalar()

    # Busca página
    query = text("""
        SELECT p.id, p.name, p.height, p.weight,
               COALESCE(
                   (SELECT STRING_AGG(t.name, ',' ORDER BY pt.slot)
                    FROM types t
                    JOIN pokemon_types pt ON t.id = pt.type_id
                    WHERE pt.pokemon_id = p.id),
                   ''
               ) as types
        FROM pokemon p
        ORDER BY p.id
        LIMIT :limit OFFSET :offset
    """)
    results = db.execute(query, {"limit": limit, "offset": offset}).fetchall()

    items = [
        PokemonListItem(
            id=r[0],
            name=r[1],
            height=r[2],
            weight=r[3],
            types=r[4].split(",") if r[4] else [],
        )
        for r in results
    ]

    logger.info(
        "list_pokemons_response",
        count=len(items),
        total=total,
    )

    return PokemonListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/stats/top", response_model=TopPokemonResponse)
def get_top_by_stat(
    stat: str = Query(
        ...,
        description="Nome do stat (hp, attack, defense, special_attack, special_defense, speed)",
    ),
    limit: int = Query(default=10, ge=1, le=50, description="Quantidade de itens"),
    db: Session = Depends(get_db),
) -> TopPokemonResponse:
    """
    Retorna ranking dos Pokemons por um stat específico.

    Stats válidos: hp, attack, defense, special_attack, special_defense, speed
    """
    logger.info(
        "top_by_stat_request",
        stat=stat,
        limit=limit,
    )

    if stat not in VALID_STATS:
        raise HTTPException(
            status_code=400,
            detail=f"Stat invalido: {stat}. Stats validos: {', '.join(sorted(VALID_STATS))}",
        )

    query = text(f"""
        SELECT p.id, p.name, s.{stat}
        FROM pokemon p
        JOIN stats s ON p.id = s.pokemon_id
        ORDER BY s.{stat} DESC
        LIMIT :limit
    """)
    results = db.execute(query, {"limit": limit}).fetchall()

    items = [
        TopPokemonItem(
            rank=idx + 1,
            id=r[0],
            name=r[1],
            stat_name=stat,
            stat_value=r[2],
        )
        for idx, r in enumerate(results)
    ]

    logger.info(
        "top_by_stat_response",
        stat=stat,
        count=len(items),
    )

    return TopPokemonResponse(stat=stat, items=items)


@router.get("/compare", response_model=PokemonCompareResponse)
def compare_pokemons(
    pokemon_a: str = Query(..., description="Nome ou ID do primeiro Pokemon"),
    pokemon_b: str = Query(..., description="Nome ou ID do segundo Pokemon"),
    db: Session = Depends(get_db),
) -> PokemonCompareResponse:
    """
    Compara dois Pokemons lado a lado.

    Retorna stats de ambos e a diferença entre eles.
    """
    logger.info(
        "compare_pokemons_request",
        pokemon_a=pokemon_a,
        pokemon_b=pokemon_b,
    )

    # Busca Pokemon A
    if pokemon_a.isdigit():
        data_a = _get_pokemon_by_id(db, int(pokemon_a))
    else:
        data_a = _get_pokemon_by_name(db, pokemon_a)

    if not data_a:
        raise HTTPException(
            status_code=404,
            detail=f"Pokemon nao encontrado: {pokemon_a}",
        )

    # Busca Pokemon B
    if pokemon_b.isdigit():
        data_b = _get_pokemon_by_id(db, int(pokemon_b))
    else:
        data_b = _get_pokemon_by_name(db, pokemon_b)

    if not data_b:
        raise HTTPException(
            status_code=404,
            detail=f"Pokemon nao encontrado: {pokemon_b}",
        )

    detail_a = _build_pokemon_detail(db, data_a)
    detail_b = _build_pokemon_detail(db, data_b)

    # Compara stats
    stat_names = [
        "hp",
        "attack",
        "defense",
        "special_attack",
        "special_defense",
        "speed",
    ]
    comparisons = []
    wins_a = 0
    wins_b = 0

    for stat_name in stat_names:
        val_a = getattr(detail_a.stats, stat_name)
        val_b = getattr(detail_b.stats, stat_name)
        diff = val_a - val_b

        if diff > 0:
            winner = detail_a.name
            wins_a += 1
        elif diff < 0:
            winner = detail_b.name
            wins_b += 1
        else:
            winner = "empate"

        comparisons.append(
            StatDiff(
                stat=stat_name,
                pokemon_a=val_a,
                pokemon_b=val_b,
                diff=diff,
                winner=winner,
            )
        )

    if wins_a > wins_b:
        summary = f"{detail_a.name} vence em {wins_a} stats"
    elif wins_b > wins_a:
        summary = f"{detail_b.name} vence em {wins_b} stats"
    else:
        summary = "Empate"

    logger.info(
        "compare_pokemons_response",
        pokemon_a=detail_a.name,
        pokemon_b=detail_b.name,
        wins_a=wins_a,
        wins_b=wins_b,
    )

    return PokemonCompareResponse(
        pokemon_a=detail_a,
        pokemon_b=detail_b,
        stat_comparison=comparisons,
        summary=summary,
    )


@router.get("/type/{type_name}", response_model=PokemonListResponse)
def list_pokemons_by_type(
    type_name: str,
    limit: int = Query(default=20, ge=1, le=100, description="Quantidade de itens"),
    offset: int = Query(default=0, ge=0, description="Offset para paginação"),
    db: Session = Depends(get_db),
) -> PokemonListResponse:
    """
    Lista todos os Pokemons de um tipo específico.

    Retorna 404 se o tipo não existir.
    """
    logger.info(
        "list_by_type_request",
        type_name=type_name,
        limit=limit,
        offset=offset,
    )

    # Verifica se tipo existe
    type_check = text("SELECT id FROM types WHERE LOWER(name) = LOWER(:type_name)")
    type_exists = db.execute(type_check, {"type_name": type_name}).fetchone()

    if not type_exists:
        raise HTTPException(
            status_code=404,
            detail=f"Tipo nao encontrado: {type_name}",
        )

    # Conta total
    count_query = text("""
        SELECT COUNT(DISTINCT p.id)
        FROM pokemon p
        JOIN pokemon_types pt ON p.id = pt.pokemon_id
        JOIN types t ON pt.type_id = t.id
        WHERE LOWER(t.name) = LOWER(:type_name)
    """)
    total = db.execute(count_query, {"type_name": type_name}).scalar()

    # Busca página
    query = text("""
        SELECT DISTINCT p.id, p.name, p.height, p.weight,
               COALESCE(
                   (SELECT STRING_AGG(t2.name, ',' ORDER BY pt2.slot)
                    FROM types t2
                    JOIN pokemon_types pt2 ON t2.id = pt2.type_id
                    WHERE pt2.pokemon_id = p.id),
                   ''
               ) as types
        FROM pokemon p
        JOIN pokemon_types pt ON p.id = pt.pokemon_id
        JOIN types t ON pt.type_id = t.id
        WHERE LOWER(t.name) = LOWER(:type_name)
        ORDER BY p.id
        LIMIT :limit OFFSET :offset
    """)
    results = db.execute(
        query, {"type_name": type_name, "limit": limit, "offset": offset}
    ).fetchall()

    items = [
        PokemonListItem(
            id=r[0],
            name=r[1],
            height=r[2],
            weight=r[3],
            types=r[4].split(",") if r[4] else [],
        )
        for r in results
    ]

    logger.info(
        "list_by_type_response",
        type_name=type_name,
        count=len(items),
        total=total,
    )

    return PokemonListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{name_or_id}", response_model=PokemonDetail)
def get_pokemon(
    name_or_id: str,
    db: Session = Depends(get_db),
) -> PokemonDetail:
    """
    Busca um Pokemon por nome ou ID.

    Retorna detalhes completos incluindo stats, tipos e habilidades.
    """
    logger.info(
        "get_pokemon_request",
        name_or_id=name_or_id,
    )

    # Tenta buscar por ID se for número
    if name_or_id.isdigit():
        pokemon_data = _get_pokemon_by_id(db, int(name_or_id))
    else:
        pokemon_data = _get_pokemon_by_name(db, name_or_id)

    if not pokemon_data:
        raise HTTPException(
            status_code=404,
            detail=f"Pokemon nao encontrado: {name_or_id}",
        )

    result = _build_pokemon_detail(db, pokemon_data)

    logger.info(
        "get_pokemon_response",
        pokemon_id=result.id,
        pokemon_name=result.name,
    )

    return result
