#!/bin/bash
# ===========================================
# Script para executar a pipeline ETL
# ===========================================

set -e

echo "=== Pokemon ETL Pipeline ==="
echo ""

# Verifica se o banco está pronto
echo "[1/4] Verificando conexao com o banco..."
docker compose exec -T db pg_isready -U "${POSTGRES_USER:-pokemon_user}" -d "${POSTGRES_DB:-pokemon_db}"

if [ $? -ne 0 ]; then
    echo "ERRO: Banco de dados nao esta pronto. Execute 'docker compose up -d db' primeiro."
    exit 1
fi

echo "[2/4] Banco de dados pronto."
echo ""

# Executa a pipeline
echo "[3/4] Executando pipeline ETL..."
echo ""

docker compose run --rm etl

echo ""
echo "[4/4] Pipeline concluida."
echo ""

# Mostra contagem de registros
echo "=== Resumo dos dados carregados ==="
docker compose exec -T db psql -U "${POSTGRES_USER:-pokemon_user}" -d "${POSTGRES_DB:-pokemon_db}" -c "
SELECT 
    'pokemon' as tabela, COUNT(*) as registros FROM pokemon
UNION ALL
SELECT 'types', COUNT(*) FROM types
UNION ALL
SELECT 'abilities', COUNT(*) FROM abilities
UNION ALL
SELECT 'stats', COUNT(*) FROM stats
ORDER BY tabela;
"

echo ""
echo "Pipeline executada com sucesso!"
