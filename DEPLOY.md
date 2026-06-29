# Deploy gratuito (Neon + Render + Streamlit Cloud)

Pensado para "usuario 1 ou poucos usuarios" -- sem custo, sem cartao de
credito. Os passos marcados **[VOCE]** sao acoes que so voce pode fazer
(criar conta, clicar em botoes de sites externos). O resto eu preparo.

## 0. Repositorio no GitHub

1. **[VOCE]** Crie um repositorio vazio no GitHub (pode ser privado) -- ex:
   `cfo-ia`. Nao inicialize com README (ja temos um).
2. Me envie a URL do repositorio (ex: `https://github.com/seu-usuario/cfo-ia.git`)
   que eu conecto e empurro o codigo local.

## 1. Banco de dados -- Neon (Postgres gratuito)

1. **[VOCE]** Crie conta em https://neon.tech (pode entrar com GitHub).
2. **[VOCE]** Crie um projeto novo (ex: "cfo-ia"). A regiao nao importa muito,
   prefira algo perto do Brasil se houver (ex: US East).
3. **[VOCE]** Na tela do projeto, copie a "Connection string" (formato
   `postgresql://usuario:senha@host/dbname?sslmode=require`).
4. Me envie essa connection string (ou cole direto no campo de variavel de
   ambiente do Render no passo 2 -- o que for mais confortavel pra voce).
   Troque o prefixo `postgresql://` por `postgresql+psycopg2://` antes de
   usar (driver que a API espera).

## 2. API -- Render (web service gratuito)

1. **[VOCE]** Crie conta em https://render.com (pode entrar com GitHub).
2. **[VOCE]** "New" -> "Web Service" -> conecte o repositorio `cfo-ia` do
   GitHub.
3. Configuracao do servico:
   - **Root Directory**: `apps/api`
   - **Runtime**: Docker (o Render deve detectar o `Dockerfile` automaticamente)
   - **Plan**: Free
4. **[VOCE]** Em "Environment", adicione as variaveis:
   - `DATABASE_URL` = a connection string do Neon (com `+psycopg2`)
   - `JWT_SECRET` = qualquer string longa e aleatoria (ou deixe o Render gerar)
   - `ACCESS_TOKEN_EXPIRE_MINUTES` = `1440`
   - `PLUGGY_CLIENT_ID` e `PLUGGY_CLIENT_SECRET` = as mesmas do seu `.env` local
5. **[VOCE]** Clique em "Create Web Service". A primeira build roda
   `alembic upgrade head` automaticamente (ver `Dockerfile`) antes de subir
   a API -- nao precisa rodar migracao manual.
6. Quando terminar, anote a URL publica (ex: `https://cfo-ia-api.onrender.com`).

> Plano free do Render "dorme" depois de ~15 min sem uso e demora ~30s para
> acordar no proximo acesso. Para 1 usuario isso e aceitavel; se incomodar,
> e so trocar de plano depois sem mudar nada do codigo.

## 3. Dashboard -- Streamlit Community Cloud

1. **[VOCE]** Crie conta em https://share.streamlit.io (entrar com GitHub).
2. **[VOCE]** "New app" -> selecione o repositorio `cfo-ia`, branch `master`,
   arquivo principal `apps/web/dashboard.py`.
3. **[VOCE]** Em "Advanced settings" -> "Secrets", cole:
   ```toml
   API_URL = "https://cfo-ia-api.onrender.com"
   ```
   (troque pela URL real do Render do passo 2.6)
4. **[VOCE]** Clique em "Deploy". Em ~1-2 min o app fica disponivel numa URL
   fixa do tipo `https://seu-usuario-cfo-ia.streamlit.app` -- essa e a URL
   que voce acessa de qualquer lugar, sem depender da sua maquina.

## Depois do deploy

- Crie sua conta de novo nesse ambiente (`/auth/register` pelo proprio
  dashboard) -- e um banco novo (Neon), nao tem os dados que estavam no
  Postgres local.
- Reconecte o Pluggy (`POST /contas/conexoes` com o `item_id` que ja
  funciona) e rode "Sincronizar (Pluggy real)".
- A partir daqui, acessa de qualquer lugar pela URL do Streamlit Cloud --
  nao depende mais do Docker Desktop nem da sua maquina estar ligada.
