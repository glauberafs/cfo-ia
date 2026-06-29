"""CFO IA - orquestrador do pipeline.

Uso:
  python main.py --demo      # roda com transacoes de exemplo (sem credenciais)
  python main.py             # roda de verdade, puxando da Pluggy (precisa de .env)
"""
import json
import sys
import uuid

from cfo.models import Conta, TipoConta
from cfo.normalize import normalizar, hash_transacao
from cfo.storage import Storage


def _tipo(pluggy_type: str) -> str:
    return TipoConta.CARTAO if pluggy_type == "CREDIT" else TipoConta.CONTA


def processar(conta: Conta, transacoes: list, store: Storage):
    novos = 0
    for t in transacoes:
        h = hash_transacao(t, conta.id)
        bid = store.salvar_bruta(t, h, t.get("id", ""))
        if bid is None:
            continue  # dedup: ja existia
        ev = normalizar(t, conta, bid)
        store.salvar_evento(ev)
        novos += 1
    return novos


def rodar_demo(store: Storage):
    with open("sample_transactions.json", encoding="utf-8") as f:
        dados = json.load(f)
    por_id = {c["id"]: c for c in dados["contas"]}
    total = 0
    for acc_id, txs in dados["transacoes"].items():
        c = por_id[acc_id]
        conta = Conta(id=acc_id, pluggy_account_id=acc_id, nome=c["name"],
                      tipo=_tipo(c["type"]), instituicao=c["institution"], saldo=c["balance"])
        store.salvar_conta(conta)
        total += processar(conta, txs, store)
    return total


def rodar_real(store: Storage):
    import os
    from dotenv import load_dotenv
    from cfo.pluggy_client import PluggyClient
    load_dotenv()
    client = PluggyClient()
    item_id = os.environ["PLUGGY_ITEM_ID"]
    total = 0
    for c in client.listar_contas(item_id):
        conta = Conta(id=str(uuid.uuid4()), pluggy_account_id=c["id"], nome=c.get("name", ""),
                      tipo=_tipo(c.get("type", "BANK")), instituicao=c.get("marketingName", ""),
                      saldo=c.get("balance", 0.0))
        store.salvar_conta(conta)
        total += processar(conta, client.listar_transacoes(c["id"]), store)
    return total


def imprimir(store: Storage):
    eventos = store.listar_eventos()
    print(f"\n{'DATA':<11} {'NATUREZA':<16} {'STATUS':<9} {'CATEGORIA':<16} {'VALOR':>10}  DESCRICAO")
    print("-" * 90)
    for e in eventos:
        flag = "" if e["afeta_patrimonio"] else "  (neutro)"
        print(f"{e['data']:<11} {e['natureza']:<16} {e['status']:<9} "
              f"{e['categoria_id']:<16} {e['valor']:>10.2f}  {e['descricao']}{flag}")

    # resumo simples: gastos por categoria (so o que afeta patrimonio e e saida)
    print("\nGasto realizado por categoria:")
    por_cat = {}
    for e in eventos:
        if e["afeta_patrimonio"] and e["status"] == "REALIZADO" and e["valor"] < 0:
            por_cat[e["categoria_id"]] = por_cat.get(e["categoria_id"], 0) + e["valor"]
    for cat, v in sorted(por_cat.items(), key=lambda x: x[1]):
        print(f"  {cat:<18} {v:>10.2f}")

    previstos = [e for e in eventos if e["status"] == "PREVISTO"]
    if previstos:
        tot = sum(e["valor"] for e in previstos)
        print(f"\nObrigacoes futuras (PREVISTO): {len(previstos)} evento(s), total {tot:.2f}")


if __name__ == "__main__":
    store = Storage("cfo.db")
    if "--demo" in sys.argv:
        n = rodar_demo(store)
        print(f"Demo: {n} novo(s) evento(s) processado(s).")
    else:
        n = rodar_real(store)
        print(f"Real: {n} novo(s) evento(s) processado(s).")
    imprimir(store)
