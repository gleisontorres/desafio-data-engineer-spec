# Pokemon Data Pipeline

![CI Pipeline](https://github.com/gleisontorres/desafio-data-engineer-spec/actions/workflows/ci.yml/badge.svg)

---

## Visão Geral

Pipeline de dados end-to-end que extrai informações dos 151 Pokémon da primeira geração via PokéAPI, processa e armazena em PostgreSQL, expõe via API REST e permite consultas em linguagem natural através de um Agente de IA.

**Fonte de dados:** [PokéAPI](https://pokeapi.co/) - API pública gratuita com dados completos de Pokémon. Escolhida por oferecer dados semi-estruturados e aninhados que permitem modelagem relacional real, além de possibilitar transformações, normalizações e agregações relevantes.

---

## Arquitetura

```mermaid
flowchart TB
    subgraph External
        POKEAPI[PokeAPI]
    end

    subgraph Docker["Docker Compose"]
        subgraph ETL["Container: etl"]
            E[extract.py]
            T[transform.py]
            L[load.py]
        end

        subgraph DB["Container: db"]
            PG[(PostgreSQL 15)]
        end

        subgraph API["Container: api"]
            FA[FastAPI]
            R[Routers]
        end

        subgraph AGENT["Container: agent"]
            AG[OpenAI Agent]
            TOOLS[Tools]
        end

        subgraph UI["Container: ui"]
            ST[Streamlit]
        end
    end

    subgraph Clients
        CLI[CLI]
        HTTP[HTTP Client]
        BROWSER[Browser]
    end

    POKEAPI -->|HTTP GET| E
    E --> T
    T --> L
    L -->|INSERT/UPSERT| PG
    PG -->|SELECT| FA
    FA --> R
    R -->|JSON| AGENT
    TOOLS --> R
    AG --> TOOLS
    ST -->|POST /ask| AG

    CLI -->|docker compose run| AG
    HTTP -->|POST /ask| AG
    HTTP -->|GET /pokemons| FA
    BROWSER -->|http://localhost:8501| ST
```

### Fluxo de Dados

1. **Extract**: Busca dados brutos da PokéAPI (151 Pokémon + abilities)
2. **Transform**: Limpa, normaliza e estrutura os dados para o modelo relacional
3. **Load**: Persiste no PostgreSQL com upsert (idempotente)
4. **API**: Expõe endpoints REST para consulta dos dados processados
5. **Agent**: Responde perguntas em linguagem natural usando as tools que consultam a API

---

## Tecnologias Utilizadas

| Tecnologia | Versão | Justificativa |
|------------|--------|---------------|
| Python | 3.11+ | Versão LTS com suporte a type hints modernos e performance otimizada |
| FastAPI | 0.109+ | Framework async com validação automática via Pydantic e docs OpenAPI |
| PostgreSQL | 15 | Banco relacional robusto com suporte a UPSERT e JSON |
| SQLAlchemy | 2.0+ | Gerenciamento de conexões e pool; queries em SQL puro para performance |
| psycopg2 | 2.9+ | Driver PostgreSQL nativo de alta performance |
| httpx | 0.27+ | Cliente HTTP moderno com suporte async e retry |
| structlog | 24.1+ | Logging estruturado em JSON para observabilidade |
| OpenAI Agents SDK | 0.1+ | SDK oficial para construção de agentes com function calling |
| Streamlit | 1.32+ | Framework para criação rápida de interfaces web interativas |
| Dozzle | latest | Visualizador de logs Docker em tempo real com interface web |
| Docker | 24+ | Containerização para reproducibilidade e isolamento |
| GitHub Actions | - | CI/CD integrado ao repositório com workflow declarativo |

---

## Pré-requisitos

- **Docker Desktop** 24+ instalado e rodando
- **Conta OpenAI** com API key ativa (modelo gpt-4o-mini ou superior)
- **Git** para clonar o repositório
- **8GB RAM** disponível (recomendado para rodar os 4 containers)

---

## Como Subir o Projeto

### 1. Clonar o repositório

```bash
git clone https://github.com/gleisontorres/desafio-data-engineer-spec.git
cd desafio-data-engineer-spec
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Edite o arquivo `.env` e preencha:

```env
POSTGRES_USER=pokemon_user
POSTGRES_PASSWORD=sua_senha_segura
POSTGRES_DB=pokemon_db
OPENAI_API_KEY=sk-sua-chave-aqui
```

### 3. Subir os containers

```bash
docker compose up --build -d
```

### 4. Verificar status

```bash
docker compose ps
```

Todos os containers devem estar com status `healthy` ou `running`:

```
NAME            STATUS
pokemon_db      healthy
pokemon_api     running
pokemon_agent   running
pokemon_ui      running
```

### 5. Verificar logs (opcional)

```bash
docker compose logs -f api
```

---

## Como Executar a Pipeline ETL

A pipeline ETL extrai os 151 Pokémon da primeira geração, transforma os dados e carrega no PostgreSQL.

### Executar manualmente

```bash
docker compose run etl
```

### O que esperar nos logs

```json
{"event": "pipeline_started", "level": "info", "timestamp": "...", "limit": 151}
{"event": "pokemon_extracted", "level": "info", "pokemon_id": 1, "pokemon_name": "bulbasaur"}
...
{"event": "load_completed", "level": "info", "pokemons": 151, "types": 15, "abilities": 98}
{"event": "pipeline_completed", "level": "info", "total_elapsed_ms": 45000}
```

### Verificar dados carregados

```bash
docker compose exec db psql -U pokemon_user -d pokemon_db -c "SELECT COUNT(*) FROM pokemon;"
```

Resultado esperado: `151`

### Executar com limite reduzido (para testes)

```bash
docker compose run -e POKEMON_LIMIT=10 etl
```

---

## Endpoints da API

A API roda na porta 8000 e possui documentação interativa em `/docs`.

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/pokemons` | Lista Pokémon com paginação |
| GET | `/pokemons/{name_or_id}` | Detalhes de um Pokémon |
| GET | `/pokemons/type/{type}` | Pokémon por tipo |
| GET | `/pokemons/stats/top` | Ranking por stat |
| GET | `/pokemons/compare` | Comparação entre dois Pokémon |
| GET | `/health` | Health check da API |

### Exemplos de uso

**Listar Pokémon (paginado)**

```bash
curl http://localhost:8000/pokemons?limit=5&offset=0
```

```json
{
  "items": [
    {"id": 1, "name": "bulbasaur", "height": 7, "weight": 69, "types": ["grass", "poison"]},
    {"id": 2, "name": "ivysaur", "height": 10, "weight": 130, "types": ["grass", "poison"]}
  ],
  "total": 151,
  "limit": 5,
  "offset": 0
}
```

**Buscar Pokémon por nome**

```bash
curl http://localhost:8000/pokemons/pikachu
```

```json
{
  "id": 25,
  "name": "pikachu",
  "height": 4,
  "weight": 60,
  "base_experience": 112,
  "stats": {
    "hp": 35,
    "attack": 55,
    "defense": 40,
    "special_attack": 50,
    "special_defense": 50,
    "speed": 90
  },
  "types": [{"id": 13, "name": "electric"}],
  "abilities": [{"id": 9, "name": "static", "description": "..."}]
}
```

**Pokémon por tipo**

```bash
curl http://localhost:8000/pokemons/type/fire
```

**Ranking por stat**

```bash
curl "http://localhost:8000/pokemons/stats/top?stat=attack&limit=5"
```

```json
{
  "stat": "attack",
  "items": [
    {"rank": 1, "id": 68, "name": "machamp", "stat_name": "attack", "stat_value": 130},
    {"rank": 2, "id": 57, "name": "primeape", "stat_name": "attack", "stat_value": 105}
  ]
}
```

**Comparar dois Pokémon**

```bash
curl "http://localhost:8000/pokemons/compare?pokemon_a=pikachu&pokemon_b=raichu"
```

```json
{
  "pokemon_a": {"id": 25, "name": "pikachu", "...": "..."},
  "pokemon_b": {"id": 26, "name": "raichu", "...": "..."},
  "stat_comparison": [
    {"stat": "hp", "pokemon_a": 35, "pokemon_b": 60, "diff": -25, "winner": "raichu"},
    {"stat": "speed", "pokemon_a": 90, "pokemon_b": 110, "diff": -20, "winner": "raichu"}
  ],
  "summary": "raichu vence em 6 stats"
}
```

---

## Como Usar o Agente de IA

O Agente responde perguntas sobre Pokémon em linguagem natural, consultando os dados da pipeline.

### Via CLI

```bash
docker compose run agent "Qual Pokémon tem o maior ataque?"
```

**Exemplos de perguntas e respostas:**

| Pergunta | Resposta esperada |
|----------|-------------------|
| `"Qual Pokémon tem o maior ataque?"` | Machamp com 130 de ataque |
| `"Liste os Pokémon do tipo fogo"` | Charmander, Charmeleon, Charizard, Vulpix... |
| `"Compare Pikachu com Raichu"` | Raichu é superior em todos os stats exceto... |
| `"Quais são os 5 Pokémon mais rápidos?"` | Electrode (150), Jolteon (130), Aerodactyl (130)... |
| `"Quais habilidades o Bulbasaur tem?"` | Overgrow e Chlorophyll (hidden) |

### Via POST /ask

O Agente também expõe um endpoint HTTP na porta 8001.

```bash
curl -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Quem é mais forte, Charizard ou Blastoise?"}'
```

```json
{
  "answer": "Comparando Charizard e Blastoise:\n\n- Charizard tem maior Special Attack (109 vs 85)\n- Blastoise tem maior Defense (100 vs 78) e Special Defense (105 vs 85)\n- Ambos têm a mesma Speed (78)\n\nNo geral, Blastoise é mais defensivo enquanto Charizard é mais ofensivo. Depende do estilo de batalha desejado."
}
```

---

## Interface Web

O projeto inclui uma interface web construída com Streamlit para interação visual com o Agente de IA.

### Acesso

Após subir os containers, acesse:

```
http://localhost:8501
```

### Funcionalidades

- **Chat interativo**: Digite perguntas em linguagem natural sobre Pokémon
- **Histórico de conversas**: Visualize todas as perguntas e respostas da sessão
- **Exemplos de perguntas**: Clique em exemplos pré-definidos na barra lateral
- **Indicador de status**: Mostra se o agente está online ou offline
- **Tema escuro**: Interface com identidade visual TOTVS (azul #1B2A4A e laranja #F26522)

### Exemplos de uso

1. Acesse `http://localhost:8501` no navegador
2. Digite uma pergunta como "Qual Pokémon tem o maior ataque?"
3. Clique em "Consultar" e aguarde a resposta do agente
4. O histórico fica salvo durante a sessão

### Perguntas de exemplo disponíveis

- "Qual pokemon tem o maior ataque?"
- "Liste os pokemons do tipo fogo"
- "Compare pikachu e charizard"
- "Quais são os top 5 pokémons por defesa?"
- "Me fale sobre o bulbasaur"

---

## Pipeline CI/CD

O projeto usa GitHub Actions para integração contínua.

### Jobs

| Job | Descrição | Dependência |
|-----|-----------|-------------|
| **lint** | Executa Ruff para verificar estilo e erros de código | - |
| **test** | Roda pytest nos testes unitários | lint |
| **build** | Constrói as imagens Docker para validar que compilam | test |

### Eventos

- **push** na branch `main`
- **pull_request** para branch `main`

### Verificar status

Acesse a aba "Actions" no repositório GitHub ou verifique o badge no topo deste README.

---

## Estrutura do Projeto

```
.
├── .github/workflows/ci.yml    # Pipeline CI/CD
├── api/                        # Serviço FastAPI
│   ├── main.py
│   ├── database.py
│   ├── routers/
│   ├── schemas/
│   ├── Dockerfile
│   └── requirements.txt
├── agent/                      # Agente de IA
│   ├── agent_app.py
│   ├── tools.py
│   ├── logger.py
│   ├── Dockerfile
│   └── requirements.txt
├── etl/                        # Pipeline ETL
│   ├── extract.py
│   ├── transform.py
│   ├── load.py
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── ui/                         # Interface Web Streamlit
│   ├── streamlit_app.py
│   ├── Dockerfile
│   └── requirements.txt
├── db/
│   └── init.sql                # Schema do banco
├── tests/                      # Testes unitários
│   ├── etl/
│   ├── api/
│   └── agent/
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Observabilidade

### Logs em Tempo Real - Dozzle

O projeto inclui o [Dozzle](https://dozzle.dev/), um visualizador de logs Docker com interface web leve e em tempo real.

**Acesso:** `http://localhost:9090`

**Funcionalidades:**

- Visualização de logs de todos os containers em tempo real
- Filtro por container (db, api, agent, etl, ui)
- Busca por texto nos logs
- Download de logs
- Interface responsiva e leve (sem banco de dados, apenas leitura)

**Como usar:**

1. Acesse `http://localhost:9090` no navegador
2. Selecione o container desejado na barra lateral
3. Os logs aparecem em tempo real conforme são gerados
4. Use o campo de busca para filtrar por palavras-chave

O Dozzle é útil para:

- Debug de problemas em tempo real
- Monitorar execução da pipeline ETL
- Acompanhar requisições na API e Agent
- Verificar erros e exceptions

### Logs Estruturados

Todos os serviços Python (ETL, API, Agent) utilizam **structlog** com output em JSON, facilitando:

- Parsing automatizado por ferramentas de observabilidade
- Filtros por campos específicos (module, event, level)
- Correlação de eventos entre serviços

---

## Possíveis Melhorias Futuras

### 1. Cache de requisições na API

**O que é:** Implementar cache Redis para endpoints frequentes como listagem e busca por tipo.

**Por que agrega valor:** Reduz carga no banco e latência de resposta em 10x para consultas repetidas.

### 2. Pipeline incremental

**O que é:** Modificar o ETL para buscar apenas Pokémon novos ou atualizados desde a última execução.

**Por que agrega valor:** Permite rodar a pipeline periodicamente sem reprocessar todos os 151 Pokémon, economizando tempo e requests.

### 3. Tracing distribuído

**O que é:** Integrar OpenTelemetry para rastrear requisições end-to-end entre API, Agent e banco.

**Por que agrega valor:** Facilita debug de problemas de performance e identifica gargalos em produção.

### 4. Autenticação na API

**O que é:** Adicionar JWT ou API keys para proteger os endpoints.

**Por que agrega valor:** Permite controle de acesso e rate limiting por usuário em ambiente de produção.

### 5. Suporte a mais gerações

**O que é:** Expandir a pipeline para extrair Pokémon de todas as gerações (900+).

**Por que agrega valor:** Aumenta a base de dados e possibilita análises mais ricas sobre evolução dos stats ao longo das gerações.

---

## Contato

Desenvolvido para o desafio técnico TOTVS IDEIA - Engenharia de Dados.
