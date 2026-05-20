import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
import re # Nueva herramienta: Expresiones regulares para limpiar textos

# ==========================================
# CONFIGURACIÓN (Avanzada)
# ==========================================
st.set_page_config(page_title="Radar de Marca | Leonardo Jofré", page_icon="⚖️", layout="wide")

# Diccionario de sentimiento ponderado
DICCIONARIO_SENTIMIENTO = {
    "excelente": 5, "brillante": 5, "destaca": 4, "logro": 4, "triunfo": 4,
    "apoyo": 3, "acuerdo": 3, "solución": 3, "verdad": 3, "justicia": 3,
    "bueno": 2, "favor": 2, "avanza": 2, "defensa": 2, "abogado": 1,
    "corrupto": -5, "delito": -5, "escándalo": -5, "fraude": -5,
    "crisis": -4, "fracaso": -4, "acusación": -4, "polémica": -4,
    "malo": -2, "contra": -2, "crítica": -3, "rechazo": -3, "error": -3,
    "investigación": -2, "duda": -2
}

def analizar_sentimiento_avanzado(texto):
    texto = texto.lower()
    puntaje_total = 0
    palabras_encontradas = 0
    
    for palabra, peso in DICCIONARIO_SENTIMIENTO.items():
        if palabra in texto:
            puntaje_total += peso
            palabras_encontradas += 1
            
    if palabras_encontradas > 0:
        promedio = puntaje_total / palabras_encontradas
    else:
        promedio = 0
        
    if promedio > 0.5: return "Positivo", promedio
    elif promedio < -0.5: return "Negativo", promedio
    else: return "Neutral", promedio

# ==========================================
# MOTOR DE BÚSQUEDA (Actualizado con variaciones y cuentas)
# ==========================================
@st.cache_data(ttl=3600)
def buscar_menciones(query_avanzada, filtro_red_social=None):
    
    query = query_avanzada
    if filtro_red_social:
        query += f' site:{filtro_red_social}'
        
    query_codificado = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={query_codificado}&hl=es-419&gl=CL&ceid=CL:es-419"
    
    try:
        respuesta = requests.get(url)
        sopa = BeautifulSoup(respuesta.content, 'xml')
        noticias = sopa.find_all('item')
        
        datos = []
        for noticia in noticias:
            titulo = noticia.title.text
            link = noticia.link.text
            fecha_str = noticia.pubDate.text
            fecha_dt = datetime.strptime(fecha_str, "%a, %d %b %Y %H:%M:%S %Z")
            
            if fecha_dt.year >= 2024:
                categoria, puntaje = analizar_sentimiento_avanzado(titulo)
                
                # Clasificación de fuente y EXTRACCIÓN DE CUENTA
                fuente = "Prensa"
                cuenta = "Medio de Prensa" # Valor por defecto
                
                if "twitter.com" in link or "x.com" in link: 
                    fuente = "X (Twitter)"
                    if " en X:" in titulo:
                        cuenta = titulo.split(" en X:")[0].strip()
                    elif " on X:" in titulo:
                        cuenta = titulo.split(" on X:")[0].strip()
                    else:
                        cuenta = "Usuario X"
                        
                elif "linkedin.com" in link: 
                    fuente = "LinkedIn"
                    if " | LinkedIn" in titulo:
                        partes = titulo.split(" | LinkedIn")[0].split("-")
                        cuenta = partes[-1].strip() if len(partes) > 1 else partes[0].strip()
                    else:
                        cuenta = "Usuario LinkedIn"
                        
                elif "facebook.com" in link: 
                    fuente = "Facebook"
                    # ¡NUEVO! Detectar la cuenta oficial de Facebook
                    cuenta = "LeonardoJofreR" if "leonardojofrer" in link.lower() else "Usuario Facebook"
                    
                # ¡NUEVO! Detectar Instagram
                elif "instagram.com" in link:
                    fuente = "Instagram"
                    cuenta = "@leojofrerios" if "leojofrerios" in link.lower() else "Usuario Instagram"
                
                datos.append({
                    "Fecha": fecha_dt.date(),
                    "Fuente": fuente,
                    "Cuenta / Autor": cuenta, 
                    "Título / Mención": titulo,
                    "Sentimiento": categoria,
                    "Puntaje": puntaje,
                    "Link": link
                })
        return pd.DataFrame(datos)
    except Exception as e:
        st.error(f"Error al buscar datos: {e}")
        return pd.DataFrame()

