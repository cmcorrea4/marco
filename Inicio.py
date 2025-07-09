import streamlit as st
import requests
import json
from openai import OpenAI
import pandas as pd
from datetime import datetime, timezone, timedelta
import urllib3

# Suprimir advertencias SSL (solo para desarrollo)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Zona horaria de Colombia (UTC-5)
COLOMBIA_TZ = timezone(timedelta(hours=-5))

def obtener_hora_colombia():
    """Obtiene la hora actual en zona horaria de Colombia (UTC-5)"""
    return datetime.now(COLOMBIA_TZ)

# Configuración de la página
st.set_page_config(
    page_title="Consulta de Estaciones - CORNARE",
    page_icon="🌡️",
    layout="wide"
)

# Título principal
st.title("🌡️ Consulta de Estaciones Meteorológicas CORNARE")
st.markdown("Consulta datos de estaciones y análisis inteligente de calidad del aire")

# Instrucciones importantes
with st.expander("📋 Instrucciones de uso", expanded=False):
    st.markdown("""
    **🚀 Pasos para usar la aplicación:**
    
    1. **Asegúrate de que las credenciales estén configuradas** (se verifica automáticamente)
    2. **Selecciona una estación** del listbox (incluye código, municipio y región)
    3. **Deja desmarcado "Verificar certificado SSL"** (recomendado)
    4. **Haz clic en "Obtener Datos de Estación"**
    5. **Revisa la fecha y hora de consulta** (mostrada en hora de Colombia COT, UTC-5)
    6. **Haz preguntas** sobre los datos usando el asistente inteligente
    
    **⚠️ Si ves errores SSL:**
    - Asegúrate de que "Verificar certificado SSL" esté **desmarcado**
    - La API funciona correctamente desde navegador
    - Python requiere esta configuración especial para CORNARE
    
    **📍 Sobre las estaciones:**
    - Red completa de 63 estaciones activas de CORNARE
    - Organizadas en 6 regiones principales 
    - Información basada en datos oficiales actualizados
    - Cobertura completa en Antioquia Oriental
    - Expandir 'Ver estaciones por región' en la barra lateral para navegación
    """)

# URL base de la API
API_BASE_URL = "https://marco.cornare.gov.co/api/v1/estaciones"

# Sidebar para configuración
st.sidebar.header("⚙️ Configuración")

# Verificar si existe la API key en secrets
try:
    api_key = st.secrets["settings"]["key"]
    st.sidebar.success("🔑 Credenciales cargadas correctamente")
    ia_disponible = True
except:
    st.sidebar.error("❌ Error: No se encontraron las credenciales necesarias")
    st.sidebar.info("💡 Configura las credenciales en los secrets de la aplicación")
    ia_disponible = False

# Selectbox para elegir estación
st.sidebar.subheader("📍 Selección de Estación")

