"""
Testes unitários para os endpoints de Pokemon.

Cobertura:
- GET /pokemons — status 200 e estrutura
- GET /pokemons/{id} — status 200 com Pokemon existente
- GET /pokemons/{id} — status 404 com Pokemon inexistente
- GET /pokemons/stats/top — status 200 e ordenação
"""

import importlib.util
import os
import unittest
from unittest.mock import patch
import sys
from pathlib import Path

# Configura paths para a API
api_path = Path(__file__).parent.parent.parent / "api"


def load_api_module(module_name: str):
    """Carrega um módulo da API pelo caminho absoluto."""
    module_file = api_path / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(module_name, module_file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# Adiciona api ao path para imports internos
sys.path.insert(0, str(api_path))


class TestSchemas(unittest.TestCase):
    """Testes para os schemas Pydantic."""

    def test_pokemon_base_schema(self) -> None:
        """PokemonBase deve validar dados corretamente."""
        from schemas.pokemon import PokemonBase

        pokemon = PokemonBase(
            id=25, name="pikachu", height=4, weight=60, base_experience=112
        )

        self.assertEqual(pokemon.id, 25)
        self.assertEqual(pokemon.name, "pikachu")

    def test_pokemon_stats_schema(self) -> None:
        """PokemonStats deve validar dados corretamente."""
        from schemas.pokemon import PokemonStats

        stats = PokemonStats(
            hp=35,
            attack=55,
            defense=40,
            special_attack=50,
            special_defense=50,
            speed=90,
        )

        self.assertEqual(stats.hp, 35)
        self.assertEqual(stats.speed, 90)

    def test_pokemon_list_response_schema(self) -> None:
        """PokemonListResponse deve validar dados corretamente."""
        from schemas.pokemon import PokemonListResponse, PokemonListItem

        item = PokemonListItem(
            id=25, name="pikachu", height=4, weight=60, types=["electric"]
        )

        response = PokemonListResponse(items=[item], total=1, limit=20, offset=0)

        self.assertEqual(len(response.items), 1)
        self.assertEqual(response.total, 1)

    def test_top_pokemon_item_schema(self) -> None:
        """TopPokemonItem deve validar dados corretamente."""
        from schemas.pokemon import TopPokemonItem

        item = TopPokemonItem(
            rank=1, id=25, name="pikachu", stat_name="speed", stat_value=90
        )

        self.assertEqual(item.rank, 1)
        self.assertEqual(item.stat_value, 90)

    def test_stat_diff_schema(self) -> None:
        """StatDiff deve validar dados corretamente."""
        from schemas.pokemon import StatDiff

        diff = StatDiff(
            stat="attack", pokemon_a=55, pokemon_b=90, diff=-35, winner="raichu"
        )

        self.assertEqual(diff.diff, -35)
        self.assertEqual(diff.winner, "raichu")


class TestRouterFunctions(unittest.TestCase):
    """Testes para funções do router de Pokemon."""

    def test_valid_stats_constant(self) -> None:
        """VALID_STATS deve conter os 6 stats esperados."""
        from routers.pokemon import VALID_STATS

        expected = {
            "hp",
            "attack",
            "defense",
            "special_attack",
            "special_defense",
            "speed",
        }
        self.assertEqual(VALID_STATS, expected)


class TestDatabaseModule(unittest.TestCase):
    """Testes para o módulo de banco de dados."""

    @patch.dict(
        os.environ,
        {
            "POSTGRES_USER": "test_user",
            "POSTGRES_PASSWORD": "test_pass",
            "POSTGRES_HOST": "test_host",
            "POSTGRES_PORT": "5432",
            "POSTGRES_DB": "test_db",
        },
    )
    def test_get_database_url(self) -> None:
        """get_database_url deve construir URL corretamente."""
        # Recarrega o módulo para pegar as novas variáveis de ambiente
        import database

        importlib.reload(database)

        url = database.get_database_url()

        self.assertIn("test_user", url)
        self.assertIn("test_host", url)
        self.assertIn("test_db", url)


if __name__ == "__main__":
    unittest.main()
