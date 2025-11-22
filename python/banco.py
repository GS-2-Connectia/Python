# banco.py
# Módulo para conexão e operações no banco Oracle.
import os
import json
import datetime
import oracledb

# Ler variáveis de ambiente (ou use outro método de configuração)
DB_USER = os.getenv("ORACLE_USER", "rm566516")
DB_PASSWORD = os.getenv("ORACLE_PASSWORD", "210806")
DB_DSN = os.getenv("ORACLE_DSN", "oracle.fiap.com.br:1521/orcl")  # ex: "myhost:1521/XEPDB1"

# Conexão global (pool simples)
POOL = None

def init_pool(min=1, max=4, increment=1):
    global POOL
    if POOL is None:
        POOL = oracledb.create_pool(user=DB_USER,
                                    password=DB_PASSWORD,
                                    dsn=DB_DSN,
                                    min=min,
                                    max=max,
                                    increment=increment,
                                    encoding="UTF-8")
    return POOL

def get_conn():
    init_pool()
    return POOL.acquire()

# util: convert rows -> dicts
def rows_to_dicts(cursor, rows):
    cols = [col[0].lower() for col in cursor.description]
    results = []
    for r in rows:
        row = {}
        for k, v in zip(cols, r):
            if isinstance(v, datetime.date):
                row[k] = v.isoformat()
            else:
                row[k] = v
        results.append(row)
    return results

# util: write JSON file (returns path)
def export_to_json(data, filename=None):
    if filename is None:
        filename = f"export_{int(datetime.datetime.utcnow().timestamp())}.json"
    path = f"/tmp/{filename}"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path

# --- USER CRUD (T_CON_USUARIO) ---
def get_next_id(table="T_CON_USUARIO", pk="ID_USUARIO", conn=None):
    """Tenta retornar um próximo ID simples (não safe para concorrência real)."""
    close_conn = False
    if conn is None:
        conn = get_conn()
        close_conn = True
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT NVL(MAX({pk}),0)+1 FROM {table}")
        next_id = cur.fetchone()[0]
        cur.close()
        return int(next_id)
    finally:
        if close_conn:
            conn.close()

def create_user(user_data):
    """
    Espera dict: { 'nm_usuario', 'ds_email', 'ds_senha', 'id_carreira', 'tp_plano', 't_con_carreira_id_area' }
    Retorna o usuário inserido (com id).
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        # validações mínimas
        required = ['nm_usuario', 'ds_email', 'ds_senha', 'id_carreira', 'tp_plano', 't_con_carreira_id_area']
        for f in required:
            if f not in user_data:
                raise ValueError(f"Campo obrigatório ausente: {f}")

        # verifica email único
        cur.execute("SELECT COUNT(*) FROM T_CON_USUARIO WHERE DS_EMAIL = :email", [user_data['ds_email']])
        if cur.fetchone()[0] > 0:
            raise ValueError("Email já cadastrado")

        new_id = get_next_id(conn=conn)
        cur.execute(
            """
            INSERT INTO T_CON_USUARIO (
                ID_USUARIO, NM_USUARIO, DS_EMAIL, DS_SENHA, ID_CARREIRA, TP_PLANO, T_CON_CARREIRA_ID_AREA
            ) VALUES (
                :id_usuario, :nm_usuario, :ds_email, :ds_senha, :id_carreira, :tp_plano, :t_con_carreira_id_area
            )
            """,
            {
                "id_usuario": new_id,
                "nm_usuario": user_data['nm_usuario'],
                "ds_email": user_data['ds_email'],
                "ds_senha": user_data['ds_senha'],
                "id_carreira": int(user_data['id_carreira']),
                "tp_plano": user_data['tp_plano'],
                "t_con_carreira_id_area": int(user_data['t_con_carreira_id_area'])
            }
        )
        conn.commit()
        cur.close()
        user_data_out = user_data.copy()
        user_data_out['id_usuario'] = new_id
        return user_data_out
    finally:
        conn.close()

def get_user(id_usuario):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT ID_USUARIO, NM_USUARIO, DS_EMAIL, ID_CARREIRA, TP_PLANO, T_CON_CARREIRA_ID_AREA FROM T_CON_USUARIO WHERE ID_USUARIO = :id", [int(id_usuario)])
        row = cur.fetchone()
        if not row:
            return None
        cols = [col[0].lower() for col in cur.description]
        user = dict(zip(cols, row))
        cur.close()
        return user
    finally:
        conn.close()

def list_users(limit=100, offset=0):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT ID_USUARIO, NM_USUARIO, DS_EMAIL, ID_CARREIRA, TP_PLANO, T_CON_CARREIRA_ID_AREA
            FROM T_CON_USUARIO
            ORDER BY ID_USUARIO
            OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
        """, {"offset": int(offset), "limit": int(limit)})
        rows = cur.fetchall()
        users = rows_to_dicts(cur, rows)
        cur.close()
        return users
    finally:
        conn.close()