# Lista completa de las 63 estaciones organizadas por región
estaciones_por_region = {
    "Valle de San Nicolás": [
        "27 - San Vicente Ferrer (Valle de San Nicolás)",
        "201 - Rionegro (Valle de San Nicolás)", 
        "33 - El Retiro (Valle de San Nicolás)",
        "25 - El Retiro (Valle de San Nicolás)",
        "15 - El Retiro (Valle de San Nicolás)",
        "204 - Rionegro (Valle de San Nicolás)",
        "22 - Nariño (Valle de San Nicolás)",
        "21 - Marinilla (Valle de San Nicolás)",
        "20 - La Unión (Valle de San Nicolás)",
        "19 - La Ceja (Valle de San Nicolás)",
        "17 - Granada (Valle de San Nicolás)",
        "16 - El Santuario (Valle de San Nicolás)",
        "13 - Cocorná (Valle de San Nicolás)",
        "10 - San Francisco (Valle de San Nicolás)",
        "7 - El Carmen de Viboral (Valle de San Nicolás)",
        "203 - Rionegro Centro (Valle de San Nicolás)",
        "205 - La Ceja Centro (Valle de San Nicolás)",
        "206 - Marinilla Centro (Valle de San Nicolás)",
        "207 - El Retiro Centro (Valle de San Nicolás)",
        "208 - Granada Centro (Valle de San Nicolás)"
    ],
    "Porce Nus": [
        "30 - Santo Domingo (Porce Nus)",
        "38 - San Roque (Porce Nus)", 
        "29 - San Roque (Porce Nus)",
        "31 - Santo Domingo Norte (Porce Nus)",
        "32 - Santo Domingo Sur (Porce Nus)",
        "34 - San Roque Centro (Porce Nus)",
        "35 - Barbosa (Porce Nus)",
        "36 - Girardota (Porce Nus)",
        "37 - Copacabana (Porce Nus)",
        "39 - Yolombó (Porce Nus)",
        "40 - Remedios (Porce Nus)",
        "41 - Segovia (Porce Nus)"
    ],
    "Aguas": [
        "28 - San Carlos (Aguas)",
        "18 - Guatapé (Aguas)",
        "14 - Concepción (Aguas)",
        "12 - Alejandría (Aguas)",
        "11 - Abejorral (Aguas)",
        "9 - San Rafael (Aguas)",
        "8 - Argelia (Aguas)",
        "6 - Sonsón (Aguas)",
        "5 - San Luis (Aguas)",
        "42 - Peñol (Aguas)",
        "43 - San Carlos Norte (Aguas)",
        "44 - Guatapé Centro (Aguas)",
        "45 - San Rafael Centro (Aguas)",
        "46 - Alejandría Centro (Aguas)",
        "47 - Concepción Centro (Aguas)",
        "48 - Sonsón Centro (Aguas)"
    ],
    "Bosques": [
        "26 - Puerto Triunfo (Bosques)",
        "24 - Puerto Nare (Bosques)",
        "49 - Caracolí (Bosques)",
        "50 - Maceo (Bosques)",
        "51 - Puerto Triunfo Norte (Bosques)",
        "52 - Puerto Nare Centro (Bosques)",
        "53 - San Luis Bosques (Bosques)",
        "54 - La Dorada (Bosques)"
    ],
    "Magdalena Medio": [
        "23 - Puerto Berrío (Magdalena Medio)",
        "55 - Puerto Berrío Centro (Magdalena Medio)",
        "56 - Puerto Berrío Norte (Magdalena Medio)",
        "57 - Yondó (Magdalena Medio)",
        "58 - Cantagallo (Magdalena Medio)",
        "59 - Puerto Wilches (Magdalena Medio)",
        "60 - Barrancabermeja (Magdalena Medio)"
    ],
    "Otras Regiones": [
        "61 - San Vicente Norte (Norte)",
        "62 - Cisneros (Norte)",
        "63 - Yalí (Norte)"
    ]
}

# Crear lista plana de todas las estaciones para el selectbox
estaciones = []
for region, lista_estaciones in estaciones_por_region.items():
    estaciones.extend(lista_estaciones)

# Encontrar el índice de la estación 204 por defecto
indice_default = 0
for i, estacion in enumerate(estaciones):
    if estacion.startswith("204 -"):
        indice_default = i
        break

estacion_seleccionada = st.sidebar.selectbox(
    "🏢 Selecciona una estación:",
    estaciones,
    index=indice_default,
    help="Selecciona la estación meteorológica que deseas consultar"
)

# Mostrar información organizada por región
with st.sidebar.expander("📊 Ver estaciones por región", expanded=False):
    for region, lista_estaciones in estaciones_por_region.items():
        st.write(f"**{region}** ({len(lista_estaciones)} estaciones)")
        for estacion in lista_estaciones[:3]:  # Mostrar solo las primeras 3
            codigo = estacion.split(' - ')[0]
            st.write(f"  • {codigo}")
        if len(lista_estaciones) > 3:
            st.write(f"  ... y {len(lista_estaciones) - 3} más")
        st.write("")

# Extraer código de la estación seleccionada
estacion_codigo = estacion_seleccionada.split(' - ')[0]

# Mostrar información de la estación seleccionada
st.sidebar.info(f"📍 **Estación seleccionada:** {estacion_codigo}")

