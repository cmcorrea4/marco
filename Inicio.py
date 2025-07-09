import streamlit as st
import requests
import json
from openai import OpenAI
import pandas as pd
from datetime import datetime
import urllib3

# Suprimir advertencias SSL (solo para desarrollo)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuración de la página
st.set_page_config(
    page_title="Consulta de Estaciones - CORNARE",
    page_icon="🌡️",
    layout="wide"
)

# Título principal
st.title("🌡️ Consulta de Estaciones Meteorológicas CORNARE")
st.markdown("Consulta datos de estaciones y haz preguntas usando IA")

# Instrucciones importantes
with st.expander("📋 Instrucciones de uso", expanded=False):
    st.markdown("""
    **🚀 Pasos para usar la aplicación:**
    
    1. **Configura tu API Key de OpenAI** en la barra lateral
    2. **Deja desmarcado "Verificar certificado SSL"** (recomendado)
    3. **Ingresa el ID de estación** (por defecto: 204)
    4. **Haz clic en "Obtener Datos de Estación"**
    5. **Haz preguntas** sobre los datos usando IA
    
    **⚠️ Si ves errores SSL:**
    - Asegúrate de que "Verificar certificado SSL" esté **desmarcado**
    - La API funciona correctamente desde navegador
    - Python requiere esta configuración especial para CORNARE
    """)

# Sidebar para configuración
st.sidebar.header("⚙️ Configuración")

# Campo para API Key de OpenAI
openai_api_key = st.sidebar.text_input(
    "🔑 API Key de OpenAI:",
    type="password",
    placeholder="sk-..."
)

# Campo para ID de estación
estacion_id = st.sidebar.text_input(
    "🏢 ID de Estación:",
    value="204",
    placeholder="Ej: 204"
)

# Opción para verificación SSL
verificar_ssl = st.sidebar.checkbox(
    "🔒 Verificar certificado SSL",
    value=False,
    help="Desmarca si tienes problemas de conexión SSL"
)

if not verificar_ssl:
    st.sidebar.success("✅ SSL deshabilitado - Debería funcionar correctamente")
else:
    st.sidebar.info("🔒 SSL habilitado - Si hay errores, desmarca la opción")

# URL base de la API
API_BASE_URL = st.sidebar.selectbox(
    "🌐 Protocolo de conexión:",
    ["https://marco.cornare.gov.co/api/v1/estaciones", 
     "http://marco.cornare.gov.co/api/v1/estaciones"],
    help="Si HTTPS falla, prueba con HTTP"
)

def obtener_datos_estacion(id_estacion, verificar_ssl=False):
    """Obtiene los datos de una estación específica"""
    try:
        url = f"{API_BASE_URL}/{id_estacion}"
        
        # Headers para mejorar compatibilidad (similares al navegador)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }
        
        # Realizar request con configuración específica
        response = requests.get(
            url, 
            headers=headers,
            timeout=20,
            verify=verificar_ssl,  # Usar el valor del checkbox
            allow_redirects=True
        )
        
        if response.status_code == 200:
            try:
                return response.json(), None
            except json.JSONDecodeError as e:
                return None, f"Error al decodificar JSON: {str(e)}"
        else:
            return None, f"Error HTTP {response.status_code}: {response.text[:200]}"
            
    except requests.exceptions.SSLError as e:
        return None, f"Error SSL: {str(e)}. ✅ SOLUCIÓN: Desmarca 'Verificar certificado SSL' en la barra lateral."
    except requests.exceptions.ConnectionError as e:
        return None, f"Error de conexión: {str(e)}. Verifica tu conexión a internet."
    except requests.exceptions.Timeout as e:
        return None, f"Timeout: La API tardó demasiado en responder. {str(e)}"
    except requests.exceptions.RequestException as e:
        return None, f"Error de request: {str(e)}"
    except Exception as e:
        return None, f"Error inesperado: {str(e)}"

def formatear_datos_para_ai(datos_json):
    """Formatea los datos JSON para enviar a OpenAI"""
    # Información básica
    info_basica = f"""
INFORMACIÓN GENERAL DE LA ESTACIÓN:
- ID: {datos_json.get('id', 'N/A')}
- Código: {datos_json.get('codigo', 'N/A')}
- Municipio ID: {datos_json.get('municipio', 'N/A')}
- Región: {datos_json.get('region', 'N/A')}
- Ubicación: {datos_json.get('ubicacion_campo', 'N/A')}
- Red: {datos_json.get('red', 'N/A')}
- Clasificación: {datos_json.get('clasificacion', 'N/A')}
- Corriente: {datos_json.get('corriente', 'N/A')}
- Etiqueta completa: {datos_json.get('label', 'N/A')}

COORDENADAS:
- Latitud: {datos_json.get('latitud', 'N/A')}
- Longitud: {datos_json.get('longitud', 'N/A')}
"""
    
    # Información detallada de sensores
    sensores_info = "\nMEDICIONES ACTUALES DE SENSORES:\n"
    
    if 'sensores' in datos_json and isinstance(datos_json['sensores'], dict):
        for sensor_tipo, sensor_data in datos_json['sensores'].items():
            if isinstance(sensor_data, dict):
                nombre = sensor_data.get('parametro_nombre_corto', sensor_tipo)
                valor = sensor_data.get('valor', 'N/A')
                categoria = sensor_data.get('categoria_value', 'N/A')
                codigo = sensor_data.get('codigo', 'N/A')
                indice = sensor_data.get('indice', 'N/A')
                
                sensores_info += f"""
• {nombre} ({sensor_tipo}):
  - Valor actual: {valor}
  - Estado/Categoría: {categoria}
  - Código: {codigo}
  - Índice: {indice}
"""
    
    return info_basica + sensores_info + """
CONTEXTO ADICIONAL:
Esta estación forma parte de la red de monitoreo ambiental de CORNARE y mide diversos parámetros 
de calidad del aire, condiciones meteorológicas y otros factores ambientales en tiempo real.
"""

