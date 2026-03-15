"""
Testes unitários para o módulo transform.py.

Cobertura:
- clean_pokemon com campos nulos
- clean_pokemon com tipos incorretos
- transform_pokemons verificando deduplicação
- normalize_stat nos valores limite
"""

import unittest
import sys
from pathlib import Path

# Adiciona o diretório etl ao path para importação
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "etl"))

from transform import (
    clean_pokemon,
    normalize_stat,
    transform_pokemons,
    TransformationError,
)


class TestNormalizeStat(unittest.TestCase):
    """Testes para a função normalize_stat."""

    def test_normalize_stat_zero(self) -> None:
        """Valor zero deve retornar 0.0."""
        result = normalize_stat(0)
        self.assertEqual(result, 0.0)

    def test_normalize_stat_max(self) -> None:
        """Valor máximo (255) deve retornar 1.0."""
        result = normalize_stat(255)
        self.assertEqual(result, 1.0)

    def test_normalize_stat_middle(self) -> None:
        """Valor intermediário deve retornar proporção correta."""
        result = normalize_stat(127)
        self.assertAlmostEqual(result, 0.498, places=3)

    def test_normalize_stat_negative(self) -> None:
        """Valor negativo deve ser tratado como zero."""
        result = normalize_stat(-10)
        self.assertEqual(result, 0.0)

    def test_normalize_stat_above_max(self) -> None:
        """Valor acima do máximo deve ser limitado a 1.0."""
        result = normalize_stat(300)
        self.assertEqual(result, 1.0)

    def test_normalize_stat_custom_max(self) -> None:
        """Deve funcionar com max_value customizado."""
        result = normalize_stat(50, max_value=100)
        self.assertEqual(result, 0.5)

    def test_normalize_stat_zero_max(self) -> None:
        """max_value zero deve retornar 0.0 (evita divisão por zero)."""
        result = normalize_stat(100, max_value=0)
        self.assertEqual(result, 0.0)