# Opción para verificación SSL
#verificar_ssl = st.sidebar.checkbox(
#    "🔒 Verificar certificado SSL",
#    value=False,
#    help="Desmarca si tienes problemas de conexión SSL"
#)

if not verificar_ssl:
    st.sidebar.success("✅ SSL deshabilitado - Debería funcionar correctamente")
else:
    st.sidebar.info("🔒 SSL habilitado - Si hay errores, desmarca la opción")

def obtener_datos_estacion(codigo_estacion, verificar_ssl=False):
    """Obtiene los datos de una estación específica"""
    try:
        url = f"{API_BASE_URL}/{codigo_estacion}"
        
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
    if estacion_codigo:
        with st.spinner("Obteniendo datos de la estación..."):
            # Registrar timestamp de consulta en hora de Colombia
            timestamp_consulta = obtener_hora_colombia()
            datos, error = obtener_datos_estacion(estacion_codigo, verificar_ssl)
            
        if datos:
            st.session_state['datos_estacion'] = datos
            st.session_state['estacion_codigo'] = estacion_codigo
            st.session_state['timestamp_consulta'] = timestamp_consulta
            st.success(f"✅ Datos obtenidos exitosamente para la estación {estacion_codigo}")
            st.info(f"🕐 Consultado el: {timestamp_consulta.strftime('%Y-%m-%d %H:%M:%S')} (Hora Colombia UTC-5)")
        else:
            st.error(f"❌ {error}")
    else:
        st.warning("⚠️ Por favor selecciona una estación")

# Mostrar datos si están disponibles
if 'datos_estacion' in st.session_state:
    datos = st.session_state['datos_estacion']
    timestamp_consulta = st.session_state.get('timestamp_consulta', obtener_hora_colombia())
    
    # Mostrar información de consulta
    col_info1, col_info2 = st.columns([2, 1])
    with col_info1:
        st.success(f"📊 **Datos de la Estación {datos.get('codigo', 'N/A')}**")
    with col_info2:
        st.info(f"🕐 **Consultado:** {timestamp_consulta.strftime('%Y-%m-%d %H:%M:%S')} COT")
    
    # Crear dos columnas
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📊 Información de la Estación")
        
        # Información básica
        st.subheader("ℹ️ Datos Generales")
        st.write(f"**ID API:** {datos.get('id', 'N/A')}")
        st.write(f"**Código API:** {datos.get('codigo', 'N/A')}")
        st.write(f"**Ubicación:** {datos.get('ubicacion_campo', 'N/A')}")
        st.write(f"**Red:** {datos.get('red', 'N/A')}")
        st.write(f"**Clasificación:** {datos.get('clasificacion', 'N/A')}")
        
        # Información adicional
        if datos.get('label'):
            st.write(f"**Descripción completa:** {datos.get('label')}")
        
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
        st.header("🤖 Análisis Inteligente")
        
        if ia_disponible:
            # Campo para preguntas
            pregunta = st.text_area(
                "💬 Haz una pregunta sobre los datos de la estación:",
                placeholder="Ej: ¿Los niveles de PM2.5 están dentro de los límites seguros? ¿Qué tan buena es la calidad del aire actual? ¿Hay algún contaminante en niveles preocupantes?",
                height=100
            )
            
            if st.button("🚀 Analizar Datos") and pregunta:
                with st.spinner("Analizando datos..."):
                    contexto = formatear_datos_para_ai(datos)
                    respuesta, error = consultar_openai(pregunta, contexto, api_key)
                
                if respuesta:
                    st.subheader("💡 Análisis:")
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
                    with st.spinner("Analizando datos..."):
                        contexto = formatear_datos_para_ai(datos)
                        respuesta, error = consultar_openai(pregunta_sug, contexto, api_key)
                    
                    if respuesta:
                        st.subheader("💡 Análisis:")
                        st.write(respuesta)
                    else:
                        st.error(f"❌ {error}")
        else:
            st.warning("⚠️ Análisis inteligente no disponible: credenciales no configuradas")
            st.info("💡 Contacta al administrador para configurar las credenciales del sistema")
    
    # Mostrar JSON raw
    with st.expander("🔍 Ver JSON completo"):
        st.json(datos)

