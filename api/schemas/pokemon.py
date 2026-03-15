"""
Schemas Pydantic para os endpoints de Pokemon.

Define a estrutura de dados para requests e responses da API.
"""

from pydantic import BaseModel, Field


class PokemonBase(BaseModel):
    """Dados base de um Pokemon."""

    id: int = Field(..., description="ID único do Pokemon")
    name: str = Field(..., description="Nome do Pokemon")
    height: int = Field(..., description="Altura em decímetros")
    weight: int = Field(..., description="Peso em hectogramas")
    base_experience: int | None = Field(None, description="Experiência base")

    model_config = {"from_attributes": True}


class PokemonStats(BaseModel):
    """Estatísticas base de um Pokemon."""

    hp: int = Field(..., description="Hit Points")
    attack: int = Field(..., description="Ataque físico")
    defense: int = Field(..., description="Defesa física")
    special_attack: int = Field(..., description="Ataque especial")
    special_defense: int = Field(..., description="Defesa especial")
    speed: int = Field(..., description="Velocidade")

    model_config = {"from_attributes": True}


class PokemonType(BaseModel):
    """Tipo de Pokemon."""

    id: int = Field(..., description="ID do tipo")
    name: str = Field(..., description="Nome do tipo")

    model_config = {"from_attributes": True}


class PokemonAbility(BaseModel):
    """Habilidade de Pokemon."""

    id: int = Field(..., description="ID da habilidade")
    name: str = Field(..., description="Nome da habilidade")
    description: str | None = Field(None, description="Descrição da habilidade")

    model_config = {"from_attributes": True}


class PokemonListItem(BaseModel):
    """Item resumido para listagem de Pokemons."""

    id: int = Field(..., description="ID único do Pokemon")
    name: str = Field(..., description="Nome do Pokemon")
    height: int = Field(..., description="Altura em decímetros")
    weight: int = Field(..., description="Peso em hectogramas")
    types: list[str] = Field(default_factory=list, description="Lista de tipos")

    model_config = {"from_attributes": True}


class PokemonDetail(BaseModel):
    """Detalhes completos de um Pokemon."""

    id: int = Field(..., description="ID único do Pokemon")
    name: str = Field(..., description="Nome do Pokemon")
    height: int = Field(..., description="Altura em decímetros")
    weight: int = Field(..., description="Peso em hectogramas")
    base_experience: int | None = Field(None, description="Experiência base")
    stats: PokemonStats = Field(..., description="Estatísticas base")
    types: list[PokemonType] = Field(default_factory=list, description="Tipos")
    abilities: list[PokemonAbility] = Field(
        default_factory=list, description="Habilidades"
    )

    model_config = {"from_attributes": True}


class PokemonListResponse(BaseModel):
    """Response para listagem de Pokemons."""

    items: list[PokemonListItem] = Field(..., description="Lista de Pokemons")
    total: int = Field(..., description="Total de registros")
    limit: int = Field(..., description="Limite da página")
    offset: int = Field(..., description="Offset da página")


class StatDiff(BaseModel):
    """Diferença de stats entre dois Pokemons."""

    stat: str = Field(..., description="Nome do stat")
    pokemon_a: int = Field(..., description="Valor do Pokemon A")
    pokemon_b: int = Field(..., description="Valor do Pokemon B")
    diff: int = Field(..., description="Diferença (A - B)")
    winner: str = Field(..., description="Nome do Pokemon com maior valor")


class PokemonCompareResponse(BaseModel):
    """Response para comparação de dois Pokemons."""

    pokemon_a: PokemonDetail = Field(..., description="Primeiro Pokemon")
    pokemon_b: PokemonDetail = Field(..., description="Segundo Pokemon")
    stat_comparison: list[StatDiff] = Field(..., description="Comparação stat a stat")
    summary: str = Field(..., description="Resumo da comparação")


class TopPokemonItem(BaseModel):
    """Item do ranking de Pokemons por stat."""

    rank: int = Field(..., description="Posição no ranking")
    id: int = Field(..., description="ID do Pokemon")
    name: str = Field(..., description="Nome do Pokemon")
    stat_name: str = Field(..., description="Nome do stat")
    stat_value: int = Field(..., description="Valor do stat")


class TopPokemonResponse(BaseModel):
    """Response para ranking de Pokemons."""

    stat: str = Field(..., description="Stat usado para ranking")
    items: list[TopPokemonItem] = Field(..., description="Lista ordenada")
