# Librerías principales
from dotenv import load_dotenv  # Variables de entorno
import os
import requests
from typing import Literal, List
from fastapi import FastAPI, Body, Request, Response

# LangChain y Langraph
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import BaseMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langgraph.graph import StateGraph, START, END

# Tipado y modelos
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

# Cargar variables de entorno
load_dotenv()

# Crear la API
app = FastAPI()

# Configurar la entrada de preguntas
class DataQuestion(BaseModel):
    question: str

# Configuración de Embeddings
model_name = "sentence-transformers/all-mpnet-base-v2"
hf_embeddings = HuggingFaceEmbeddings(
    model_name=model_name, 
    model_kwargs={"device": "cpu"}, 
    encode_kwargs={"normalize_embeddings": False}
)

# Configuración del VectorStore FAISS
vectorstore = FAISS.load_local(
    './agro_dbv', 
    hf_embeddings, 
    allow_dangerous_deserialization=True
)

retriever = vectorstore.as_retriever(
    search_type='similarity',
    search_kwargs={'k': 5}  # Número de resultados similares
)

# Configuración del modelo LLM
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY")
)

# HISTORIAL EN MEMORIA
class InMemoryHistory(BaseChatMessageHistory, BaseModel):
    """Historial de mensajes en memoria."""
    messages: List[BaseMessage] = Field(default_factory=list)

    def add_messages(self, messages: List[BaseMessage]) -> None:
        self.messages.extend(messages)

    def clear(self) -> None:
        self.messages = []

store = {}

def get_by_session_id(session_id: str) -> BaseChatMessageHistory:
    """Obtiene el historial de una sesión específica."""
    if session_id not in store:
        store[session_id] = InMemoryHistory()
    return store[session_id]

# [PROMPTS]
# Prompt para responder preguntas
prompt_preguntas = ChatPromptTemplate.from_messages([
    ("system", '''
Actúa como un experto en cultivo hidropónico y sigue estrictamente las siguientes pautas al responder:

1. **Explicación Completa**: 
   - Proporciona respuestas breves y cortas que aborden todos los aspectos relevantes de la pregunta.
   - Relaciona tus explicaciones con los conceptos fundamentales del cultivo hidropónico.

2. **Contexto Específico**: 
   - Responde exclusivamente en función del **Contexto** proporcionado.
   - Si la pregunta no está relacionada con el contexto, indica que no puedes responder.
   - En caso de consultas relacionadas con los libros, si no se encuentra la respuesta en ellos, busca información en internet para complementar.

3. **Cordialidad y Profesionalismo**: 
   - Mantén un tono cordial, profesional y enfocado en la claridad.

Responde exclusivamente basado en el **Contexto** proporcionado.
**Contexto**:
{context}
'''),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}")
])

# Prompt para generar informe del cultivo
prompt_informe = ChatPromptTemplate.from_messages([
    ("system", '''
    Actúa como un experto en cultivo hidropónico y sigue estrictamente estas pautas al responder:

    1. **Explicación Completa**: 
       - Proporciona un informe breve del sistema, incluyendo los valores actuales de los parámetros monitoreados: temperatura, humedad, concentración de nutrientes y pH.
       - Explica cómo cada parámetro impacta en la salud y el desarrollo del cultivo. Tambien se va a dar informacion del tiempo del area, haz recomendaciones tomando en cuenta eso
       tambien 
    
    2. **Campos Monitorizados**:
     - Detalla los parámetros que se monitorean y cuales son los valores óptimos recomendados para cada uno.
        **Sistema Hidroponico***:
        'Temperatura'
        'pH'
        'Concentración de Nutrientes'
        'Humedad'
    - Considera los datos meteorologicos a parte 
        **Tiempo de la zona**:
        'temp'  
        'feels_like' 
        'temp_min'  
        'temp_max'  
        'pressure'  
        'humidity' 
        'sea_level'  
        'grnd_level' 

    3. **Recomendaciones**: 
       - Evalúa la situación del cultivo en base a los valores proporcionados.
       - Ofrece recomendaciones prácticas y específicas para mejorar las condiciones, si es necesario.
       - Indica acciones preventivas o correctivas en caso de desviaciones significativas de los valores óptimos.

    4. **Estilo y Contexto**:
       - Responde de manera profesional y únicamente en base al **Contexto** proporcionado.
       - Evita especulaciones fuera de los datos proporcionados.

    **Contexto**:
    {context}
    '''),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}")
])

