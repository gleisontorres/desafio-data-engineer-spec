"""Schemas Pydantic para validação de dados da API."""

from .pokemon import (
    PokemonBase,
    PokemonStats,
    PokemonType,
    PokemonAbility,
    PokemonDetail,
    PokemonListItem,
    PokemonListResponse,
    PokemonCompareResponse,
    StatDiff,
    TopPokemonItem,
    TopPokemonResponse,
)

__all__ = [
    "PokemonBase",
    "PokemonStats",
    "PokemonType",
    "PokemonAbility",
    "PokemonDetail",
    "PokemonListItem",
    "PokemonListResponse",
    "PokemonCompareResponse",
    "StatDiff",
    "TopPokemonItem",
    "TopPokemonResponse",
]
