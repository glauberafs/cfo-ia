"""Projecao de patrimonio e aposentadoria.

Modelo simples de acumulo (aportes mensais + juros compostos) e, na
aposentadoria, renda passiva sustentavel calculada como perpetuidade
(retira-se so o rendimento, preservando o principal). Taxa de retorno e
considerada REAL (ja acima da inflacao) -- evita ter que projetar inflacao
separadamente.

Patrimonio atual = saldo das contas (Pluggy/demo) + ativos cadastrados a mao
em apps/api/app/core/patrimonio_service.py (investimentos, imoveis etc -- a
Pluggy pessoal nao traz posicao de carteira, so movimentacao).
"""
from sqlalchemy.orm import Session

from ..models import PerfilAposentadoria, Usuario
from .patrimonio_service import resumo as resumo_patrimonio


def patrimonio_atual(db: Session, usuario: Usuario) -> float:
    return resumo_patrimonio(db, usuario)["total"]


def upsert_perfil(db: Session, usuario: Usuario, dados: dict) -> PerfilAposentadoria:
    perfil = db.query(PerfilAposentadoria).filter(PerfilAposentadoria.usuario_id == usuario.id).first()
    if perfil:
        for k, v in dados.items():
            setattr(perfil, k, v)
    else:
        perfil = PerfilAposentadoria(usuario_id=usuario.id, **dados)
        db.add(perfil)
    db.commit()
    db.refresh(perfil)
    return perfil


def _taxa_mensal(taxa_anual_pct: float) -> float:
    return (1 + taxa_anual_pct / 100) ** (1 / 12) - 1


def _valor_futuro(principal: float, aporte_mensal: float, taxa_mensal: float, meses: int) -> float:
    if taxa_mensal == 0:
        return principal + aporte_mensal * meses
    fator = (1 + taxa_mensal) ** meses
    return principal * fator + aporte_mensal * ((fator - 1) / taxa_mensal)


def projetar(db: Session, usuario: Usuario, perfil: PerfilAposentadoria) -> dict:
    patrimonio = patrimonio_atual(db, usuario)
    meses_restantes = max((perfil.idade_aposentadoria - perfil.idade_atual) * 12, 0)
    taxa_m = _taxa_mensal(perfil.taxa_retorno_anual_pct)

    trajetoria = []
    for ano in range(0, meses_restantes // 12 + 1):
        meses = ano * 12
        valor = _valor_futuro(patrimonio, perfil.aporte_mensal, taxa_m, meses)
        trajetoria.append({"idade": perfil.idade_atual + ano, "patrimonio_projetado": round(valor, 2)})

    patrimonio_na_aposentadoria = trajetoria[-1]["patrimonio_projetado"] if trajetoria else patrimonio

    renda_passiva_mensal = round(patrimonio_na_aposentadoria * taxa_m, 2)
    deficit_superavit = round(renda_passiva_mensal - perfil.renda_desejada_mensal, 2)

    if taxa_m > 0:
        patrimonio_necessario = perfil.renda_desejada_mensal / taxa_m
        falta = max(patrimonio_necessario - patrimonio, 0)
        if meses_restantes > 0:
            fator = (1 + taxa_m) ** meses_restantes
            aporte_necessario = (
                (patrimonio_necessario - patrimonio * fator) * taxa_m / (fator - 1) if fator != 1 else None
            )
        else:
            aporte_necessario = None
    else:
        patrimonio_necessario = perfil.renda_desejada_mensal * 12 * 30  # regra grosseira sem juros
        aporte_necessario = None

    return {
        "patrimonio_atual": patrimonio,
        "idade_atual": perfil.idade_atual,
        "idade_aposentadoria": perfil.idade_aposentadoria,
        "patrimonio_projetado_aposentadoria": patrimonio_na_aposentadoria,
        "renda_passiva_estimada_mensal": renda_passiva_mensal,
        "renda_desejada_mensal": perfil.renda_desejada_mensal,
        "deficit_superavit_mensal": deficit_superavit,
        "patrimonio_necessario_para_meta": round(patrimonio_necessario, 2),
        "aporte_mensal_necessario_para_meta": (
            round(aporte_necessario, 2) if aporte_necessario is not None and aporte_necessario > 0 else 0.0
        ),
        "trajetoria": trajetoria,
    }
