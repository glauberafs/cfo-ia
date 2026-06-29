"""Schemas Pydantic (entrada/saida da API)."""
from typing import Optional

from pydantic import BaseModel, EmailStr


class UsuarioCriar(BaseModel):
    email: EmailStr
    senha: str
    nome: str = ""
    apelidos_proprios: list[str] = []


class UsuarioLogin(BaseModel):
    email: EmailStr
    senha: str


class UsuarioOut(BaseModel):
    id: str
    email: str
    nome: str
    apelidos_proprios: list[str]

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ConexaoPluggyCriar(BaseModel):
    item_id: str
    instituicao: str = ""


class EventoOut(BaseModel):
    id: str
    conta_id: str
    data: str
    descricao: str
    valor: float
    natureza: str
    status: str
    categoria_id: str
    categoria_fonte: str
    categoria_confianca: Optional[float]
    afeta_patrimonio: bool
    contraparte: Optional[str]
    parcela_numero: Optional[int]
    parcela_total: Optional[int]

    class Config:
        from_attributes = True


class ClassificarEvento(BaseModel):
    categoria_id: str


class ResumoDashboard(BaseModel):
    receitas: float
    gastos: float
    resultado: float
    obrigacoes_futuras: float
    gasto_por_categoria: dict[str, float]


class OrcamentoCriar(BaseModel):
    categoria_id: str
    ano: int
    mes: int = 0  # 0 = orcamento anual (fallback /12 quando nao ha orcamento do mes)
    valor: float


class OrcamentoOut(BaseModel):
    id: str
    categoria_id: str
    ano: int
    mes: int
    valor: float

    class Config:
        from_attributes = True


class ComparativoCategoria(BaseModel):
    categoria_id: str
    orcado: Optional[float]
    realizado: float
    desvio: Optional[float]
    desvio_pct: Optional[float]
    origem_orcamento: Optional[str]  # MENSAL | ANUAL_PRORRATEADO | None


class ComparativoResumo(BaseModel):
    ano: int
    mes: Optional[int]
    categorias: list[ComparativoCategoria]
    orcado_total: float
    realizado_total: float


class PontoSaldo(BaseModel):
    data: str
    saldo: float


class ForecastSaldoConta(BaseModel):
    conta_id: str
    nome: str
    saldo_atual: float
    saldo_projetado: float
    pontos: list[PontoSaldo]


class ForecastFaturaConta(BaseModel):
    conta_id: str
    nome: str
    competencia: str
    realizado: float
    previsto: float
    total: float


class PerfilAposentadoriaCriar(BaseModel):
    idade_atual: int
    idade_aposentadoria: int
    renda_desejada_mensal: float
    taxa_retorno_anual_pct: float = 4.0
    aporte_mensal: float = 0.0


class PerfilAposentadoriaOut(PerfilAposentadoriaCriar):
    class Config:
        from_attributes = True


class PontoTrajetoria(BaseModel):
    idade: int
    patrimonio_projetado: float


class ProjecaoAposentadoria(BaseModel):
    patrimonio_atual: float
    idade_atual: int
    idade_aposentadoria: int
    patrimonio_projetado_aposentadoria: float
    renda_passiva_estimada_mensal: float
    renda_desejada_mensal: float
    deficit_superavit_mensal: float
    patrimonio_necessario_para_meta: float
    aporte_mensal_necessario_para_meta: float
    trajetoria: list[PontoTrajetoria]


class AtivoCriar(BaseModel):
    nome: str
    categoria: str = "outro"
    valor_inicial: float = 0.0


class AtivoOut(BaseModel):
    id: str
    nome: str
    categoria: str
    valor_atual: float

    class Config:
        from_attributes = True


class MovimentoCriar(BaseModel):
    tipo: str  # APORTE | RETIRADA | AJUSTE_VALOR
    valor: float
    data: Optional[str] = None
    observacao: str = ""


class MovimentoOut(BaseModel):
    id: str
    ativo_id: str
    tipo: str
    valor: float
    data: str
    observacao: str

    class Config:
        from_attributes = True


class ResumoPatrimonio(BaseModel):
    contas: float
    ativos_manuais: float
    total: float


class ResumoPeriodo(BaseModel):
    receitas: float
    despesas: float
    resultado: float
    por_categoria: dict[str, float]


class DREResponse(BaseModel):
    ano: int
    mes: Optional[int]
    atual: ResumoPeriodo
    periodo_anterior: Optional[ResumoPeriodo]
    mesmo_periodo_ano_anterior: Optional[ResumoPeriodo]
    acumulado_ano_atual: ResumoPeriodo
    acumulado_ano_anterior: ResumoPeriodo


class AnomaliaOut(BaseModel):
    categoria_id: str
    valor_atual: float
    media_historica: float
    variacao_pct: float
    mensagem: str


class ComponenteScore(BaseModel):
    pontos: float
    pontos_max: float
    valor_pct: Optional[float] = None


class ScoreFinanceiro(BaseModel):
    score: int
    score_max: int
    classificacao: str
    componentes: dict[str, ComponenteScore]


class AtivoInvestimentoOut(BaseModel):
    ativo_id: str
    nome: str
    valor_atual: float
    total_aportado_liquido: float
    rentabilidade_rs: float
    rentabilidade_pct: Optional[float]


class ResumoInvestimentos(BaseModel):
    total_investido_atual: float
    total_aportado_liquido: float
    rentabilidade_rs_total: float
    rentabilidade_pct_total: Optional[float]
    ativos: list[AtivoInvestimentoOut]
    eventos_movimentacao_detectados: int


class AlertaOut(BaseModel):
    tipo: str
    mensagem: str
    categoria_id: Optional[str] = None
    conta_id: Optional[str] = None
    valor_orcado: Optional[float] = None
    valor_realizado: Optional[float] = None
    valor_projetado: Optional[float] = None
    data: Optional[str] = None
    saldo_projetado: Optional[float] = None
