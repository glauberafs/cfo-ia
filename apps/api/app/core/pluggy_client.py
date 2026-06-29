"""Cliente minimo da API Pluggy (REST).

Client_id/secret sao credenciais do APP (uma so para toda a plataforma);
o item_id identifica a conexao de CADA usuario com seu banco.
"""
import requests

BASE = "https://api.pluggy.ai"


class PluggyClient:
    def __init__(self, client_id: str, client_secret: str):
        if not client_id or not client_secret:
            raise RuntimeError("PLUGGY_CLIENT_ID/SECRET nao configurados no .env da API.")
        self.client_id = client_id
        self.client_secret = client_secret
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
