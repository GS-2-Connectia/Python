# banco.py
import os
import json
import datetime
import oracledb

DB_USER = os.getenv("ORACLE_USER", "rm566516")
DB_PASSWORD = os.getenv("ORACLE_PASSWORD", "210806")
DB_DSN = os.getenv("ORACLE_DSN", "oracle.fiap.com.br:1521/orcl")


def get_conexao():
    return oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)


def rows_to_dicts(cursor, rows):
    cols = [c[0].lower() for c in cursor.description]
    result = []
    for r in rows:
        row = {}
        for k, v in zip(cols, r):
            if isinstance(v, datetime.date):
                row[k] = v.isoformat()
            else:
                row[k] = v
        result.append(row)
    return result


# ==========================
# USUÁRIOS (T_CON_USUARIO)
# ==========================

def get_next_user_id():
    with get_conexao() as con:
        with con.cursor() as cur:
            cur.execute("SELECT NVL(MAX(ID_USUARIO),0)+1 FROM T_CON_USUARIO")
            return cur.fetchone()[0]


def create_user(data):
    required = ["nm_usuario", "ds_email", "ds_senha", "id_carreira", "tp_plano"]
    for campo in required:
        if campo not in data or not data[campo]:
            raise ValueError(f"Campo obrigatório ausente: {campo}")

    with get_conexao() as con:
        with con.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM T_CON_USUARIO WHERE DS_EMAIL = :email",
                        {"email": data["ds_email"]})
            if cur.fetchone()[0] > 0:
                raise ValueError("E-mail já cadastrado")

            new_id = get_next_user_id()

            cur.execute("""
                INSERT INTO T_CON_USUARIO
                (ID_USUARIO, NM_USUARIO, DS_EMAIL, DS_SENHA, ID_CARREIRA, TP_PLANO)
                VALUES (:id, :nm, :email, :senha, :carreira, :plano)
            """, {
                "id": new_id,
                "nm": data["nm_usuario"],
                "email": data["ds_email"],
                "senha": data["ds_senha"],
                "carreira": int(data["id_carreira"]),
                "plano": data["tp_plano"]
            })

        con.commit()
        return new_id


def list_users():
    with get_conexao() as con:
        with con.cursor() as cur:
            cur.execute("""
                SELECT ID_USUARIO, NM_USUARIO, DS_EMAIL, ID_CARREIRA, TP_PLANO
                FROM T_CON_USUARIO
                ORDER BY ID_USUARIO
            """)
            rows = cur.fetchall()
            return rows_to_dicts(cur, rows)


def delete_user(id_usuario):
    with get_conexao() as con:
        with con.cursor() as cur:
            cur.execute("DELETE FROM T_CON_USUARIO WHERE ID_USUARIO = :id",
                        {"id": int(id_usuario)})
        con.commit()
        return cur.rowcount > 0


# ==========================
# CURSOS (T_CON_CURSOS)
# ==========================

def list_courses():
    with get_conexao() as con:
        with con.cursor() as cur:
            cur.execute("""
                SELECT NM_CURSO, ID_CURSO, DS_CURSO, TP_CONTEUDO,
                       DT_INICIO, STS_CURSO, ID_USUARIO, ID_AREA
                FROM T_CON_CURSOS
            """)
            rows = cur.fetchall()
            return rows_to_dicts(cur, rows)


def query_courses_by_status(status):
    with get_conexao() as con:
        with con.cursor() as cur:
            cur.execute("""
                SELECT ID_CURSO, NM_CURSO, DS_CURSO, STS_CURSO, ID_AREA
                FROM T_CON_CURSOS
                WHERE STS_CURSO = :st
            """, {"st": status})
            rows = cur.fetchall()
            return rows_to_dicts(cur, rows)


def query_user_courses(id_usuario):
    with get_conexao() as con:
        with con.cursor() as cur:
            cur.execute("""
                SELECT ID_CURSO, NM_CURSO, DS_CURSO, DT_INICIO, STS_CURSO, ID_AREA
                FROM T_CON_CURSOS
                WHERE ID_USUARIO = :u
                ORDER BY DT_INICIO DESC NULLS LAST
            """, {"u": int(id_usuario)})
            rows = cur.fetchall()
            return rows_to_dicts(cur, rows)


# ==========================
# Exportação JSON
# ==========================

def export_json(data, filename):
    fullpath = f"./{filename}"
    with open(fullpath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return fullpath
