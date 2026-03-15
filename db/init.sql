-- ===========================================
-- Pokemon Database Schema
-- Desafio Data Engineer - TOTVS IDEIA
-- ===========================================

-- Habilita extensão para UUIDs (opcional, se necessário no futuro)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===========================================
-- Tabela: pokemon
-- Dados base dos Pokémon extraídos da PokéAPI
-- ===========================================
CREATE TABLE IF NOT EXISTS pokemon (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    height INTEGER NOT NULL,
    weight INTEGER NOT NULL,
    base_experience INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pokemon_name ON pokemon(name);

-- ===========================================
-- Tabela: types
-- Tipos de Pokémon (fire, water, grass, etc.)
-- ===========================================
CREATE TABLE IF NOT EXISTS types (
    id INTEGER PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_types_name ON types(name);

-- ===========================================
-- Tabela: pokemon_types
-- Relação N:N entre pokemon e types
-- Um Pokémon pode ter múltiplos tipos (ex: Charizard = fire + flying)
-- ===========================================
CREATE TABLE IF NOT EXISTS pokemon_types (
    pokemon_id INTEGER NOT NULL,
    type_id INTEGER NOT NULL,
    slot INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (pokemon_id, type_id),
    CONSTRAINT fk_pokemon_types_pokemon
        FOREIGN KEY (pokemon_id)
        REFERENCES pokemon(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_pokemon_types_type
        FOREIGN KEY (type_id)
        REFERENCES types(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_pokemon_types_pokemon_id ON pokemon_types(pokemon_id);
CREATE INDEX IF NOT EXISTS idx_pokemon_types_type_id ON pokemon_types(type_id);

-- ===========================================
-- Tabela: stats
-- Estatísticas base de cada Pokémon
-- Relação 1:1 com pokemon (um registro por pokemon)
-- ===========================================
CREATE TABLE IF NOT EXISTS stats (
    id SERIAL PRIMARY KEY,
    pokemon_id INTEGER NOT NULL UNIQUE,
    hp INTEGER NOT NULL DEFAULT 0,
    attack INTEGER NOT NULL DEFAULT 0,
    defense INTEGER NOT NULL DEFAULT 0,
    special_attack INTEGER NOT NULL DEFAULT 0,
    special_defense INTEGER NOT NULL DEFAULT 0,
    speed INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_stats_pokemon
        FOREIGN KEY (pokemon_id)
        REFERENCES pokemon(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_stats_pokemon_id ON stats(pokemon_id);
CREATE INDEX IF NOT EXISTS idx_stats_hp ON stats(hp DESC);
CREATE INDEX IF NOT EXISTS idx_stats_attack ON stats(attack DESC);
CREATE INDEX IF NOT EXISTS idx_stats_defense ON stats(defense DESC);
CREATE INDEX IF NOT EXISTS idx_stats_speed ON stats(speed DESC);

-- ===========================================
-- Tabela: abilities
-- Habilidades dos Pokémon
-- ===========================================
CREATE TABLE IF NOT EXISTS abilities (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_abilities_name ON abilities(name);

-- ===========================================
-- Tabela: pokemon_abilities
-- Relação N:N entre pokemon e abilities
-- Um Pokémon pode ter múltiplas habilidades
-- ===========================================
CREATE TABLE IF NOT EXISTS pokemon_abilities (
    pokemon_id INTEGER NOT NULL,
    ability_id INTEGER NOT NULL,
    is_hidden BOOLEAN NOT NULL DEFAULT FALSE,
    slot INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (pokemon_id, ability_id),
    CONSTRAINT fk_pokemon_abilities_pokemon
        FOREIGN KEY (pokemon_id)
        REFERENCES pokemon(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_pokemon_abilities_ability
        FOREIGN KEY (ability_id)
        REFERENCES abilities(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_pokemon_abilities_pokemon_id ON pokemon_abilities(pokemon_id);
CREATE INDEX IF NOT EXISTS idx_pokemon_abilities_ability_id ON pokemon_abilities(ability_id);

-- ===========================================
-- Função: Atualiza updated_at automaticamente
-- ===========================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ===========================================
-- Triggers: Auto-update de updated_at
-- ===========================================
DROP TRIGGER IF EXISTS trigger_pokemon_updated_at ON pokemon;
CREATE TRIGGER trigger_pokemon_updated_at
    BEFORE UPDATE ON pokemon
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_types_updated_at ON types;
CREATE TRIGGER trigger_types_updated_at
    BEFORE UPDATE ON types
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_stats_updated_at ON stats;
CREATE TRIGGER trigger_stats_updated_at
    BEFORE UPDATE ON stats
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_abilities_updated_at ON abilities;
CREATE TRIGGER trigger_abilities_updated_at
    BEFORE UPDATE ON abilities
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ===========================================
-- Comentários nas tabelas (documentação)
-- ===========================================
COMMENT ON TABLE pokemon IS 'Dados base dos Pokémon extraídos da PokéAPI';
COMMENT ON TABLE types IS 'Tipos de Pokémon (fire, water, grass, etc.)';
COMMENT ON TABLE pokemon_types IS 'Relação N:N entre Pokémon e seus tipos';
COMMENT ON TABLE stats IS 'Estatísticas base de cada Pokémon (HP, Attack, etc.)';
COMMENT ON TABLE abilities IS 'Habilidades disponíveis dos Pokémon';
COMMENT ON TABLE pokemon_abilities IS 'Relação N:N entre Pokémon e suas habilidades';