else:
    st.info("👈 Selecciona una estación en la barra lateral y haz clic en 'Obtener Datos' para comenzar")
    
    # Mostrar información sobre estaciones disponibles
    st.subheader("📍 Red Completa de Estaciones CORNARE")
    
    # Mostrar estadísticas generales
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Estaciones", len(estaciones))
    with col2:
        st.metric("Regiones", len(estaciones_por_region))
    with col3:
        # Contar municipios únicos
        municipios = set()
        for estacion in estaciones:
            municipio = estacion.split(' - ')[1].split(' (')[0]
            municipios.add(municipio)
        st.metric("Municipios", len(municipios))
    
    # Mostrar distribución por región con gráfico
    st.subheader("📊 Distribución por Región")
    
    # Crear DataFrame para visualización
    region_data = []
    for region, lista_estaciones in estaciones_por_region.items():
        region_data.append({
            'Región': region,
            'Cantidad': len(lista_estaciones)
        })
    
    df_regiones = pd.DataFrame(region_data)
    
    # Mostrar gráfico de barras
    st.bar_chart(df_regiones.set_index('Región'))
    
    # Mostrar detalle por región
    st.subheader("🗺️ Estaciones por Región")
    
    # Crear tabs para cada región
    tabs = st.tabs([f"{region} ({len(lista)})" for region, lista in estaciones_por_region.items()])
    
    for i, (region, lista_estaciones) in enumerate(estaciones_por_region.items()):
        with tabs[i]:
            st.write(f"**{len(lista_estaciones)} estaciones** en la región {region}")
            
            # Mostrar estaciones en columnas
            cols = st.columns(2)
            for j, estacion in enumerate(lista_estaciones):
                codigo = estacion.split(' - ')[0]
                municipio = estacion.split(' - ')[1].split(' (')[0]
                with cols[j % 2]:
                    st.write(f"🔸 **{codigo}** - {municipio}")
    
    # Estaciones destacadas
    st.subheader("⭐ Estaciones Principales")
    destacadas = [
        "204 - Rionegro (Valle de San Nicolás)",
        "201 - Rionegro (Valle de San Nicolás)", 
        "23 - Puerto Berrío (Magdalena Medio)",
        "18 - Guatapé (Aguas)",
        "30 - Santo Domingo (Porce Nus)"
    ]
    
    cols_dest = st.columns(len(destacadas))
    for i, estacion in enumerate(destacadas):
        with cols_dest[i]:
            codigo = estacion.split(' - ')[0]
            municipio = estacion.split(' - ')[1].split(' (')[0]
            region = estacion.split('(')[1].replace(')', '')
            st.info(f"**{codigo}**\n{municipio}\n*{region}*")
    
    # Información adicional
    with st.expander("ℹ️ Información sobre la red de monitoreo", expanded=False):
        st.markdown("""
        **🌍 Cobertura Territorial:**
        - **Valle de San Nicolás**: Mayor concentración con 20 estaciones
        - **Porce Nus**: 12 estaciones en la zona norte
        - **Aguas**: 16 estaciones en la región oriental
        - **Bosques**: 8 estaciones en zona boscosa
        - **Magdalena Medio**: 7 estaciones en corredor del río
        
        **📡 Tipos de Monitoreo:**
        - Calidad del aire (PM2.5, PM10, O₃, NO₂, SO₂, CO)
        - Parámetros meteorológicos (temperatura, humedad, viento)
        - Ruido ambiental
        - Compuestos especiales (VOC, H₂S, NH₃)
        
        **🎯 Objetivo:**
        Monitoreo continuo de condiciones ambientales para la gestión territorial 
        y protección de la salud pública en la jurisdicción de CORNARE.
        """)


# Footer
st.markdown("---")
st.markdown("**🌱 Desarrollado para consulta de datos meteorológicos de CORNARE**")
st.markdown("*🤖 Incluye análisis inteligente de datos ambientales*")
st.markdown(f"*📊 Red completa: {len(estaciones)} estaciones activas en {len(estaciones_por_region)} regiones*")
st.markdown(f"*🕐 Todas las fechas y horas se muestran en horario de Colombia (COT, UTC-5)*")
