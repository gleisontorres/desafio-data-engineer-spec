"""
Testes unitários para o módulo load.py.

Cobertura:
- run_load com sucesso — verificar que commit foi chamado
- run_load com erro — verificar que rollback foi chamado
- upsert_pokemons com lista vazia — não deve quebrar
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Adiciona o diretório etl ao path para importação
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "etl"))

from load import (
    run_load,
    upsert_pokemons,
    upsert_types,
    upsert_abilities,
    upsert_stats,
    upsert_pokemon_types,
    upsert_pokemon_abilities,
    LoadError,
)


class TestUpsertPokemons(unittest.TestCase):
    """Testes para a função upsert_pokemons."""

    def test_upsert_pokemons_empty_list(self) -> None:
        """Lista vazia deve retornar 0 sem executar query."""
        mock_conn = MagicMock()

        result = upsert_pokemons(mock_conn, [])

        self.assertEqual(result, 0)
        mock_conn.cursor.assert_not_called()

    def test_upsert_pokemons_executes_query(self) -> None:
        """Lista com dados deve executar query corretamente."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        pokemons = [
            {
                "id": 25,
                "name": "pikachu",
                "height": 4,
                "weight": 60,
                "base_experience": 112,
            }
        ]

        result = upsert_pokemons(mock_conn, pokemons)

        self.assertEqual(result, 1)
        mock_cursor.executemany.assert_called_once()

    def test_upsert_pokemons_multiple_records(self) -> None:
        """Múltiplos registros devem ser processados."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        pokemons = [
            {
                "id": 1,
                "name": "bulbasaur",
                "height": 7,
                "weight": 69,
                "base_experience": 64,
            },
            {
                "id": 2,
                "name": "ivysaur",
                "height": 10,
                "weight": 130,
                "base_experience": 142,
            },
            {
                "id": 3,
                "name": "venusaur",
                "height": 20,
                "weight": 1000,
                "base_experience": 263,
            },
        ]

        result = upsert_pokemons(mock_conn, pokemons)

        self.assertEqual(result, 3)


class TestUpsertTypes(unittest.TestCase):
    """Testes para a função upsert_types."""

    def test_upsert_types_empty_list(self) -> None:
        """Lista vazia deve retornar 0."""
        mock_conn = MagicMock()

        result = upsert_types(mock_conn, [])

        self.assertEqual(result, 0)

    def test_upsert_types_executes_query(self) -> None:
        """Lista com dados deve executar query."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        types = [{"id": 13, "name": "electric"}]

        result = upsert_types(mock_conn, types)

        self.assertEqual(result, 1)
        mock_cursor.executemany.assert_called_once()


class TestUpsertAbilities(unittest.TestCase):
    """Testes para a função upsert_abilities."""

    def test_upsert_abilities_empty_list(self) -> None:
        """Lista vazia deve retornar 0."""
        mock_conn = MagicMock()

        result = upsert_abilities(mock_conn, [])

        self.assertEqual(result, 0)


class TestUpsertStats(unittest.TestCase):
    """Testes para a função upsert_stats."""

    def test_upsert_stats_empty_list(self) -> None:
        """Lista vazia deve retornar 0."""
        mock_conn = MagicMock()

        result = upsert_stats(mock_conn, [])

        self.assertEqual(result, 0)


class TestUpsertPokemonTypes(unittest.TestCase):
    """Testes para a função upsert_pokemon_types."""

    def test_upsert_pokemon_types_empty_list(self) -> None:
        """Lista vazia deve retornar 0."""
        mock_conn = MagicMock()

        result = upsert_pokemon_types(mock_conn, [])

        self.assertEqual(result, 0)


class TestUpsertPokemonAbilities(unittest.TestCase):
    """Testes para a função upsert_pokemon_abilities."""

    def test_upsert_pokemon_abilities_empty_list(self) -> None:
        """Lista vazia deve retornar 0."""
        mock_conn = MagicMock()

        result = upsert_pokemon_abilities(mock_conn, [])

        self.assertEqual(result, 0)


