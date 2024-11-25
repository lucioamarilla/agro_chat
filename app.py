import streamlit as st
import requests

# URL de la API en FastAPI
url = "http://127.0.0.1:8000/answer/"  # Cambia esta URL si tu API está alojada en otro lugar

# Configuración de la interfaz
st.set_page_config(page_title="Asistente para Sistemas Hidropónicos", page_icon="🌱")
st.title("🌱 Asistente Hidropónico")

# Inicializa el historial de mensajes si no existe
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar el historial de mensajes en la interfaz
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrada de preguntas desde la interfaz
if query := st.chat_input("Escribe tu pregunta sobre tu sistema hidropónico:"):
    # Añadir la pregunta del usuario al historial
    st.session_state.messages.append({"role": "user", "content": query})
    
    with st.chat_message("user"):
        st.markdown(query)

    # Procesar la pregunta enviándola a la API
    with st.chat_message("assistant"):
        with st.spinner("Analizando tu pregunta..."):
            message_placeholder = st.empty()
            full_response = ""

            try:
                # Llamada a la API FastAPI
                response = requests.post(url, json={"question": query})
                response.raise_for_status()  # Lanza una excepción si hay un error HTTP

                # Obtiene la respuesta de la API
                api_response = response.json()
                full_response = api_response.get("answer", "No se recibió respuesta de la API.")
            except requests.exceptions.RequestException as e:
                full_response = f"Error al conectar con la API: {e}"

            # Mostrar la respuesta en tiempo real con el cursor de escritura
            message_placeholder.markdown(full_response + "▌")

            # Finalmente muestra la respuesta completa
            message_placeholder.markdown(full_response)

    # Añadir la respuesta al historial
    st.session_state.messages.append({"role": "assistant", "content": full_response})