def consultar_openai(prompt, contexto, api_key):
    """Realiza consulta a OpenAI con el contexto de los datos"""
    try:
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": f"""Eres un especialista en monitoreo ambiental y calidad del aire de CORNARE 
                    (Corporación Autónoma Regional del Centro de Antioquia). 
                    
                    Tienes experiencia en:
                    - Análisis de calidad del aire y contaminantes atmosféricos
                    - Interpretación de índices de calidad ambiental
                    - Parámetros meteorológicos y su impacto en la salud
                    - Material particulado (PM2.5, PM10), gases como NO₂, O₃, CO, SO₂
                    - Compuestos como H₂S, NH₃, VOC
                    - Mediciones de ruido ambiental
                    
                    Responde preguntas basándote únicamente en los siguientes datos de la estación:
                    
                    {contexto}
                    
                    INSTRUCCIONES:
                    - Proporciona respuestas claras, técnicas pero comprensibles
                    - Interpreta los valores según estándares de calidad del aire
                    - Explica qué significan las categorías (Buena, Moderada, etc.)
                    - Si un valor indica riesgo para la salud, menciónalo
                    - Si no tienes información específica, menciona que no está disponible
                    - Usa unidades de medida apropiadas cuando sea relevante
                    - Relaciona los datos con posibles impactos ambientales o de salud cuando sea apropiado"""
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=1200,
            temperature=0.3
        )
        
        return response.choices[0].message.content, None
    except Exception as e:
        return None, f"Error con OpenAI: {str(e)}"

# Botón para obtener datos
if st.sidebar.button("🔄 Obtener Datos de Estación", type="primary"):
    if estacion_id:
        with st.spinner("Obteniendo datos de la estación..."):
            datos, error = obtener_datos_estacion(estacion_id, verificar_ssl)
            
        if datos:
            st.session_state['datos_estacion'] = datos
            st.session_state['estacion_id'] = estacion_id
            st.success(f"✅ Datos obtenidos exitosamente para la estación {estacion_id}")
        else:
            st.error(f"❌ {error}")
    else:
        st.warning("⚠️ Por favor ingresa un ID de estación")

# Mostrar datos si están disponibles
if 'datos_estacion' in st.session_state:
    datos = st.session_state['datos_estacion']
    
    # Crear dos columnas
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📊 Información de la Estación")
        
        # Información básica
        st.subheader("ℹ️ Datos Generales")
        st.write(f"**ID:** {datos.get('id', 'N/A')}")
        st.write(f"**Código:** {datos.get('codigo', 'N/A')}")
        st.write(f"**Ubicación:** {datos.get('ubicacion_campo', 'N/A')}")
        st.write(f"**Red:** {datos.get('red', 'N/A')}")
        st.write(f"**Clasificación:** {datos.get('clasificacion', 'N/A')}")
        
        # Coordenadas y mapa
        st.subheader("🗺️ Ubicación")
        st.write(f"**Latitud:** {datos.get('latitud', 'N/A')}")
        st.write(f"**Longitud:** {datos.get('longitud', 'N/A')}")
        
        # Mostrar mapa si tenemos coordenadas válidas
        if datos.get('latitud') and datos.get('longitud'):
            try:
                map_data = pd.DataFrame({
                    'lat': [float(datos['latitud'])],
                    'lon': [float(datos['longitud'])]
                })
                st.map(map_data, zoom=12)
            except (ValueError, TypeError):
                st.write("*(Coordenadas no válidas para mostrar mapa)*")
        
        # Sensores
        if 'sensores' in datos and datos['sensores']:
            st.subheader("🔬 Sensores y Mediciones")
            sensores = datos['sensores']
            
            # Crear DataFrame con información de sensores para mejor visualización
            if isinstance(sensores, dict):
                sensor_data = []
                for sensor_tipo, sensor_info in sensores.items():
                    if isinstance(sensor_info, dict):
                        sensor_data.append({
                            'Parámetro': sensor_info.get('parametro_nombre_corto', sensor_tipo),
                            'Valor': sensor_info.get('valor', 'N/A'),
                            'Categoría': sensor_info.get('categoria_value', 'N/A'),
                            'Código': sensor_info.get('codigo', 'N/A'),
                            'Índice': sensor_info.get('indice', 'N/A')
                        })
                
                if sensor_data:
                    df_sensores = pd.DataFrame(sensor_data)
                    st.dataframe(df_sensores, use_container_width=True)
                    
                    # Mostrar métricas destacadas
                    st.subheader("📊 Mediciones Destacadas")
                    
                    # Crear columnas para métricas
                    metrics_cols = st.columns(4)
                    
                    # Métricas importantes
                    importantes = ['temperatura', 'humedad', 'PM25', 'O3']
                    col_idx = 0
                    
                    for param in importantes:
                        if param in sensores:
                            sensor = sensores[param]
                            with metrics_cols[col_idx % 4]:
                                st.metric(
                                    label=sensor.get('parametro_nombre_corto', param),
                                    value=f"{sensor.get('valor', 'N/A')}",
                                    help=f"Categoría: {sensor.get('categoria_value', 'N/A')}"
                                )
                            col_idx += 1
                    
                    # Alertas por categorías
                    st.subheader("⚠️ Estado de Calidad del Aire")
                    categorias_malas = []
                    categorias_buenas = []
                    
                    for sensor_tipo, sensor_info in sensores.items():
                        categoria = sensor_info.get('categoria_value', '').lower()
                        param_nombre = sensor_info.get('parametro_nombre_corto', sensor_tipo)
                        
                        if categoria in ['mala', 'muy mala', 'dañina', 'peligrosa', 'naranja']:
                            categorias_malas.append(f"{param_nombre}: {categoria}")
                        elif categoria in ['buena', 'moderada', 'seguro']:
                            categorias_buenas.append(f"{param_nombre}: {categoria}")
                    
                    if categorias_malas:
                        st.error("🚨 **Parámetros con alertas:**")
                        for item in categorias_malas:
                            st.write(f"- {item}")
                    
                    if categorias_buenas:
                        st.success("✅ **Parámetros en buen estado:**")
                        for item in categorias_buenas[:5]:  # Mostrar solo los primeros 5
                            st.write(f"- {item}")
                        if len(categorias_buenas) > 5:
                            st.write(f"... y {len(categorias_buenas) - 5} más")
    
    with col2:
        st.header("🤖 Consulta con IA")
        
        if openai_api_key:
            # Campo para preguntas
            pregunta = st.text_area(
                "💬 Haz una pregunta sobre los datos de la estación:",
                placeholder="Ej: ¿Los niveles de PM2.5 están dentro de los límites seguros? ¿Qué tan buena es la calidad del aire actual? ¿Hay algún contaminante en niveles preocupantes?",
                height=100
            )
            
            if st.button("🚀 Consultar IA") and pregunta:
                with st.spinner("Consultando con IA..."):
                    contexto = formatear_datos_para_ai(datos)
                    respuesta, error = consultar_openai(pregunta, contexto, openai_api_key)
                
                if respuesta:
                    st.subheader("💡 Respuesta de IA:")
                    st.write(respuesta)
                else:
                    st.error(f"❌ {error}")
            
            # Preguntas sugeridas
            st.subheader("💡 Preguntas Sugeridas:")
            preguntas_sugeridas = [
                "¿Cuál es la calidad del aire actual en esta estación?",
                "¿Qué parámetros están en estado de alerta?",
                "¿Cuáles son los valores de PM2.5 y PM10?",
                "¿Cómo están los niveles de ozono y dióxido de nitrógeno?",
                "¿Cuáles son las condiciones meteorológicas actuales?",
                "¿Hay algún contaminante que supere los límites normales?",
                "Compara los valores de material particulado",
                "¿Qué significa el índice de cada sensor?",
                "¿Dónde exactamente está ubicada esta estación?",
                "Resume el estado ambiental general de la zona"
            ]
            
            for pregunta_sug in preguntas_sugeridas:
                if st.button(pregunta_sug, key=f"sug_{pregunta_sug}"):
                    with st.spinner("Consultando con IA..."):
                        contexto = formatear_datos_para_ai(datos)
                        respuesta, error = consultar_openai(pregunta_sug, contexto, openai_api_key)
                    
                    if respuesta:
                        st.subheader("💡 Respuesta de IA:")
                        st.write(respuesta)
                    else:
                        st.error(f"❌ {error}")
        else:
            st.warning("⚠️ Por favor ingresa tu API Key de OpenAI en la barra lateral para usar las funciones de IA")
    
    # Mostrar JSON raw
    with st.expander("🔍 Ver JSON completo"):
        st.json(datos)

else:
    st.info("👈 Ingresa un ID de estación en la barra lateral y haz clic en 'Obtener Datos' para comenzar")

# Footer
st.markdown("---")
st.markdown("**Desarrollado para consulta de datos meteorológicos de CORNARE**")
st.markdown("*Asegúrate de tener una API Key válida de OpenAI para usar las funciones de IA*")