class TestRunLoad(unittest.TestCase):
    """Testes para a função run_load."""

    def setUp(self) -> None:
        """Dados de teste."""
        self.sample_data = {
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

    @patch("load.get_connection")
    def test_run_load_success_commits(self, mock_get_conn: MagicMock) -> None:
        """Carga bem sucedida deve chamar commit."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_conn.return_value = mock_conn

        result = run_load(self.sample_data)

        mock_conn.commit.assert_called_once()
        mock_conn.rollback.assert_not_called()
        mock_conn.close.assert_called_once()

        self.assertEqual(result["pokemons"], 1)
        self.assertEqual(result["types"], 1)

    @patch("load.get_connection")
    def test_run_load_error_rollbacks(self, mock_get_conn: MagicMock) -> None:
        """Erro durante carga deve chamar rollback."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.executemany.side_effect = Exception("Database error")
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_conn.return_value = mock_conn

        with self.assertRaises(LoadError):
            run_load(self.sample_data)

        mock_conn.rollback.assert_called_once()
        mock_conn.commit.assert_not_called()
        mock_conn.close.assert_called_once()

    @patch("load.get_connection")
    def test_run_load_empty_data(self, mock_get_conn: MagicMock) -> None:
        """Dados vazios deve funcionar sem erros."""
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        result = run_load({})

        mock_conn.commit.assert_called_once()
        self.assertEqual(result["pokemons"], 0)
        self.assertEqual(result["types"], 0)

    @patch("load.get_connection")
    def test_run_load_connection_closed_on_success(
        self, mock_get_conn: MagicMock
    ) -> None:
        """Conexão deve ser fechada após sucesso."""
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        run_load({})

        mock_conn.close.assert_called_once()

    @patch("load.get_connection")
    def test_run_load_connection_closed_on_error(
        self, mock_get_conn: MagicMock
    ) -> None:
        """Conexão deve ser fechada mesmo após erro."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.executemany.side_effect = Exception("Error")
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_conn.return_value = mock_conn

        with self.assertRaises(LoadError):
            run_load(self.sample_data)

        mock_conn.close.assert_called_once()

    @patch("load.get_connection")
    def test_run_load_returns_counts(self, mock_get_conn: MagicMock) -> None:
        """Retorno deve conter contagem de todas as entidades."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_conn.return_value = mock_conn

        result = run_load(self.sample_data)

        expected_keys = [
            "pokemons",
            "types",
            "abilities",
            "stats",
            "pokemon_types",
            "pokemon_abilities",
        ]
        for key in expected_keys:
            self.assertIn(key, result)

    @patch("load.get_connection")
    def test_run_load_respects_order(self, mock_get_conn: MagicMock) -> None:
        """Inserções devem respeitar ordem de dependência (FKs)."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_conn.return_value = mock_conn

        call_order = []

        def track_calls(query, data):
            query_lower = query.lower()
            if "into pokemon_types" in query_lower:
                call_order.append("pokemon_types")
            elif "into pokemon_abilities" in query_lower:
                call_order.append("pokemon_abilities")
            elif "into pokemon " in query_lower or "into pokemon(" in query_lower:
                call_order.append("pokemons")
            elif "into types " in query_lower or "into types(" in query_lower:
                call_order.append("types")
            elif "into abilities " in query_lower or "into abilities(" in query_lower:
                call_order.append("abilities")
            elif "into stats " in query_lower or "into stats(" in query_lower:
                call_order.append("stats")

        mock_cursor.executemany.side_effect = track_calls

        run_load(self.sample_data)

        # Entidades principais devem vir antes das relações
        pokemons_idx = call_order.index("pokemons")
        types_idx = call_order.index("types")
        abilities_idx = call_order.index("abilities")
        stats_idx = call_order.index("stats")
        pokemon_types_idx = call_order.index("pokemon_types")
        pokemon_abilities_idx = call_order.index("pokemon_abilities")

        # stats depende de pokemons
        self.assertLess(pokemons_idx, stats_idx)

        # pokemon_types depende de pokemons e types
        self.assertLess(pokemons_idx, pokemon_types_idx)
        self.assertLess(types_idx, pokemon_types_idx)

        # pokemon_abilities depende de pokemons e abilities
        self.assertLess(pokemons_idx, pokemon_abilities_idx)
        self.assertLess(abilities_idx, pokemon_abilities_idx)


if __name__ == "__main__":
    unittest.main()
