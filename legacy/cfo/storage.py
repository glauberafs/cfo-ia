"""Armazenamento local em SQLite (zero setup, ideal para uso pessoal)."""
import json
import sqlite3
import uuid

SCHEMA = """
CREATE TABLE IF NOT EXISTS contas (
    id TEXT PRIMARY KEY, pluggy_account_id TEXT, nome TEXT, tipo TEXT,
    instituicao TEXT, saldo REAL, moeda TEXT
);
CREATE TABLE IF NOT EXISTS transacoes_brutas (
    id TEXT PRIMARY KEY, pluggy_transaction_id TEXT, hash TEXT UNIQUE,
    payload_json TEXT, importado_em TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS eventos (
    id TEXT PRIMARY KEY, transacao_bruta_id TEXT, conta_id TEXT, data TEXT,
    descricao TEXT, descricao_raw TEXT, valor REAL, natureza TEXT, status TEXT,
    categoria_id TEXT, categoria_fonte TEXT, categoria_confianca REAL,
    afeta_patrimonio INTEGER, contraparte TEXT, parcela_numero INTEGER,
    parcela_total INTEGER, tags TEXT
);
"""


class Storage:
    def __init__(self, path="cfo.db"):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def salvar_conta(self, conta):
        self.conn.execute(
            "INSERT OR REPLACE INTO contas VALUES (?,?,?,?,?,?,?)",
            (conta.id, conta.pluggy_account_id, conta.nome, conta.tipo,
             conta.instituicao, conta.saldo, conta.moeda),
        )
        self.conn.commit()

    def salvar_bruta(self, payload: dict, hash_: str, pluggy_id: str) -> str | None:
        """Retorna o id da bruta, ou None se ja existia (dedup por hash)."""
        existe = self.conn.execute(
            "SELECT id FROM transacoes_brutas WHERE hash=?", (hash_,)
        ).fetchone()
        if existe:
            return None
        bid = str(uuid.uuid4())
        self.conn.execute(
            "INSERT INTO transacoes_brutas (id, pluggy_transaction_id, hash, payload_json) VALUES (?,?,?,?)",
            (bid, pluggy_id, hash_, json.dumps(payload, ensure_ascii=False)),
        )
        self.conn.commit()
        return bid

    def salvar_evento(self, ev):
        r = ev.to_row()
        r["afeta_patrimonio"] = 1 if r["afeta_patrimonio"] else 0
        cols = ",".join(r.keys())
        ph = ",".join("?" * len(r))
        self.conn.execute(f"INSERT OR REPLACE INTO eventos ({cols}) VALUES ({ph})", tuple(r.values()))
        self.conn.commit()

    def listar_eventos(self):
        return self.conn.execute("SELECT * FROM eventos ORDER BY data").fetchall()
