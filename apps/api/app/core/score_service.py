"""Score financeiro: indicador composto 0-1000, simples e explicavel (cada
componente mostra seus pontos, nada de caixa-preta). Pesos: poupanca 400,
aderencia ao orcamento 300, saldo sem previsao de ficar negativo 200,
patrimonio liquido positivo 100.
"""
from datetime import date

from sqlalchemy.orm import Session

from ..models import Usuario
from .aposentadoria_service import patrimonio_atual
from .dre_service import dre
from .forecast_service import projetar_saldo
from .orcamento_service import comparativo


def _classificar(score: int) -> str:
    if score >= 800:
        return "Excelente"
    if score >= 600:
        return "Bom"
    if score >= 400:
        return "Regular"
    if score >= 200:
        return "Atencao"
    return "Critico"


def calcular(db: Session, usuario: Usuario) -> dict:
    hoje = date.today()

    dre_atual = dre(db, usuario, hoje.year, hoje.month)["atual"]
    receitas, resultado = dre_atual["receitas"], dre_atual["resultado"]
    taxa_poupanca = (resultado / receitas) if receitas > 0 else 0.0
    pontos_poupanca = round(max(0.0, min(taxa_poupanca, 1.0)) * 400, 1)

    comp = comparativo(db, usuario, hoje.year, hoje.month)
    com_orcamento = [linha for linha in comp["categorias"] if linha["orcado"]]
    if com_orcamento:
        dentro_do_orcado = sum(1 for linha in com_orcamento if linha["realizado"] <= linha["orcado"])
        pontos_orcamento = round((dentro_do_orcado / len(com_orcamento)) * 300, 1)
    else:
        pontos_orcamento = 150.0  # sem orcamento cadastrado: neutro, nem penaliza nem premia

    saldos = projetar_saldo(db, usuario, dias=30)
    sem_saldo_negativo = all(p["saldo"] >= 0 for conta in saldos for p in conta["pontos"]) if saldos else True
    pontos_saldo = 200.0 if sem_saldo_negativo else 0.0

    pontos_patrimonio = 100.0 if patrimonio_atual(db, usuario) > 0 else 0.0

    score = round(pontos_poupanca + pontos_orcamento + pontos_saldo + pontos_patrimonio)

    return {
        "score": score,
        "score_max": 1000,
        "classificacao": _classificar(score),
        "componentes": {
            "taxa_poupanca_mes": {
                "valor_pct": round(taxa_poupanca * 100, 1), "pontos": pontos_poupanca, "pontos_max": 400,
            },
            "aderencia_orcamento_mes": {"pontos": pontos_orcamento, "pontos_max": 300},
            "saldo_30d_sem_negativo": {"pontos": pontos_saldo, "pontos_max": 200},
            "patrimonio_liquido_positivo": {"pontos": pontos_patrimonio, "pontos_max": 100},
        },
    }
