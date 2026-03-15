"""
Agente de IA para consultas sobre Pokemon.

Usa OpenAI Agents SDK para processar perguntas em linguagem natural
e consultar dados via tools que acessam a API REST.

Modos de execução:
1. CLI: python agent_app.py "pergunta"
2. API: POST /ask {"question": "..."}
"""

import asyncio
import os
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agents import Agent, Runner, function_tool

from logger import get_logger
from tools import (
    buscar_pokemon,
    listar_por_tipo,
    top_n_por_stat,
    comparar_pokemons,
)

logger = get_logger("agent_app")

# Configurações
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# System prompt do agente
SYSTEM_PROMPT = """Voce e um assistente especialista em Pokemon. Seu objetivo e responder 
perguntas sobre Pokemon de forma clara, precisa e amigavel.

Voce tem acesso a ferramentas que consultam um banco de dados com informacoes dos 
primeiros 151 Pokemon (geracao 1). Use essas ferramentas para obter dados reais 
antes de responder.

Regras:
1. Sempre use as ferramentas disponiveis para buscar dados antes de responder
2. Se nao encontrar um Pokemon, informe educadamente que ele nao esta no banco
3. Ao comparar Pokemon, destaque as diferencas mais relevantes
4. Responda em portugues brasileiro
5. Seja conciso, mas informativo
6. Quando mostrar stats, explique o que cada um significa se o usuario parecer iniciante

Ferramentas disponiveis:
- buscar_pokemon: busca detalhes de um Pokemon especifico
- listar_por_tipo: lista Pokemon de um tipo (fire, water, etc)
- top_n_por_stat: ranking dos Pokemon por um stat (attack, speed, etc)
- comparar_pokemons: compara dois Pokemon lado a lado
"""


# Converte as funções em tools do SDK
@function_tool
def tool_buscar_pokemon(nome_ou_id: str) -> dict:
    """
    Busca informacoes detalhadas de um Pokemon pelo nome ou ID.

    Args:
        nome_ou_id: Nome do Pokemon (ex: pikachu) ou ID numerico (ex: 25)
    """
    return buscar_pokemon(nome_ou_id)


@function_tool
def tool_listar_por_tipo(tipo: str) -> dict:
    """
    Lista todos os Pokemons de um tipo especifico.

    Args:
        tipo: Nome do tipo em ingles (fire, water, electric, grass, etc)
    """
    return listar_por_tipo(tipo)


@function_tool
def tool_top_n_por_stat(stat: str, n: int = 10) -> dict:
    """
    Retorna ranking dos Pokemons com maiores valores em um stat.
    Stats validos: hp, attack, defense, special_attack, special_defense, speed.

    Args:
        stat: Nome do stat (hp, attack, defense, special_attack, special_defense, speed)
        n: Quantidade no ranking (padrao 10, maximo 50)
    """
    return top_n_por_stat(stat, n)


@function_tool
def tool_comparar_pokemons(pokemon_a: str, pokemon_b: str) -> dict:
    """
    Compara dois Pokemons lado a lado mostrando stats e qual e superior.

    Args:
        pokemon_a: Nome ou ID do primeiro Pokemon
        pokemon_b: Nome ou ID do segundo Pokemon
    """
    return comparar_pokemons(pokemon_a, pokemon_b)


# Cria o agente
agent = Agent(
    name="Pokemon Expert",
    instructions=SYSTEM_PROMPT,
    model=OPENAI_MODEL,
    tools=[
        tool_buscar_pokemon,
        tool_listar_por_tipo,
        tool_top_n_por_stat,
        tool_comparar_pokemons,
    ],
)


async def ask_agent(question: str) -> str:
    """
    Envia uma pergunta ao agente e retorna a resposta.

    Args:
        question: Pergunta em linguagem natural.

    Returns:
        Resposta do agente.
    """
    logger.info(
        "agent_query_started",
        question=question[:100],
    )

    try:
        result = await Runner.run(agent, question)
        answer = result.final_output

        logger.info(
            "agent_query_completed",
            question=question[:100],
            answer_length=len(answer) if answer else 0,
        )

        return answer

    except Exception as e:
        logger.error(
            "agent_query_failed",
            question=question[:100],
            error=str(e),
        )
        raise


# ============================================
# Modo API (FastAPI)
# ============================================


class AskRequest(BaseModel):
    """Request para o endpoint /ask."""

    question: str


class AskResponse(BaseModel):
    """Response do endpoint /ask."""

    answer: str


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Gerencia ciclo de vida da aplicação."""
    logger.info("agent_api_startup")
    yield
    logger.info("agent_api_shutdown")


app = FastAPI(
    title="Pokemon AI Agent",
    description="Agente de IA para responder perguntas sobre Pokemon",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/ask", response_model=AskResponse)
async def ask_endpoint(request: AskRequest) -> AskResponse:
    """
    Endpoint para fazer perguntas ao agente.

    Recebe uma pergunta em linguagem natural e retorna a resposta do agente.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Pergunta nao pode ser vazia")

    try:
        answer = await ask_agent(request.question)
        return AskResponse(answer=answer)

    except Exception as e:
        logger.error(
            "ask_endpoint_error",
            error=str(e),
        )
        raise HTTPException(
            status_code=500,
            detail="Erro ao processar pergunta. Tente novamente.",
        )


@app.get("/health")
def health_check() -> dict:
    """Health check do agente."""
    return {"status": "healthy", "agent": "Pokemon Expert"}


# ============================================
# Modo CLI
# ============================================


def run_cli(question: str) -> None:
    """
    Executa o agente no modo CLI.

    Args:
        question: Pergunta do usuário.
    """
    logger.info(
        "cli_mode_started",
        question=question[:100],
    )

    answer = asyncio.run(ask_agent(question))

    # Output para stdout (não usar print em produção, mas CLI precisa mostrar resultado)
    import sys

    sys.stdout.write(f"\n{answer}\n")


def run_api() -> None:
    """Inicia o servidor API via uvicorn."""
    import uvicorn

    logger.info("agent_api_starting", port=8001)
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")


def main() -> int:
    """
    Entry point principal.

    Detecta o modo de execução baseado nos argumentos:
    - --api-mode ou sem argumentos: inicia servidor API
    - Qualquer outro argumento: modo CLI com a pergunta
    """
    if len(sys.argv) == 1:
        # Sem argumentos: modo API
        run_api()
        return 0

    if sys.argv[1] == "--api-mode":
        # Flag explícita para modo API
        run_api()
        return 0

    # Modo CLI - trata todos os argumentos como pergunta
    question = " ".join(sys.argv[1:])
    run_cli(question)
    return 0


if __name__ == "__main__":
    sys.exit(main())
