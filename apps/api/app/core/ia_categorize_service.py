"""Classificacao por IA (Claude) dos eventos que sobraram em 'nao_classificado'.

Le a descricao (normalmente nome do fornecedor/estabelecimento) e escolhe a
melhor categoria da taxonomia. Deduplica por chave de merchant para classificar
cada fornecedor uma unica vez (economiza chamadas/custo) e aplica o resultado a
todos os eventos daquele fornecedor. Os eventos classificados pela IA ficam com
categoria_fonte='IA' (distinguivel das classificacoes do usuario).

So envia para a Anthropic a DESCRICAO da transacao -- nunca saldo, numero de
conta, ou dados pessoais alem do que ja consta na propria descricao.
"""
import json

from sqlalchemy.orm import Session

from ..config import settings
from ..models import Evento, Usuario
from .categorize import CATEGORIAS_VALIDAS
from .normalize import chave_memoria

MODELO_IA = "claude-haiku-4-5-20251001"
LOTE = 40  # descricoes por chamada

# Categorias que a IA nao deve escolher para um fornecedor (neutras / genericas).
_BLOQUEADAS = {"nao_classificado", "neutro", "pagamento_cartao"}
_CATS_IA = [c for c in CATEGORIAS_VALIDAS if c not in _BLOQUEADAS]

_SYSTEM = (
    "Voce e um categorizador de transacoes financeiras pessoais no Brasil. "
    "Recebe descricoes de transacoes bancarias e de cartao (geralmente o nome "
    "do estabelecimento/fornecedor) e escolhe a categoria mais provavel de uma "
    "lista fixa. Responda SOMENTE com um objeto JSON valido mapeando o indice "
    "(string) para a categoria escolhida, sem texto antes ou depois. Quando nao "
    "houver pista razoavel do tipo de gasto, use 'nao_classificado'."
)


def _classificar_descricoes(descricoes: list[str]) -> dict[int, str]:
    """Chama o Claude em lotes e retorna {indice_global: categoria}."""
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    cats = ", ".join(_CATS_IA) + ", nao_classificado"
    resultado: dict[int, str] = {}

    for inicio in range(0, len(descricoes), LOTE):
        bloco = descricoes[inicio:inicio + LOTE]
        linhas = "\n".join(f"{i}: {d}" for i, d in enumerate(bloco))
        prompt = (
            f"Categorias permitidas (use exatamente uma destas strings): {cats}.\n\n"
            f"Transacoes (indice: descricao):\n{linhas}\n\n"
            "Retorne JSON {\"0\": \"categoria\", \"1\": \"categoria\", ...} "
            "para todos os indices acima."
        )
        msg = client.messages.create(
            model=MODELO_IA,
            max_tokens=2000,
            system=_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        texto = "".join(b.text for b in msg.content if getattr(b, "type", None) == "text").strip()
        try:
            ini_j = texto.index("{")
            fim_j = texto.rindex("}") + 1
            mapa = json.loads(texto[ini_j:fim_j])
        except (ValueError, json.JSONDecodeError):
            mapa = {}
        for k, v in mapa.items():
            try:
                idx_local = int(k)
            except (ValueError, TypeError):
                continue
            cat = v if isinstance(v, str) and v in CATEGORIAS_VALIDAS else "nao_classificado"
            resultado[inicio + idx_local] = cat

    return resultado


def classificar_pendentes_ia(db: Session, usuario: Usuario) -> dict:
    """Classifica com IA todos os eventos 'nao_classificado' do usuario."""
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY nao configurada na API.")

    pendentes = (
        db.query(Evento)
        .filter(Evento.usuario_id == usuario.id, Evento.categoria_id == "nao_classificado")
        .all()
    )
    if not pendentes:
        return {"classificados": 0, "fornecedores_reconhecidos": 0, "pendentes_restantes": 0}

    # deduplica por fornecedor (mesma chave de merchant -> uma classificacao so)
    por_chave: dict[str, list[Evento]] = {}
    for ev in pendentes:
        chave = chave_memoria(ev.descricao) or (ev.descricao or "").strip().lower()
        por_chave.setdefault(chave, []).append(ev)

    chaves = list(por_chave.keys())
    descricoes = [por_chave[c][0].descricao or "" for c in chaves]
    mapa_idx = _classificar_descricoes(descricoes)

    classificados = 0
    fornecedores = 0
    for idx, chave in enumerate(chaves):
        cat = mapa_idx.get(idx, "nao_classificado")
        if cat == "nao_classificado" or cat in _BLOQUEADAS:
            continue
        fornecedores += 1
        for ev in por_chave[chave]:
            ev.categoria_id = cat
            ev.categoria_fonte = "IA"
            ev.categoria_confianca = 0.7
            classificados += 1
    db.commit()

    return {
        "classificados": classificados,
        "fornecedores_reconhecidos": fornecedores,
        "pendentes_restantes": len(pendentes) - classificados,
    }
