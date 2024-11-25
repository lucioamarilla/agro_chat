# 🌱 Asistente para Gestión de Sistemas de Cultivo

Este proyecto implementa un **asistente conversacional** diseñado para proporcionar soporte técnico y operativo en sistemas de cultivo. Utiliza inteligencia artificial y técnicas de búsqueda en bases de datos vectoriales para responder preguntas y generar informes basados en datos en tiempo real.

---

## 🛠️ Componentes del Proyecto

### 1. **`app.py`**
Este archivo contiene la **API** desarrollada con **FastAPI**, que actúa como intermediaria entre el usuario y los modelos de lenguaje y bases de datos.

### 2. **`main.py`**
Contiene la lógica principal del asistente, incluyendo:
   - Clasificación de preguntas.
   - Integración con la base de datos vectorial.
   - Comunicación con ThingSpeak para obtener datos en tiempo real.

### 3. **`agro_dbv`**
Este archivo almacena la base de datos vectorial que contiene los embeddings de la información sobre sistemas de cultivo.

---

## 🚀 Funcionalidades

1. **Consultas teóricas sobre sistemas de cultivo.**
   - Respuestas generadas utilizando un modelo RAG (Generación Aumentada por Recuperación).

2. **Generación de informes operativos.**
   - Obtiene datos en tiempo real desde ThingSpeak y los procesa.

3. **Clasificación automática de preguntas.**
   - Determina si una consulta es teórica o relacionada con datos operativos.

4. **Interfaz API robusta.**
   - Facilita la interacción con aplicaciones externas o interfaces gráficas.

---

## 📋 Requisitos del Sistema

- **Python 3.8 o superior.**
- Claves API necesarias:
  - **ThingSpeak API Key** para obtener datos del sistema de cultivo.
  - Opcional: Otras claves API si integras servicios adicionales como información meteorológica.

---

## 🛠️ Instalación y Configuración

### 1. **Clonar el Repositorio**

```bash
git clone https://github.com/lucioamarilla/agro_chat.git
cd agro_chat 
```

### 2. **Crear un Entorno Virtual**

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. **Instalar Dependencias**

```bash
pip install -r requirements.txt
```

### 4.Configurar Variables de Entorno

Crea un archivo .env en el directorio raíz con la siguiente información:

THINGSPEAK_API_KEY=tu_api_key_thingspeak
OPENWETHERMAP_API_KEY=tu_api_key_openweathermap

### 5.Ejecutar la API

Inicia el servidor FastAPI desde main.py:

```bash
uvicorn main:app --reload
```

### 5.Ejecutar la API

Inicia la interfaz grafica de Streamlit desde app.py:

```bash
streamlit run app.py
```