def update_user(id_usuario, data):
    conn = get_conn()
    try:
        cur = conn.cursor()
        # construção dinâmica segura (parâmetros nomeados)
        allowed = ['nm_usuario', 'ds_email', 'ds_senha', 'id_carreira', 'tp_plano', 't_con_carreira_id_area']
        set_parts = []
        params = {}
        for k in allowed:
            if k in data:
                set_parts.append(f"{k.upper()} = :{k}")
                params[k] = data[k]
        if not set_parts:
            raise ValueError("Nenhum campo atualizável fornecido")
        params['id'] = int(id_usuario)
        sql = f"UPDATE T_CON_USUARIO SET {', '.join(set_parts)} WHERE ID_USUARIO = :id"
        cur.execute(sql, params)
        if cur.rowcount == 0:
            raise LookupError("Usuário não encontrado")
        conn.commit()
        cur.close()
        return get_user(id_usuario)
    finally:
        conn.close()

def delete_user(id_usuario):
    conn = get_conn()
    try:
        cur = conn.cursor()
        # Atenção: por integridade referencial, dependências podem impedir exclusão
        cur.execute("DELETE FROM T_CON_USUARIO WHERE ID_USUARIO = :id", [int(id_usuario)])
        if cur.rowcount == 0:
            raise LookupError("Usuário não encontrado")
        conn.commit()
        cur.close()
        return True
    finally:
        conn.close()

# --- COURSE helpers (T_CON_CURSOS) ---
def list_courses(limit=100, offset=0):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT ID_CURSO, NM_CURSO, DS_CURSO, ID_CARREIRA, TP_CONTEUDO, DT_INICIO, STS_CURSO, ID_USUARIO, ID_AREA
            FROM T_CON_CURSOS
            ORDER BY ID_CURSO
            OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
        """, {"offset": int(offset), "limit": int(limit)})
        rows = cur.fetchall()
        courses = rows_to_dicts(cur, rows)
        cur.close()
        return courses
    finally:
        conn.close()

def get_course(id_curso, id_carreira=None, id_area=None):
    conn = get_conn()
    try:
        cur = conn.cursor()
        if id_carreira is None or id_area is None:
            cur.execute("SELECT * FROM T_CON_CURSOS WHERE ID_CURSO = :id", [int(id_curso)])
        else:
            cur.execute("SELECT * FROM T_CON_CURSOS WHERE ID_CURSO = :id AND ID_CARREIRA = :id_carreira AND ID_AREA = :id_area",
                        {"id": int(id_curso), "id_carreira": int(id_carreira), "id_area": int(id_area)})
        row = cur.fetchone()
        if not row:
            return None
        course = dict(zip([c[0].lower() for c in cur.description], row))
        cur.close()
        return course
    finally:
        conn.close()

def update_course_status(id_curso, new_status, id_carreira=None, id_area=None):
    if new_status not in ('C','N','E'):
        raise ValueError("Status inválido. Use 'C', 'N' ou 'E'")
    conn = get_conn()
    try:
        cur = conn.cursor()
        if id_carreira is None or id_area is None:
            cur.execute("UPDATE T_CON_CURSOS SET STS_CURSO = :sts WHERE ID_CURSO = :id", {"sts": new_status, "id": int(id_curso)})
        else:
            cur.execute("UPDATE T_CON_CURSOS SET STS_CURSO = :sts WHERE ID_CURSO = :id AND ID_CARREIRA = :id_carreira AND ID_AREA = :id_area",
                        {"sts": new_status, "id": int(id_curso), "id_carreira": int(id_carreira), "id_area": int(id_area)})
        if cur.rowcount == 0:
            raise LookupError("Curso não encontrado")
        conn.commit()
        cur.close()
        return get_course(id_curso, id_carreira, id_area)
    finally:
        conn.close()

# --- CONSULTAS REQUERIDAS (pelo menos 3) ---
def query_users_by_career(id_carreira):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT u.id_usuario, u.nm_usuario, u.ds_email, u.tp_plano, u.id_carreira
            FROM T_CON_USUARIO u
            WHERE u.id_carreira = :id
            ORDER BY u.id_usuario
        """, {"id": int(id_carreira)})
        rows = cur.fetchall()
        res = rows_to_dicts(cur, rows)
        cur.close()
        return res
    finally:
        conn.close()

def query_courses_by_status(sts):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id_curso, nm_curso, ds_curso, id_carreira, id_area, sts_curso
            FROM T_CON_CURSOS
            WHERE sts_curso = :sts
            ORDER BY id_curso
        """, {"sts": sts})
        rows = cur.fetchall()
        res = rows_to_dicts(cur, rows)
        cur.close()
        return res
    finally:
        conn.close()

def query_user_courses(id_usuario):
    """
    Consulta que lista cursos associados a um usuário (T_CON_CURSOS.ID_USUARIO = id)
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT c.id_curso, c.nm_curso, c.ds_curso, c.sts_curso, c.dt_inicio, c.id_area, c.id_carreira
            FROM T_CON_CURSOS c
            WHERE c.id_usuario = :id
            ORDER BY c.dt_inicio NULLS LAST
        """, {"id": int(id_usuario)})
        rows = cur.fetchall()
        res = rows_to_dicts(cur, rows)
        cur.close()
        return res
    finally:
        conn.close()
