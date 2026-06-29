"""Cliente minimo da API Pluggy (REST).

As credenciais vem de variaveis de ambiente (PLUGGY_CLIENT_ID / PLUGGY_CLIENT_SECRET).
NUNCA coloque as credenciais no codigo. Use um arquivo .env local (ver .env.example).
"""
import os
import requests

BASE = "https://api.pluggy.ai"


class PluggyClient:
    def __init__(self, client_id=None, client_secret=None):
        self.client_id = client_id or os.environ.get("PLUGGY_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("PLUGGY_CLIENT_SECRET")
        if not self.client_id or not self.client_secret:
            raise RuntimeError(
                "Defina PLUGGY_CLIENT_ID e PLUGGY_CLIENT_SECRET (use um .env local)."
            )
        self._api_key = None

    def _auth(self):
        if self._api_key:
            return self._api_key
        r = requests.post(f"{BASE}/auth", json={
            "clientId": self.client_id, "clientSecret": self.client_secret,
        })
        r.raise_for_status()
        self._api_key = r.json()["apiKey"]
        return self._api_key

    def _headers(self):
        return {"X-API-KEY": self._auth()}

    def listar_contas(self, item_id: str):
        r = requests.get(f"{BASE}/accounts", params={"itemId": item_id}, headers=self._headers())
        r.raise_for_status()
        return r.json().get("results", [])

    def listar_transacoes(self, account_id: str):
        """Pagina pelo endpoint /v2/transactions usando o cursor 'next'."""
        todas = []
        url = f"{BASE}/v2/transactions"
        params = {"accountId": account_id}
        while True:
            r = requests.get(url, params=params, headers=self._headers())
            r.raise_for_status()
            data = r.json()
            todas.extend(data.get("results", []))
            proximo = data.get("next")
            if not proximo:
                break
            url = f"{BASE}/v2/transactions{proximo}"
            params = None
        return todas