# CFO IA

Plataforma de gestao financeira pessoal inteligente. Ver Documento Mestre v1.0
e Especificacao do Evento Financeiro v1.0 para principios e roadmap.

## Arquitetura

Monorepo, multiusuario, pensado para crescer sem reescrita:

```
apps/
  api/    FastAPI + SQLAlchemy + PostgreSQL (Core Financeiro como servico)
  web/    Streamlit -- UI TEMPORARIA, fala com a API via HTTP. Sera trocada
          por um frontend web de verdade.
legacy/   codigo original (SQLite local, sem multiusuario) -- so referencia.
```

A API e o lugar onde toda a logica de dominio vive agora
(`apps/api/app/core/`): normalizacao do Evento Financeiro, categorizacao,
sincronizacao e cliente Pluggy. Tudo isolado por `usuario_id`.

## Subir o ambiente

1. Banco:
   ```bash
   docker compose up -d db
   ```
2. Copie `.env.example` para `.env` na raiz e preencha `PLUGGY_CLIENT_ID`/`PLUGGY_CLIENT_SECRET`
   (credenciais do APP -- nao do item de um usuario especifico).
3. API:
   ```bash
   cd apps/api
   pip install -r requirements.txt
   alembic upgrade head
   uvicorn app.main:app --reload
   ```
4. UI temporaria:
   ```bash
   cd apps/web
   pip install -r requirements.txt
   streamlit run dashboard.py
   ```

## Fluxo

1. Crie uma conta em `/auth/register` (pelo Streamlit, aba "Criar conta").
   Informe os "apelidos proprios" -- nomes que identificam VOCE como
   contraparte de transferencias (usado para diferenciar transferencia entre
   suas proprias contas de transferencia para terceiros).
2. Rode "Sync demo" para validar o pipeline sem credenciais reais, ou conecte
   um banco real via MeuPluggy/widget Pluggy e registre o `item_id` retornado
   em `POST /contas/conexoes`.
3. Classifique o que cair em `nao_classificado`: a partir da primeira vez, a
   memoria por estabelecimento e aplicada automaticamente em todo novo sync.

## Correcoes desta etapa (problemas conhecidos do esqueleto original)

1. **Categorias em ingles eliminadas**: a dica de categoria da Pluggy nunca e
   usada como categoria final; passa por `MAPA_PLUGGY` (`apps/api/app/core/categorize.py`)
   que traduz para a taxonomia em portugues, ou cai em `nao_classificado`.
2. **Transferencia para terceiro nao e mais neutra**: `Natureza.TRANSFERENCIA`
   (neutra, entre contas proprias) foi separada de `TRANSFERENCIA_TERCEIRO`
   (afeta patrimonio), usando os `apelidos_proprios` do usuario para decidir
   (`apps/api/app/core/normalize.py:_contraparte_e_propria`).
3. **Memoria de categoria roda automaticamente**: todo sync novo (Pluggy ou
   demo) reaplica a memoria do usuario antes de salvar o evento
   (`apps/api/app/core/sync_service.py`). Antes so acontecia ao clicar num
   botao do dashboard.
4. **Multiusuario desde a base**: todas as tabelas (`contas`, `eventos`,
   `transacoes_brutas`, `memoria_categoria`) tem `usuario_id` e todo acesso
   passa por JWT (`apps/api/app/security.py`).

## Modulos de valor (roadmap do Documento Mestre)

1. **Orcamento por categoria + comparativo real x orcado** -- feito.
   `PUT /orcamentos` define um limite mensal (`mes=1..12`) ou anual (`mes=0`,
   usado como fallback /12 quando nao ha orcamento daquele mes especifico).
   `GET /orcamentos/comparativo?ano=&mes=` retorna orcado, realizado, desvio
   (R$ e %) por categoria -- sem `mes` compara o ano inteiro.
   Logica em `apps/api/app/core/orcamento_service.py`; UI no Streamlit.
2. **Forecast de caixa** -- feito (versao simples, sem estimar gasto recorrente
   por media historica ainda).
   `GET /forecast/saldo?dias=30` projeta o saldo de cada conta (tipo CONTA)
   somando os eventos PREVISTO (parcelas futuras, etc) ja conhecidos.
   `GET /forecast/fatura` soma, por cartao, o que ja foi REALIZADO no mes
   corrente + parcelas PREVISTAS que caem nele.
   Logica em `apps/api/app/core/forecast_service.py`; UI no Streamlit.
3. **Projecao de patrimonio e aposentadoria** -- feito.
   Perfil por usuario (idade atual/aposentadoria, renda passiva desejada,
   taxa de retorno REAL esperada, aporte mensal) em `PUT /aposentadoria/perfil`.
   `GET /aposentadoria/projecao` acumula juros compostos + aportes ate a
   aposentadoria, estima renda passiva sustentavel (perpetuidade: so o
   rendimento, sem consumir o principal) e calcula o aporte mensal necessario
   para bater a meta caso o ritmo atual nao chegue la.
   Logica em `apps/api/app/core/aposentadoria_service.py`; UI no Streamlit.

   **Patrimonio manual** (`apps/api/app/core/patrimonio_service.py`):
   a Pluggy pessoal so traz movimentacao de conta/cartao, nao posicao de
   carteira -- entao o usuario cadastra ativos a mao (`POST /patrimonio/ativos`:
   investimento/imovel/outro) e registra **aporte**, **retirada** ou
   **ajuste direto de valor** a qualquer momento (`POST /patrimonio/ativos/{id}/movimentos`),
   com historico completo. `GET /patrimonio/resumo` soma contas + ativos
   manuais; esse total e o que entra em `patrimonio_atual` da projecao de
   aposentadoria (item 3).
4. **Analise de investimentos** -- feito, apoiada no patrimonio manual
   (a Pluggy pessoal so traz movimentacao -- eventos APLICACAO/RESGATE -- nao
   posicao de carteira). `GET /investimentos/resumo` calcula rentabilidade
   (R$ e %) de cada ativo de categoria "investimento": valor atual menos o
   total aportado/retirado liquido (historico de movimentos). Tambem reporta
   quantos eventos APLICACAO/RESGATE foram detectados nas contas sincronizadas,
   como sinal de que ha investimento acontecendo fora do que foi cadastrado a
   mao. Logica em `apps/api/app/core/investimentos_service.py`.
5. **Deteccao de anomalias** -- feito. `GET /anomalias?ano=&mes=` compara o
   gasto por categoria do mes com a media dos 3 meses anteriores; so alerta
   se houver historico e a categoria for grande o suficiente (piso de R$50,
   evita ruido). Logica em `apps/api/app/core/anomalias_service.py`.
6. **Score financeiro** -- feito. `GET /score` retorna indicador composto
   0-1000, explicavel por componente: taxa de poupanca do mes (400 pts),
   aderencia ao orcamento (300 pts), saldo projetado sem ficar negativo em
   30 dias (200 pts), patrimonio liquido positivo (100 pts).
   Logica em `apps/api/app/core/score_service.py`.
7. Copiloto financeiro conversacional (IA explicavel) -- pendente.

## Pendente conhecido (fora do roadmap de modulos)

- `nao_classificado` grande: camada de LLM para o residuo das regras.
- Deteccao de natureza ainda e heuristica por descricao (padroes Santander);
  generalizar por banco quando entrarem outras instituicoes.
- Frontend web real no lugar do Streamlit.
- LGPD/seguranca antes do primeiro cliente real (Pluggy comercial ~R$2.500/mes
  alem do tier gratuito pessoal).