# ==========================================
# INTERFAZ GRÁFICA DEL DASHBOARD
# ==========================================
def main():
    st.title("⚖️ Radar de Marca Personal: Leonardo Jofré")
    st.markdown("Monitoreo avanzado de Medios y Redes Sociales")
    st.divider()

    if st.button("🔄 Actualizar Datos Ahora"):
        st.cache_data.clear()

    with st.spinner('Rastreando huella digital en web y redes sociales...'):
        # 1. Búsqueda Maestra General (El nombre)
        busqueda_general = '"Leonardo Jofré" OR "Leo Jofré" OR "Leonardo Jofre"'
        
        # 2. Búsqueda Específica de Rastro (Las cuentas oficiales incluyendo Facebook)
        busqueda_cuentas = '"@LeoJofreRios" OR "@leojofrerios" OR "leojofrerios" OR "LeonardoJofreR"'
        
        # Unimos las búsquedas para darle más alcance a nuestro radar
        busqueda_total = f'({busqueda_general}) OR ({busqueda_cuentas})'
        
        # 3. Pasamos la búsqueda a nuestras funciones
        df_prensa = buscar_menciones(busqueda_total)
        df_x = buscar_menciones(busqueda_total, "twitter.com")
        df_linkedin = buscar_menciones(busqueda_total, "linkedin.com")
        df_ig = buscar_menciones(busqueda_total, "instagram.com")
        
        # Unimos todo de forma limpia, reiniciamos el índice y ORDENAMOS DE MÁS NUEVO A MÁS VIEJO
        df_total = pd.concat([df_prensa, df_x, df_linkedin, df_ig]).drop_duplicates(subset=['Link']).reset_index(drop=True)
        
        # ¡ESTA ES LA LÍNEA CLAVE PARA EL MOMENTUM DE LA MARCA!
        df_total = df_total.sort_values(by='Fecha', ascending=False).reset_index(drop=True)

    if df_total.empty:
        st.warning("No se encontraron menciones recientes para las variaciones ni las cuentas de Leonardo Jofré.")
        return

    # --- MÉTRICAS DE SALUD DE MARCA ---
    st.subheader("📊 Salud de Marca Digital")
    
    puntaje_general = df_total['Puntaje'].mean() * 20 
    
    col_term, col_kpis = st.columns([1, 2])
    
    with col_term:
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = puntaje_general,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Índice de Reputación"},
            gauge = {
                'axis': {'range': [-100, 100]},
                'bar': {'color': "black"},
                'steps': [
                    {'range': [-100, -20], 'color': "#ff4b4b"},
                    {'range': [-20, 20], 'color': "#ffa600"}, 
                    {'range': [20, 100], 'color': "#00cc96"}  
                ]
            }
        ))
        fig_gauge.update_layout(height=250, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_kpis:
        k1, k2, k3 = st.columns(3)
        k1.metric("Total Menciones", len(df_total))
        k2.metric("Menciones en Redes", len(df_total[df_total['Fuente'] != 'Prensa']))
        
        positivas = len(df_total[df_total['Sentimiento'] == 'Positivo'])
        negativas = len(df_total[df_total['Sentimiento'] == 'Negativo'])
        k3.metric("Ratio Positivo/Negativo", f"{positivas} / {negativas}")

    st.divider()

    # --- PESTAÑAS DE ANÁLISIS ---
    # ¡Agregamos una nueva pestaña para el rastro de cuentas oficiales!
    tab_rastro, tab_redes, tab_prensa, tab_datos = st.tabs(["👣 Rastro Cuentas Oficiales", "📱 Ecosistema Redes", "📰 Medios y Prensa", "🗄️ Base de Datos"])
    
    with tab_rastro:
        st.markdown("### Seguimiento Directo de Perfiles")
        st.markdown("Rastro digital detectado apuntando o proviniendo de **@LeoJofreRios** (X), **@leojofrerios** (IG) y **LeonardoJofreR** (FB). Organizado desde lo más reciente.")
        
        # Filtramos SOLO los datos que contengan las cuentas exactas de las 3 redes
        filtro_cuentas = df_total['Título / Mención'].str.contains('LeoJofreRios|leojofrerios|LeonardoJofreR', case=False, na=False) | df_total['Link'].str.contains('LeoJofreRios|leojofrerios|LeonardoJofreR', case=False, na=False)
        df_oficial = df_total[filtro_cuentas]
        
        if not df_oficial.empty:
            st.success(f"Se han detectado {len(df_oficial)} huellas digitales asociadas directamente a los perfiles oficiales.")
            for _, row in df_oficial.head(10).iterrows():
                # Destacamos visualmente de dónde viene el rastro
                st.markdown(f"""
                <div style='padding:10px; border-left: 5px solid #1f77b4; background-color: #f0f2f6; margin-bottom: 10px;'>
                    <strong>{row['Fuente']}</strong> | Fecha: {row['Fecha']} <br>
                    <i>{row['Título / Mención']}</i> <br>
                    <a href='{row['Link']}' target='_blank'>🔗 Seguir el rastro a la fuente original</a>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("El radar no ha detectado indexaciones recientes que mencionen la cuenta exacta (es normal si no ha habido actividad viral reciente en estas cuentas).")

    with tab_redes:
        # Añadimos Instagram a la visualización de redes
        df_social = df_total[df_total['Fuente'].isin(['X (Twitter)', 'LinkedIn', 'Facebook', 'Instagram'])]
        if not df_social.empty:
            col_graf1, col_graf2 = st.columns(2)
            
            with col_graf1:
                fig_social = px.histogram(df_social, x="Fuente", color="Sentimiento", 
                                          color_discrete_map={"Positivo":"#00cc96", "Neutral":"gray", "Negativo":"#ff4b4b"},
                                          title="Sentimiento por Red Social")
                st.plotly_chart(fig_social, use_container_width=True)
                
            with col_graf2:
                top_cuentas = df_social['Cuenta / Autor'].value_counts().reset_index().head(5)
                top_cuentas.columns = ['Cuenta', 'Menciones']
                fig_cuentas = px.bar(top_cuentas, x='Menciones', y='Cuenta', orientation='h',
                                     title="Cuentas Principales (Top 5)", color='Menciones',
                                     color_continuous_scale='Blues')
                fig_cuentas.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_cuentas, use_container_width=True)
            
            st.markdown("#### Últimas Interacciones en Redes")
            for _, row in df_social.head(5).iterrows():
                st.info(f"**{row['Cuenta / Autor']}** en {row['Fuente']} ({row['Fecha']}): [{row['Título / Mención']}]({row['Link']})")
        else:
            st.info("No hay menciones indexadas en redes sociales recientemente.")

    with tab_prensa:
        df_medios = df_total[df_total['Fuente'] == 'Prensa']
        if not df_medios.empty:
            fig_timeline = px.scatter(df_medios, x="Fecha", y="Puntaje", color="Sentimiento",
                                      color_discrete_map={"Positivo":"#00cc96", "Neutral":"gray", "Negativo":"#ff4b4b"},
                                      size_max=10, hover_data=['Título / Mención'],
                                      title="Línea de Tiempo de Medios (Impacto Positivo/Negativo)")
            st.plotly_chart(fig_timeline, use_container_width=True)
        else:
            st.info("No hay menciones en prensa recientemente.")
            
    with tab_datos:
        st.markdown("Base de datos exportable con el algoritmo de sentimiento aplicado.")
        st.dataframe(df_total.style.map(
            lambda x: 'background-color: #ffcccc' if x == 'Negativo' else ('background-color: #ccffcc' if x == 'Positivo' else ''),
            subset=['Sentimiento']
        ))

if __name__ == "__main__":
    main()