class TestCleanPokemon(unittest.TestCase):
    """Testes para a função clean_pokemon."""

    def setUp(self) -> None:
        """Dados de teste válidos para reutilização."""
        self.valid_pokemon = {
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
                    "description": "Paralyzes on contact.",
                },
            ],
        }

    def test_clean_pokemon_valid_data(self) -> None:
        """Dados válidos devem ser processados corretamente."""
        result = clean_pokemon(self.valid_pokemon)

        self.assertEqual(result["id"], 25)
        self.assertEqual(result["name"], "pikachu")
        self.assertEqual(result["height"], 4)
        self.assertEqual(result["weight"], 60)
        self.assertEqual(result["base_experience"], 112)

    def test_clean_pokemon_stats_structure(self) -> None:
        """Stats devem ter estrutura correta com todos os campos."""
        result = clean_pokemon(self.valid_pokemon)

        self.assertIn("stats", result)
        self.assertIn("hp", result["stats"])
        self.assertIn("attack", result["stats"])
        self.assertIn("defense", result["stats"])
        self.assertIn("special_attack", result["stats"])
        self.assertIn("special_defense", result["stats"])
        self.assertIn("speed", result["stats"])

        self.assertEqual(result["stats"]["hp"], 35)
        self.assertEqual(result["stats"]["speed"], 90)

    def test_clean_pokemon_stats_normalized(self) -> None:
        """Stats normalizados devem estar presentes."""
        result = clean_pokemon(self.valid_pokemon)

        self.assertIn("stats_normalized", result)
        self.assertAlmostEqual(result["stats_normalized"]["speed"], 90 / 255, places=3)

    def test_clean_pokemon_null_base_experience(self) -> None:
        """base_experience nulo deve usar valor padrão 0."""
        pokemon = self.valid_pokemon.copy()
        pokemon["base_experience"] = None

        result = clean_pokemon(pokemon)

        self.assertEqual(result["base_experience"], 0)

    def test_clean_pokemon_missing_base_experience(self) -> None:
        """base_experience ausente deve usar valor padrão 0."""
        pokemon = self.valid_pokemon.copy()
        del pokemon["base_experience"]

        result = clean_pokemon(pokemon)

        self.assertEqual(result["base_experience"], 0)

    def test_clean_pokemon_wrong_type_height(self) -> None:
        """height com tipo errado deve ser convertido para int."""
        pokemon = self.valid_pokemon.copy()
        pokemon["height"] = "4"

        result = clean_pokemon(pokemon)

        self.assertEqual(result["height"], 4)
        self.assertIsInstance(result["height"], int)

    def test_clean_pokemon_wrong_type_weight(self) -> None:
        """weight com tipo errado deve ser convertido para int."""
        pokemon = self.valid_pokemon.copy()
        pokemon["weight"] = "60.5"

        result = clean_pokemon(pokemon)

        self.assertEqual(result["weight"], 60)
        self.assertIsInstance(result["weight"], int)

    def test_clean_pokemon_null_id_raises(self) -> None:
        """id nulo deve levantar TransformationError."""
        pokemon = self.valid_pokemon.copy()
        pokemon["id"] = None

        with self.assertRaises(TransformationError):
            clean_pokemon(pokemon)

    def test_clean_pokemon_empty_name_raises(self) -> None:
        """name vazio deve levantar TransformationError."""
        pokemon = self.valid_pokemon.copy()
        pokemon["name"] = ""

        with self.assertRaises(TransformationError):
            clean_pokemon(pokemon)

    def test_clean_pokemon_missing_stats(self) -> None:
        """Stats ausentes devem ser preenchidos com zero."""
        pokemon = self.valid_pokemon.copy()
        pokemon["stats"] = []

        result = clean_pokemon(pokemon)

        for stat_name in [
            "hp",
            "attack",
            "defense",
            "special_attack",
            "special_defense",
            "speed",
        ]:
            self.assertEqual(result["stats"][stat_name], 0)

    def test_clean_pokemon_invalid_type_filtered(self) -> None:
        """Types com type_id inválido devem ser filtrados."""
        pokemon = self.valid_pokemon.copy()
        pokemon["types"] = [
            {"slot": 1, "type_id": 0, "type_name": "invalid"},
            {"slot": 2, "type_id": 13, "type_name": "electric"},
        ]

        result = clean_pokemon(pokemon)

        self.assertEqual(len(result["types"]), 1)
        self.assertEqual(result["types"][0]["type_id"], 13)

    def test_clean_pokemon_invalid_ability_filtered(self) -> None:
        """Abilities com ability_id inválido devem ser filtradas."""
        pokemon = self.valid_pokemon.copy()
        pokemon["abilities"] = [
            {
                "slot": 1,
                "is_hidden": False,
                "ability_id": None,
                "ability_name": "invalid",
                "description": "",
            },
            {
                "slot": 2,
                "is_hidden": True,
                "ability_id": 9,
                "ability_name": "static",
                "description": "Works",
            },
        ]

        result = clean_pokemon(pokemon)

        self.assertEqual(len(result["abilities"]), 1)
        self.assertEqual(result["abilities"][0]["ability_id"], 9)

    def test_clean_pokemon_strips_name_whitespace(self) -> None:
        """name com espaços deve ser trimado."""
        pokemon = self.valid_pokemon.copy()
        pokemon["name"] = "  pikachu  "

        result = clean_pokemon(pokemon)

        self.assertEqual(result["name"], "pikachu")


