# app.py
import streamlit as st
from banco import (
    create_user, list_users, delete_user,
    list_courses, query_courses_by_status,
    query_user_courses, export_json
)

st.set_page_config(page_title="Sistema Oracle - Menu Interativo", layout="centered")

st.title("📘 Sistema de Gerenciamento - Oracle + Streamlit")


# ----------------------------------------
# Função de menu
# ----------------------------------------
menu = st.sidebar.selectbox(
    "Menu Principal",
    [
        "🏠 Início",
        "👤 Usuários",
        "📚 Cursos",
        "🔍 Consultas",
        "📤 Exportar JSON"
    ]
)


# ----------------------------------------
# 1) INÍCIO
# ----------------------------------------
if menu == "🏠 Início":
    st.write("### Bem-vindo ao sistema!")
    st.write("Navegue pelas opções no menu lateral.")


# ----------------------------------------
# 2) CRUD Usuários
# ----------------------------------------
elif menu == "👤 Usuários":
    st.header("👤 Gerenciamento de Usuários")

    operacao = st.selectbox("Escolha a operação:", ["Cadastrar", "Listar", "Excluir"])

    if operacao == "Cadastrar":
        st.subheader("Cadastrar novo usuário")

        nome = st.text_input("Nome")
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")
        carreira = st.number_input("ID Carreira", min_value=1)
        plano = st.selectbox("Tipo Plano", ["Básico", "Premium"])

        if st.button("Salvar"):
            try:
                new_id = create_user({
                    "nm_usuario": nome,
                    "ds_email": email,
                    "ds_senha": senha,
                    "id_carreira": carreira,
                    "tp_plano": plano
                })
                st.success(f"Usuário criado com ID {new_id}")
            except Exception as e:
                st.error(str(e))

    elif operacao == "Listar":
        st.subheader("Lista de usuários")
        try:
            data = list_users()
            st.table(data)
        except Exception as e:
            st.error(str(e))

    elif operacao == "Excluir":
        st.subheader("Excluir usuário")
        uid = st.number_input("ID do usuário", min_value=1)
        if st.button("Excluir"):
            try:
                ok = delete_user(uid)
                if ok:
                    st.success("Usuário removido!")
                else:
                    st.error("Usuário não encontrado.")
            except Exception as e:
                st.error(str(e))


# ----------------------------------------
# 3) Cursos
# ----------------------------------------
elif menu == "📚 Cursos":
    st.header("📚 Cursos cadastrados")

    try:
        data = list_courses()
        st.table(data)
    except Exception as e:
        st.error(str(e))


# ----------------------------------------
# 4) Consultas
# ----------------------------------------
elif menu == "🔍 Consultas":
    st.header("🔍 Consultas ao Banco")

    consulta = st.selectbox("Selecione a consulta:",
                            ["Cursos por Status", "Cursos por Usuário"])

    if consulta == "Cursos por Status":
        status = st.selectbox("Status", ["N", "C", "E"])
        if st.button("Consultar"):
            try:
                data = query_courses_by_status(status)
                st.table(data)
                st.session_state["last_query"] = data
            except Exception as e:
                st.error(str(e))

    if consulta == "Cursos por Usuário":
        uid = st.number_input("ID do usuário", min_value=1)
        if st.button("Consultar"):
            try:
                data = query_user_courses(uid)
                st.table(data)
                st.session_state["last_query"] = data
            except Exception as e:
                st.error(str(e))


# ----------------------------------------
# 5) Exportar JSON
# ----------------------------------------
elif menu == "📤 Exportar JSON":
    st.header("📤 Exportação de Consultas em JSON")

    if "last_query" not in st.session_state or not st.session_state["last_query"]:
        st.warning("Nenhuma consulta foi realizada ainda!")
    else:
        filename = st.text_input("Nome do arquivo (ex.: consulta.json)")
        if st.button("Exportar"):
            try:
                path = export_json(st.session_state["last_query"], filename)
                st.success(f"Arquivo exportado com sucesso: {path}")
            except Exception as e:
                st.error(str(e))
