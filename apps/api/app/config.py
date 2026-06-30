"""Configuracao da API. Le tudo de variaveis de ambiente (.env na raiz do monorepo)."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_parents = Path(__file__).resolve().parents
ROOT_ENV = (_parents[3] / ".env") if len(_parents) > 3 else Path("/nonexistent/.env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ROOT_ENV), env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg2://cfo:cfo@localhost:5432/cfo_ia"
    jwt_secret: str = "troque-este-segredo-em-producao"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    # Credenciais Pluggy sao por app (client_id/secret), mas o item_id e por conexao do usuario
    pluggy_client_id: str | None = None
    pluggy_client_secret: str | None = None

    # Chave da Anthropic (Claude) para classificacao automatica por IA dos pendentes.
    # Opcional: sem ela, o botao "Classificar com IA" retorna erro amigavel.
    anthropic_api_key: str | None = None


settings = Settings()