# Prompt para clasificar preguntas
prompt_clasificador = ChatPromptTemplate.from_messages([
    ("system", '''
    Clasifica la pregunta recibida siguiendo estas reglas estrictas:

    1. **Concepto**:
    - Si la pregunta trata sobre definiciones, principios, fundamentos o cualquier otro concepto teórico relacionado con la hidroponía, responde únicamente con la palabra 'concepto'.

    2. **Sistema**:
    - Si la pregunta está relacionada con el sistema hidropónico, su estado actual, parámetros de funcionamiento o recomendaciones para su mejora, responde únicamente con la palabra 'sistema'.

    **Importante**:
    - Responde estrictamente con una de las dos palabras: 'concepto' o 'sistema'.
    - No proporciones explicaciones adicionales ni uses otras palabras.

    **Ejemplos**:
    -question: 'que es la hidroponia', respuesta: 'concepto'.
    -question: 'como esta el sistema', respuesta: 'sistema'.
    
    '''),
    ("human", "{question}")
])

# CHAIN DE PREGUNTAS Y RESPUESTAS
chain_preguntas_with_history = RunnableWithMessageHistory(
    prompt_preguntas | llm,
    get_by_session_id,
    input_messages_key="question",
    history_messages_key="history"
)

chain_informe_with_history = RunnableWithMessageHistory(
    prompt_informe | llm,
    get_by_session_id,
    input_messages_key="question",
    history_messages_key="history"
)

chain_clasificador = prompt_clasificador | llm

# FUNCIONES
def clasificar_pregunta(question: str) -> str:
    """Clasifica la pregunta en 'concepto' o 'sistema'."""
    response = chain_clasificador.invoke({"question": question}).dict()["content"].lower()
    return response

def get_data():
    try:
        """Obtiene datos del sistema hidropónico desde ThingSpeak."""
        url_hidro = 'https://thingspeak.mathworks.com/channels/2735925/feeds.json?results=1'
        # Mapeo de llaves originales a las nuevas
        keys_mapping = {
            'field1': 'Temperatura',
            'field2': 'pH',
            'field3': 'Concentración de Nutrientes',
            'field4': 'Humedad'
        }
        response_hidro = requests.get(url_hidro)
        if response_hidro.status_code == 200:
            # Extraer datos del feed
            main_data = response_hidro.json()['feeds'][0]
            # Crear un nuevo diccionario con las llaves renombradas
            data_hidro = {keys_mapping.get(k, k): v for k, v in main_data.items()}
        
        """Obtiene el clima de la api de OpenWeatherMap."""
        api_weather=os.getenv("OPENWETHERMAP_API_KEY")
        url_weather = f"https://api.openweathermap.org/data/2.5/weather?lat=-27.36&lon=-55.89&appid={api_weather}"
        response_weather = requests.get(url_weather)
        if response_weather.status_code == 200:  # Verifica que la respuesta sea exitosa
            data = response_weather.json()  # Convierte la respuesta a formato JSON
            main_data = data.get('main', {})  # Obtiene la sección "main"
            # Convertir temperaturas a Celsius
            data_weather = {}
            for key, value in main_data.items():
                if "temp" in key or "feels_like" == key:  # Verifica si la clave es relacionada a temperaturas
                    data_weather[key] = round(value - 273.15, 2)
                else:
                    data_weather[key] = value  # Deja los otros datos sin cambios
        return [data_hidro, data_weather]
    except Exception as e:
        return None

def responder_preguntas(state: dict) -> dict:
    """Responde preguntas teóricas sobre hidroponía."""
    question = state['messages'][0]
    context = retriever.invoke(question)
    return {"messages": chain_preguntas_with_history.invoke({"context": context, "question": question}, config={'configurable': {'session_id': 's001'}})}

def informar_cultivo(state: dict) -> dict:
    """Genera un informe del sistema hidropónico."""
    question = state['messages'][0]
    data = get_data()
    return {"messages": chain_informe_with_history.invoke({"context": data, "question": question},config={'configurable': {'session_id': 's001'}})}

def decide_mood(state) -> Literal["responder_preguntas", "informar_cultivo"]:
    """Determina la función a ejecutar según el tipo de pregunta."""
    question = state["messages"]
    return "informar_cultivo" if clasificar_pregunta(question) == "sistema" else "responder_preguntas"

# STATEGRAPH
class State(TypedDict):
    messages: str

builder = StateGraph(State)
builder.add_node("assistant", lambda state: {"messages": [state["messages"]]})
builder.add_node("responder_preguntas", responder_preguntas)
builder.add_node("informar_cultivo", informar_cultivo)
builder.add_edge(START, "assistant")
builder.add_conditional_edges("assistant", decide_mood)
builder.add_edge("responder_preguntas", END)
builder.add_edge("informar_cultivo", END)
graph = builder.compile()

# FUNCIÓN PRINCIPAL
def generar_respuesta(user_question: str) -> str:
    """Genera la respuesta final utilizando el flujo."""
    return graph.invoke({"messages": user_question})['messages'].dict()['content']

@app.get("/")
async def root():
    return {"message": "Mi servicio API"}

@app.post("/answer/")
async def answer(data: DataQuestion = Body(...)):
    #response = llm.invoke(data.questiongenerar_respuesta).content
    print(f"Ingresa pregunta API: {data.question}")
    response = generar_respuesta(data.question)
    return {"question": data.question, "answer": response}