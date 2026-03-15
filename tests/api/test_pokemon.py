"""
Testes unitários para os endpoints de Pokemon.

Cobertura:
- GET /pokemons — status 200 e estrutura
- GET /pokemons/{id} — status 200 com Pokemon existente
- GET /pokemons/{id} — status 404 com Pokemon inexistente
- GET /pokemons/stats/top — status 200 e ordenação
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Adiciona o diretório api ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "api"))

from fastapi.testclient import TestClient


class TestPokemonEndpoints(unittest.TestCase):
    """Testes para os endpoints de Pokemon."""

    @classmethod
    def setUpClass(cls) -> None:
        """Configura o cliente de teste com mocks."""
        # Mock do banco de dados
        cls.mock_db = MagicMock()

        # Dados de teste
        cls.sample_pokemon = (25, "pikachu", 4, 60, 112)
        cls.sample_stats = (35, 55, 40, 50, 50, 90)
        cls.sample_types = [(13, "electric")]
        cls.sample_abilities = [(9, "static", "May paralyze on contact")]

    def setUp(self) -> None:
        """Configura mocks antes de cada teste."""
        # Patch do get_db para retornar mock
        self.db_patch = patch("routers.pokemon.get_db")
        self.mock_get_db = self.db_patch.start()

        # Configura o mock do banco
        mock_session = MagicMock()
        self.mock_get_db.return_value = iter([mock_session])
        self.mock_session = mock_session

        # Importa app após configurar mocks
        from main import app

        self.client = TestClient(app)

    def tearDown(self) -> None:
        """Limpa mocks após cada teste."""
        self.db_patch.stop()

    def _setup_pokemon_exists(self) -> None:
        """Configura mock para Pokemon existente."""

        def execute_side_effect(query, params=None):
            query_str = str(query)
            result_mock = MagicMock()

            if "COUNT(*)" in query_str:
                result_mock.scalar.return_value = 151
                return result_mock

            if "FROM pokemon p" in query_str and "WHERE" in query_str:
                if "LOWER(p.name)" in query_str or "p.id = :pokemon_id" in query_str:
                    result_mock.fetchone.return_value = self.sample_pokemon
                    return result_mock

            if "FROM stats" in query_str:
                result_mock.fetchone.return_value = self.sample_stats
                return result_mock

            if "FROM types t" in query_str:
                result_mock.fetchall.return_value = self.sample_types
                return result_mock

            if "FROM abilities a" in query_str:
                result_mock.fetchall.return_value = self.sample_abilities
                return result_mock

            if "STRING_AGG" in query_str:
                result_mock.fetchall.return_value = [
                    (25, "pikachu", 4, 60, "electric"),
                ]
                return result_mock

            result_mock.fetchone.return_value = None
            result_mock.fetchall.return_value = []
            result_mock.scalar.return_value = 0
            return result_mock

        self.mock_session.execute.side_effect = execute_side_effect

    def _setup_pokemon_not_found(self) -> None:
        """Configura mock para Pokemon não encontrado."""

        def execute_side_effect(query, params=None):
            result_mock = MagicMock()
            result_mock.fetchone.return_value = None
            result_mock.fetchall.return_value = []
            result_mock.scalar.return_value = 0
            return result_mock

        self.mock_session.execute.side_effect = execute_side_effect

    def test_list_pokemons_returns_200(self) -> None:
        """GET /pokemons deve retornar 200."""
        self._setup_pokemon_exists()

        response = self.client.get("/pokemons")

        self.assertEqual(response.status_code, 200)

    def test_list_pokemons_response_structure(self) -> None:
        """GET /pokemons deve retornar estrutura correta."""
        self._setup_pokemon_exists()

        response = self.client.get("/pokemons")
        data = response.json()

        self.assertIn("items", data)
        self.assertIn("total", data)
        self.assertIn("limit", data)
        self.assertIn("offset", data)

    def test_list_pokemons_with_pagination(self) -> None:
        """GET /pokemons deve respeitar paginação."""
        self._setup_pokemon_exists()

        response = self.client.get("/pokemons?limit=5&offset=10")
        data = response.json()

        self.assertEqual(data["limit"], 5)
        self.assertEqual(data["offset"], 10)

    def test_get_pokemon_by_id_returns_200(self) -> None:
        """GET /pokemons/{id} com Pokemon existente deve retornar 200."""
        self._setup_pokemon_exists()

        response = self.client.get("/pokemons/25")

        self.assertEqual(response.status_code, 200)

    def test_get_pokemon_by_id_response_structure(self) -> None:
        """GET /pokemons/{id} deve retornar estrutura completa."""
        self._setup_pokemon_exists()

        response = self.client.get("/pokemons/25")
        data = response.json()

        self.assertIn("id", data)
        self.assertIn("name", data)
        self.assertIn("stats", data)
        self.assertIn("types", data)
        self.assertIn("abilities", data)

    def test_get_pokemon_by_name_returns_200(self) -> None:
        """GET /pokemons/{name} com Pokemon existente deve retornar 200."""
        self._setup_pokemon_exists()

        response = self.client.get("/pokemons/pikachu")

        self.assertEqual(response.status_code, 200)

    def test_get_pokemon_not_found_returns_404(self) -> None:
        """GET /pokemons/{id} com Pokemon inexistente deve retornar 404."""
        self._setup_pokemon_not_found()

        response = self.client.get("/pokemons/9999")

        self.assertEqual(response.status_code, 404)

    def test_get_pokemon_not_found_message(self) -> None:
        """GET /pokemons/{id} 404 deve incluir mensagem clara."""
        self._setup_pokemon_not_found()

        response = self.client.get("/pokemons/9999")
        data = response.json()

        self.assertIn("detail", data)
        self.assertIn("9999", data["detail"])

    def test_top_by_stat_returns_200(self) -> None:
        """GET /pokemons/stats/top deve retornar 200."""

        def execute_side_effect(query, params=None):
            result_mock = MagicMock()
            result_mock.fetchall.return_value = [
                (25, "pikachu", 90),
                (26, "raichu", 110),
            ]
            return result_mock

        self.mock_session.execute.side_effect = execute_side_effect

        response = self.client.get("/pokemons/stats/top?stat=speed&limit=10")

        self.assertEqual(response.status_code, 200)

    def test_top_by_stat_response_structure(self) -> None:
        """GET /pokemons/stats/top deve retornar estrutura correta."""

        def execute_side_effect(query, params=None):
            result_mock = MagicMock()
            result_mock.fetchall.return_value = [
                (25, "pikachu", 90),
            ]
            return result_mock

        self.mock_session.execute.side_effect = execute_side_effect

        response = self.client.get("/pokemons/stats/top?stat=attack&limit=5")
        data = response.json()

        self.assertIn("stat", data)
        self.assertIn("items", data)
        self.assertEqual(data["stat"], "attack")

    def test_top_by_stat_invalid_stat_returns_400(self) -> None:
        """GET /pokemons/stats/top com stat inválido deve retornar 400."""
        response = self.client.get("/pokemons/stats/top?stat=invalid_stat")

        self.assertEqual(response.status_code, 400)

    def test_top_by_stat_items_have_rank(self) -> None:
        """GET /pokemons/stats/top itens devem ter rank."""

        def execute_side_effect(query, params=None):
            result_mock = MagicMock()
            result_mock.fetchall.return_value = [
                (25, "pikachu", 90),
                (26, "raichu", 85),
            ]
            return result_mock

        self.mock_session.execute.side_effect = execute_side_effect

        response = self.client.get("/pokemons/stats/top?stat=speed")
        data = response.json()

        self.assertEqual(data["items"][0]["rank"], 1)
        self.assertEqual(data["items"][1]["rank"], 2)

    def test_health_endpoint_returns_200(self) -> None:
        """GET /health deve retornar 200."""
        with patch("main.check_database_connection", return_value=True):
            response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)

    def test_root_endpoint_returns_info(self) -> None:
        """GET / deve retornar informações da API."""
        response = self.client.get("/")
        data = response.json()

        self.assertIn("name", data)
        self.assertIn("version", data)


class TestCompareEndpoint(unittest.TestCase):
    """Testes para o endpoint de comparação."""

    def setUp(self) -> None:
        """Configura mocks antes de cada teste."""
        self.db_patch = patch("routers.pokemon.get_db")
        self.mock_get_db = self.db_patch.start()

        mock_session = MagicMock()
        self.mock_get_db.return_value = iter([mock_session])
        self.mock_session = mock_session

        from main import app

        self.client = TestClient(app)

    def tearDown(self) -> None:
        """Limpa mocks após cada teste."""
        self.db_patch.stop()

    def test_compare_returns_200(self) -> None:
        """GET /pokemons/compare deve retornar 200."""
        pokemon_a = (25, "pikachu", 4, 60, 112)
        pokemon_b = (26, "raichu", 8, 300, 218)
        stats_a = (35, 55, 40, 50, 50, 90)
        stats_b = (60, 90, 55, 90, 80, 110)

        call_count = [0]

        def execute_side_effect(query, params=None):
            query_str = str(query)
            result_mock = MagicMock()

            if "FROM pokemon p" in query_str and "WHERE" in query_str:
                call_count[0] += 1
                if call_count[0] == 1:
                    result_mock.fetchone.return_value = pokemon_a
                else:
                    result_mock.fetchone.return_value = pokemon_b
                return result_mock

            if "FROM stats" in query_str:
                if call_count[0] == 1:
                    result_mock.fetchone.return_value = stats_a
                else:
                    result_mock.fetchone.return_value = stats_b
                return result_mock

            if "FROM types t" in query_str:
                result_mock.fetchall.return_value = [(13, "electric")]
                return result_mock

            if "FROM abilities a" in query_str:
                result_mock.fetchall.return_value = [(9, "static", "Effect")]
                return result_mock

            result_mock.fetchone.return_value = None
            result_mock.fetchall.return_value = []
            return result_mock

        self.mock_session.execute.side_effect = execute_side_effect

        response = self.client.get(
            "/pokemons/compare?pokemon_a=pikachu&pokemon_b=raichu"
        )

        self.assertEqual(response.status_code, 200)

    def test_compare_response_structure(self) -> None:
        """GET /pokemons/compare deve retornar estrutura correta."""
        pokemon_a = (25, "pikachu", 4, 60, 112)
        pokemon_b = (26, "raichu", 8, 300, 218)
        stats = (35, 55, 40, 50, 50, 90)

        def execute_side_effect(query, params=None):
            query_str = str(query)
            result_mock = MagicMock()

            if "FROM pokemon p" in query_str:
                if (
                    params
                    and params.get("pokemon_id") == 25
                    or params
                    and params.get("name") == "pikachu"
                ):
                    result_mock.fetchone.return_value = pokemon_a
                else:
                    result_mock.fetchone.return_value = pokemon_b
                return result_mock

            if "FROM stats" in query_str:
                result_mock.fetchone.return_value = stats
                return result_mock

            if "FROM types" in query_str or "FROM abilities" in query_str:
                result_mock.fetchall.return_value = []
                return result_mock

            result_mock.fetchone.return_value = None
            return result_mock

        self.mock_session.execute.side_effect = execute_side_effect

        response = self.client.get("/pokemons/compare?pokemon_a=25&pokemon_b=26")
        data = response.json()

        self.assertIn("pokemon_a", data)
        self.assertIn("pokemon_b", data)
        self.assertIn("stat_comparison", data)
        self.assertIn("summary", data)


if __name__ == "__main__":
    unittest.main()
