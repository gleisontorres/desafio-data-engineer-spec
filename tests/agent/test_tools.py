"""
Testes unitários para as tools do Agente de IA.

Cobertura:
- buscar_pokemon com sucesso
- buscar_pokemon com 404
- buscar_pokemon com erro de rede
- top_n_por_stat com stat inválido
- comparar_pokemons com Pokemon inexistente
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Adiciona o diretório agent ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agent"))

from tools import (
    buscar_pokemon,
    listar_por_tipo,
    top_n_por_stat,
    comparar_pokemons,
    VALID_STATS,
)


class TestBuscarPokemon(unittest.TestCase):
    """Testes para a tool buscar_pokemon."""

    @patch("tools.httpx.Client")
    def test_buscar_pokemon_success(self, mock_client_class: MagicMock) -> None:
        """buscar_pokemon com Pokemon existente deve retornar dados."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 25,
            "name": "pikachu",
            "height": 4,
            "weight": 60,
            "stats": {"hp": 35, "attack": 55},
        }

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = buscar_pokemon("pikachu")

        self.assertEqual(result["status"], "success")
        self.assertIn("pokemon", result)
        self.assertEqual(result["pokemon"]["name"], "pikachu")

    @patch("tools.httpx.Client")
    def test_buscar_pokemon_not_found(self, mock_client_class: MagicMock) -> None:
        """buscar_pokemon com Pokemon inexistente deve retornar erro amigável."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = buscar_pokemon("pokemon_inexistente")

        self.assertEqual(result["status"], "error")
        self.assertIn("message", result)
        self.assertIn("nao encontrado", result["message"])

    @patch("tools.httpx.Client")
    def test_buscar_pokemon_network_error(self, mock_client_class: MagicMock) -> None:
        """buscar_pokemon com erro de rede não deve levantar exceção."""
        import httpx

        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.RequestError("Connection failed")
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        # Não deve levantar exceção
        result = buscar_pokemon("pikachu")

        self.assertEqual(result["status"], "error")
        self.assertIn("message", result)
        self.assertIn("conexao", result["message"].lower())

    @patch("tools.httpx.Client")
    def test_buscar_pokemon_timeout(self, mock_client_class: MagicMock) -> None:
        """buscar_pokemon com timeout não deve levantar exceção."""
        import httpx

        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.TimeoutException("Timeout")
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = buscar_pokemon("pikachu")

        self.assertEqual(result["status"], "error")
        self.assertIn("timeout", result["message"].lower())


class TestListarPorTipo(unittest.TestCase):
    """Testes para a tool listar_por_tipo."""

    @patch("tools.httpx.Client")
    def test_listar_por_tipo_success(self, mock_client_class: MagicMock) -> None:
        """listar_por_tipo com tipo existente deve retornar lista."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {"id": 25, "name": "pikachu", "types": ["electric"]},
                {"id": 26, "name": "raichu", "types": ["electric"]},
            ],
            "total": 2,
        }

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = listar_por_tipo("electric")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["tipo"], "electric")
        self.assertEqual(result["total"], 2)
        self.assertEqual(len(result["pokemons"]), 2)

    @patch("tools.httpx.Client")
    def test_listar_por_tipo_not_found(self, mock_client_class: MagicMock) -> None:
        """listar_por_tipo com tipo inexistente deve retornar erro."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = listar_por_tipo("tipo_invalido")

        self.assertEqual(result["status"], "error")
        self.assertIn("nao encontrado", result["message"])


class TestTopNPorStat(unittest.TestCase):
    """Testes para a tool top_n_por_stat."""

    def test_top_n_por_stat_invalid_stat(self) -> None:
        """top_n_por_stat com stat inválido deve retornar erro sem chamar API."""
        result = top_n_por_stat("stat_invalido", 10)

        self.assertEqual(result["status"], "error")
        self.assertIn("invalido", result["message"])
        self.assertIn("Stats validos", result["message"])

    def test_valid_stats_list(self) -> None:
        """Deve haver exatamente 6 stats válidos."""
        expected_stats = {
            "hp",
            "attack",
            "defense",
            "special_attack",
            "special_defense",
            "speed",
        }
        self.assertEqual(VALID_STATS, expected_stats)

    @patch("tools.httpx.Client")
    def test_top_n_por_stat_success(self, mock_client_class: MagicMock) -> None:
        """top_n_por_stat com stat válido deve retornar ranking."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "stat": "attack",
            "items": [
                {
                    "rank": 1,
                    "id": 68,
                    "name": "machamp",
                    "stat_name": "attack",
                    "stat_value": 130,
                },
                {
                    "rank": 2,
                    "id": 67,
                    "name": "machoke",
                    "stat_name": "attack",
                    "stat_value": 100,
                },
            ],
        }

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = top_n_por_stat("attack", 10)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["stat"], "attack")
        self.assertIn("ranking", result)

    def test_top_n_por_stat_limits_n(self) -> None:
        """top_n_por_stat deve limitar n a no máximo 50."""
        with patch("tools._make_api_request") as mock_request:
            mock_request.return_value = ({"stat": "hp", "items": []}, 200, None)

            top_n_por_stat("hp", 100)

            # Verifica que chamou com limit=50
            call_args = mock_request.call_args
            self.assertEqual(call_args[1]["params"]["limit"], 50)


class TestCompararPokemons(unittest.TestCase):
    """Testes para a tool comparar_pokemons."""

    @patch("tools.httpx.Client")
    def test_comparar_pokemons_success(self, mock_client_class: MagicMock) -> None:
        """comparar_pokemons com ambos existentes deve retornar comparação."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "pokemon_a": {"id": 25, "name": "pikachu"},
            "pokemon_b": {"id": 26, "name": "raichu"},
            "stat_comparison": [
                {
                    "stat": "attack",
                    "pokemon_a": 55,
                    "pokemon_b": 90,
                    "diff": -35,
                    "winner": "raichu",
                }
            ],
            "summary": "raichu vence em 5 stats",
        }

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = comparar_pokemons("pikachu", "raichu")

        self.assertEqual(result["status"], "success")
        self.assertIn("pokemon_a", result)
        self.assertIn("pokemon_b", result)
        self.assertIn("comparacao", result)
        self.assertIn("resumo", result)

    @patch("tools.httpx.Client")
    def test_comparar_pokemons_one_not_found(
        self, mock_client_class: MagicMock
    ) -> None:
        """comparar_pokemons com um Pokemon inexistente deve retornar erro."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = comparar_pokemons("pikachu", "pokemon_inexistente")

        self.assertEqual(result["status"], "error")
        self.assertIn("nao foram encontrados", result["message"])


class TestToolsReturnStructure(unittest.TestCase):
    """Testes para verificar que todas as tools retornam estrutura correta."""

    @patch("tools.httpx.Client")
    def test_all_tools_return_status_field(self, mock_client_class: MagicMock) -> None:
        """Todas as tools devem retornar dict com campo 'status'."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"items": [], "total": 0}

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        tools_and_args = [
            (buscar_pokemon, ("pikachu",)),
            (listar_por_tipo, ("fire",)),
            (top_n_por_stat, ("attack", 5)),
            (comparar_pokemons, ("pikachu", "raichu")),
        ]

        for tool_func, args in tools_and_args:
            result = tool_func(*args)
            self.assertIn(
                "status", result, f"{tool_func.__name__} deve retornar 'status'"
            )
            self.assertIn(result["status"], ["success", "error"])


if __name__ == "__main__":
    unittest.main()
