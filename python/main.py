import json
import oracledb
from flask import Flask, jsonify, request

# ------------------------------------------
# Conexão Oracle
# ------------------------------------------
def conectar():
    try:
        conn = oracledb.connect(
            user="admin",
            password="admin",
            dsn="localhost/XEPDB1"
        )
        return conn
    except Exception as e:
        print("Erro ao conectar ao banco:", e)
        return None

# ------------------------------------------
# CRUD
# ------------------------------------------
def validar_email(email):
    return "@" in email and "." in email

def criar_usuario(nome, email, area):
    if not validar_email(email):
        print("Email inválido!")
        return

    try:
        conn = conectar()
        if conn is None:
            return
        
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO USUARIOS (ID, NOME, EMAIL, AREA) VALUES (USUARIOS_SEQ.NEXTVAL, :1, :2, :3)",
            (nome, email, area)
        )
        conn.commit()
        print("Usuário criado com sucesso!")
    except Exception as e:
        print("Erro ao criar usuário:", e)
    finally:
        if conn:
            conn.close()

def listar_usuarios():
    try:
        conn = conectar()
        if conn is None:
            return
        
        cur = conn.cursor()
        cur.execute("SELECT ID, NOME, EMAIL, AREA FROM USUARIOS")
        usuarios = cur.fetchall()

        for u in usuarios:
            print(f"ID: {u[0]} | Nome: {u[1]} | Email: {u[2]} | Área: {u[3]}")
        return usuarios

    except Exception as e:
        print("Erro ao listar usuários:", e)
    finally:
        if conn:
            conn.close()

def atualizar_usuario(id_usuario, nome, email, area):
    try:
        conn = conectar()
        if conn is None:
            return

        cur = conn.cursor()
        cur.execute(
            "UPDATE USUARIOS SET NOME = :1, EMAIL = :2, AREA = :3 WHERE ID = :4",
            (nome, email, area, id_usuario)
        )
        conn.commit()
        print("Usuário atualizado com sucesso!")
    except Exception as e:
        print("Erro ao atualizar usuário:", e)
    finally:
        if conn:
            conn.close()

def deletar_usuario(id_usuario):
    try:
        conn = conectar()
        if conn is None:
            return

        cur = conn.cursor()
        cur.execute("DELETE FROM USUARIOS WHERE ID = :1", (id_usuario,))
        conn.commit()
        print("Usuário deletado com sucesso!")
    except Exception as e:
        print("Erro ao deletar usuário:", e)
    finally:
        if conn:
            conn.close()

# ------------------------------------------
# 3 Consultas + Exportar JSON
# ------------------------------------------

def exportar_json(nome_arquivo, dados):
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)
    print(f"Exportado para {nome_arquivo}")

def consulta_1():
    """Listar usuários por área"""
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT AREA, COUNT(*) FROM USUARIOS GROUP BY AREA")
        dados = [{"area": r[0], "quantidade": r[1]} for r in cur.fetchall()]
        return dados
    except Exception as e:
        print("Erro:", e)
    finally:
        conn.close()

def consulta_2():
    """Listar somente emails"""
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT EMAIL FROM USUARIOS")
        dados = [{"email": r[0]} for r in cur.fetchall()]
        return dados
    except Exception as e:
        print("Erro:", e)
    finally:
        conn.close()

def consulta_3():
    """Listar usuários ordenados por nome"""
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT ID, NOME, EMAIL, AREA FROM USUARIOS ORDER BY NOME")
        dados = [
            {"id": r[0], "nome": r[1], "email": r[2], "area": r[3]}
            for r in cur.fetchall()
        ]
        return dados
    except Exception as e:
        print("Erro:", e)
    finally:
        conn.close()

# ------------------------------------------
# MENU INTERATIVO
# ------------------------------------------

def menu():
    while True:
        print("\n=== SISTEMA ADMINISTRATIVO – GLOBAL SOLUTION ===")
        print("1 – Criar usuário")
        print("2 – Listar usuários")
        print("3 – Atualizar usuário")
        print("4 – Deletar usuário")
        print("5 – Consultas e Exportação JSON")
        print("0 – Sair")

        opc = input("Escolha uma opção: ")

        if opc == "1":
            nome = input("Nome: ")
            email = input("Email: ")
            area = input("Área: ")
            criar_usuario(nome, email, area)

        elif opc == "2":
            listar_usuarios()

        elif opc == "3":
            idu = int(input("ID do usuário: "))
            nome = input("Novo nome: ")
            email = input("Novo email: ")
            area = input("Nova área: ")
            atualizar_usuario(idu, nome, email, area)

        elif opc == "4":
            idu = int(input("ID do usuário: "))
            deletar_usuario(idu)

        elif opc == "5":
            print("\n1 – Consulta 1: Usuários por área")
            print("2 – Consulta 2: Emails")
            print("3 – Consulta 3: Usuários ordenados por nome")
            escolha = input("Escolha: ")

            if escolha == "1":
                dados = consulta_1()
                exportar_json("consulta1.json", dados)

            elif escolha == "2":
                dados = consulta_2()
                exportar_json("consulta2.json", dados)

            elif escolha == "3":
                dados = consulta_3()
                exportar_json("consulta3.json", dados)

        elif opc == "0":
            print("Saindo...")
            break

        else:
            print("Opção inválida!")


# ------------------------------------------
# API FLASK (Opcional)
# ------------------------------------------

app = Flask(__name__)

@app.get("/usuarios")
def api_listar():
    dados = consulta_3()
    return jsonify(dados)

@app.post("/usuarios")
def api_criar():
    body = request.json
    criar_usuario(body["nome"], body["email"], body["area"])
    return jsonify({"msg": "Usuário criado"}), 201

if __name__ == "__main__":
    print("Escolha: ")
    print("1 – Executar menu interativo (terminal)")
    print("2 – Executar API Flask")

    c = input("Opção: ")

    if c == "1":
        menu()
    else:
        app.run(port=5000)
