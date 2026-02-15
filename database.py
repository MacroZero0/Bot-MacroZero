import sqlite3
from datetime import datetime

DB_NAME = "sistema_tatico.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pontos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            user_name TEXT,
            entrada DATETIME,
            saida DATETIME,
            status TEXT DEFAULT 'ABERTO',
            msg_id INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS folgas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            user_name TEXT,
            motivo TEXT,
            data_solicitacao DATETIME,
            status TEXT DEFAULT 'PENDENTE',
            aprovado_por TEXT
        )
    """)
    conn.commit()
    conn.close()

# --- FUNÇÕES DE PONTO ---
def buscar_ponto_aberto(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, entrada, msg_id FROM pontos WHERE user_id = ? AND status = 'ABERTO'", (str(user_id),))
    return cursor.fetchone()

def abrir_ponto_db(user_id, user_name, msg_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO pontos (user_id, user_name, entrada, msg_id) VALUES (?, ?, ?, ?)", 
                   (str(user_id), user_name, agora, msg_id))
    conn.commit()
    conn.close()
    return agora

def fechar_ponto_db(ponto_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    saida = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("UPDATE pontos SET saida = ?, status = 'FECHADO' WHERE id = ?", (saida, ponto_id))
    conn.commit()
    conn.close()
    return saida

# --- FUNÇÕES DE FOLGA ---
def verificar_folga_pendente(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM folgas WHERE user_id = ? AND status = 'PENDENTE'", (str(user_id),))
    return cursor.fetchone()

def criar_folga_db(user_id, user_name, motivo):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO folgas (user_id, user_name, motivo, data_solicitacao) VALUES (?, ?, ?, ?)", 
                   (str(user_id), user_name, motivo, agora))
    folga_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return folga_id, agora

def atualizar_status_folga(folga_id, novo_status, autor):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE folgas SET status = ?, aprovado_por = ? WHERE id = ?", (novo_status, autor, folga_id))
    conn.commit()
    conn.close()