class TestTransformPokemons(unittest.TestCase):
    """Testes para a função transform_pokemons."""

    def setUp(self) -> None:
        """Dados de teste com múltiplos Pokémon."""
        self.pokemon_list = [
            {
                "id": 1,
                "name": "bulbasaur",
                "height": 7,
                "weight": 69,
                "base_experience": 64,
                "stats": [
                    {"name": "hp", "base_stat": 45},
                    {"name": "attack", "base_stat": 49},
                    {"name": "defense", "base_stat": 49},
                    {"name": "special-attack", "base_stat": 65},
                    {"name": "special-defense", "base_stat": 65},
                    {"name": "speed", "base_stat": 45},
                ],
                "types": [
                    {"slot": 1, "type_id": 12, "type_name": "grass"},
                    {"slot": 2, "type_id": 4, "type_name": "poison"},
                ],
                "abilities": [
                    {
                        "slot": 1,
                        "is_hidden": False,
                        "ability_id": 65,
                        "ability_name": "overgrow",
                        "description": "Powers up Grass-type moves.",
                    },
                ],
            },
            {
                "id": 2,
                "name": "ivysaur",
                "height": 10,
                "weight": 130,
                "base_experience": 142,
                "stats": [
                    {"name": "hp", "base_stat": 60},
                    {"name": "attack", "base_stat": 62},
                    {"name": "defense", "base_stat": 63},
                    {"name": "special-attack", "base_stat": 80},
                    {"name": "special-defense", "base_stat": 80},
                    {"name": "speed", "base_stat": 60},
                ],
                "types": [
                    {"slot": 1, "type_id": 12, "type_name": "grass"},
                    {"slot": 2, "type_id": 4, "type_name": "poison"},
                ],
                "abilities": [
                    {
                        "slot": 1,
                        "is_hidden": False,
                        "ability_id": 65,
                        "ability_name": "overgrow",
                        "description": "Powers up Grass-type moves.",
                    },
                ],
            },
        ]

    def test_transform_returns_all_keys(self) -> None:
        """Resultado deve conter todas as chaves esperadas."""
        result = transform_pokemons(self.pokemon_list)

        self.assertIn("pokemons", result)
        self.assertIn("types", result)
        self.assertIn("pokemon_types", result)
        self.assertIn("stats", result)
        self.assertIn("abilities", result)
        self.assertIn("pokemon_abilities", result)

    def test_transform_pokemons_count(self) -> None:
        """Deve ter o número correto de Pokémon processados."""
        result = transform_pokemons(self.pokemon_list)

        self.assertEqual(len(result["pokemons"]), 2)

    def test_transform_types_deduplicated(self) -> None:
        """Types devem ser únicos (sem duplicatas)."""
        result = transform_pokemons(self.pokemon_list)

        # Ambos Pokémon têm grass e poison, mas devem aparecer só uma vez
        self.assertEqual(len(result["types"]), 2)
        type_names = [t["name"] for t in result["types"]]
        self.assertIn("grass", type_names)
        self.assertIn("poison", type_names)

    def test_transform_abilities_deduplicated(self) -> None:
        """Abilities devem ser únicas (sem duplicatas)."""
        result = transform_pokemons(self.pokemon_list)

        # Ambos têm overgrow, deve aparecer só uma vez
        self.assertEqual(len(result["abilities"]), 1)
        self.assertEqual(result["abilities"][0]["name"], "overgrow")

    def test_transform_pokemon_types_relations(self) -> None:
        """Relações pokemon_types devem incluir todas as combinações."""
        result = transform_pokemons(self.pokemon_list)

        # 2 Pokémon x 2 tipos cada = 4 relações
        self.assertEqual(len(result["pokemon_types"]), 4)

    def test_transform_pokemon_abilities_relations(self) -> None:
        """Relações pokemon_abilities devem incluir todas as combinações."""
        result = transform_pokemons(self.pokemon_list)

        # 2 Pokémon x 1 ability cada = 2 relações
        self.assertEqual(len(result["pokemon_abilities"]), 2)

    def test_transform_stats_count(self) -> None:
        """Deve ter um registro de stats por Pokémon."""
        result = transform_pokemons(self.pokemon_list)

        self.assertEqual(len(result["stats"]), 2)

    def test_transform_empty_list(self) -> None:
        """Lista vazia deve retornar estrutura vazia."""
        result = transform_pokemons([])

        self.assertEqual(len(result["pokemons"]), 0)
        self.assertEqual(len(result["types"]), 0)
        self.assertEqual(len(result["abilities"]), 0)

    def test_transform_invalid_pokemon_skipped(self) -> None:
        """Pokémon inválido deve ser ignorado sem quebrar o pipeline."""
        pokemon_list = self.pokemon_list + [{"id": None, "name": "invalid"}]

        result = transform_pokemons(pokemon_list)

        # Deve processar apenas os 2 válidos
        self.assertEqual(len(result["pokemons"]), 2)

    def test_transform_types_sorted_by_id(self) -> None:
        """Types devem estar ordenados por id."""
        result = transform_pokemons(self.pokemon_list)

        type_ids = [t["id"] for t in result["types"]]
        self.assertEqual(type_ids, sorted(type_ids))

    def test_transform_abilities_sorted_by_id(self) -> None:
        """Abilities devem estar ordenadas por id."""
        result = transform_pokemons(self.pokemon_list)

        ability_ids = [a["id"] for a in result["abilities"]]
        self.assertEqual(ability_ids, sorted(ability_ids))


if __name__ == "__main__":
    unittest.main()
