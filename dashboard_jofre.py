import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
import re

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
# MOTOR DE BÚSQUEDA 
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
                
                # Clasificación de fuente MEJORADA (Lee link y titulo)
                fuente = "Prensa"
                cuenta = "Medio de Prensa" 
                texto_busqueda = (link + " " + titulo).lower()
                
                if "twitter.com" in texto_busqueda or "x.com" in texto_busqueda or " en x:" in titulo.lower() or " on x:" in titulo.lower(): 
                    fuente = "X (Twitter)"
                    if " en X:" in titulo:
                        cuenta = titulo.split(" en X:")[0].strip()
                    elif " on X:" in titulo:
                        cuenta = titulo.split(" on X:")[0].strip()
                    else:
                        cuenta = "Usuario X"
                        
                elif "linkedin.com" in texto_busqueda or " | linkedin" in titulo.lower(): 
                    fuente = "LinkedIn"
                    if " | LinkedIn" in titulo:
                        partes = titulo.split(" | LinkedIn")[0].split("-")
                        cuenta = partes[-1].strip() if len(partes) > 1 else partes[0].strip()
                    else:
                        cuenta = "Usuario LinkedIn"
                        
                elif "facebook.com" in texto_busqueda or " - facebook" in titulo.lower(): 
                    fuente = "Facebook"
                    cuenta = "LeonardoJofreR" if "leonardojofrer" in texto_busqueda else "Usuario Facebook"
                    
                elif "instagram.com" in texto_busqueda or " - instagram" in titulo.lower():
                    fuente = "Instagram"
                    cuenta = "leojofrerios" if "leojofrerios" in texto_busqueda else "Usuario Instagram"
                
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
        
        # 2. Búsqueda Específica de Rastro (Las cuentas oficiales)
        busqueda_cuentas = '"@LeoJofreRios" OR "@leojofrerios" OR "leojofrerios" OR "LeonardoJofreR"'
        
        # Unimos las búsquedas
        busqueda_total = f'({busqueda_general}) OR ({busqueda_cuentas})'
        
        # 3. Extraemos datos
        df_prensa = buscar_menciones(busqueda_total)
        df_x = buscar_menciones(busqueda_total, "twitter.com")
        df_linkedin = buscar_menciones(busqueda_total, "linkedin.com")
        df_ig = buscar_menciones(busqueda_total, "instagram.com")
        
        # Unimos, eliminamos duplicados y ordenamos de MÁS NUEVO a MÁS VIEJO
        df_total = pd.concat([df_prensa, df_x, df_linkedin, df_ig]).drop_duplicates(subset=['Link']).reset_index(drop=True)
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

    # --- PESTAÑAS DINÁMICAS ---
    df_social = df_total[df_total['Fuente'].isin(['X (Twitter)', 'LinkedIn', 'Facebook', 'Instagram'])]
    df_medios = df_total[df_total['Fuente'] == 'Prensa']
    
    nombres_pestanas = []
    
    if not df_social.empty:
        nombres_pestanas.append("📱 Ecosistema Redes") 
        
    nombres_pestanas.extend(["📰 Medios y Prensa", "🗄️ Base de Datos", "👣 Rastro Cuentas Oficiales"])
    
    pestanas = st.tabs(nombres_pestanas)
    indice = 0
    
    # PESTAÑA 1 (Opcional): Ecosistema Redes
    if not df_social.empty:
        with pestanas[indice]:
            col_graf1, col_graf2 = st.columns(2)
            
            with col_graf1:
                fig_social = px.histogram(df_social, x="Fuente", color="Sentimiento", 
                                          color_discrete_map={"Positivo":"#00cc96", "Neutral":"#7f7f7f", "Negativo":"#ff4b4b"},
                                          title="Sentimiento por Red Social")
                st.plotly_chart(fig_social, use_container_width=True)
                
            with col_graf2:
                # Filtramos al cliente del top de cuentas para no mostrar lo "obvio"
                df_social_otros = df_social[~df_social['Cuenta / Autor'].str.contains('LeoJofreRios|leojofrerios|LeonardoJofreR', case=False, na=False)]
                top_cuentas = df_social_otros['Cuenta / Autor'].value_counts().reset_index().head(5)
                top_cuentas.columns = ['Cuenta', 'Menciones']
                
                fig_cuentas = px.bar(top_cuentas, x='Menciones', y='Cuenta', orientation='h',
                                     title="Top 5: Cuentas de Terceros Más Activas", color='Menciones',
                                     color_continuous_scale='Blues')
                fig_cuentas.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_cuentas, use_container_width=True)
            
            st.markdown("#### Últimas Interacciones en Redes (Generales)")
            for _, row in df_social.head(5).iterrows():
                # Destacar si es positiva o negativa de forma sencilla
                icono = "🟢" if row['Sentimiento'] == 'Positivo' else ("🔴" if row['Sentimiento'] == 'Negativo' else "⚪")
                st.info(f"{icono} **{row['Cuenta / Autor']}** en {row['Fuente']} ({row['Fecha']}): [{row['Título / Mención']}]({row['Link']})")
                
        indice += 1

    # PESTAÑA 2: Prensa
    with pestanas[indice]:
        if not df_medios.empty:
            fig_timeline = px.scatter(df_medios, x="Fecha", y="Puntaje", color="Sentimiento",
                                      color_discrete_map={"Positivo":"#00cc96", "Neutral":"#7f7f7f", "Negativo":"#ff4b4b"},
                                      size_max=10, hover_data=['Título / Mención'],
                                      title="Línea de Tiempo de Medios (Impacto Positivo/Negativo)")
            st.plotly_chart(fig_timeline, use_container_width=True)
        else:
            st.info("No hay menciones en prensa recientemente.")
            
    indice += 1 
            
    # PESTAÑA 3: Base de datos
    with pestanas[indice]:
        st.markdown("Base de datos exportable con el algoritmo de sentimiento aplicado. (Ordenada por más reciente)")
        st.dataframe(df_total.style.map(
            lambda x: 'background-color: #ffcccc' if x == 'Negativo' else ('background-color: #ccffcc' if x == 'Positivo' else ''),
            subset=['Sentimiento']
        ))

    indice += 1

    # PESTAÑA 4: Rastro Oficial (SOLO TERCEROS CON VALORACIÓN)
    with pestanas[indice]:
        st.markdown("### Menciones Directas por Terceros")
        st.markdown("Rastro digital de **terceros** interactuando con **@LeoJofreRios** (X), **@leojofrerios** (IG) y **LeonardoJofreR** (FB). *(Excluye posteos propios)*")
        
        filtro_cuentas = df_total['Título / Mención'].str.contains('LeoJofreRios|leojofrerios|LeonardoJofreR', case=False, na=False) | df_total['Link'].str.contains('LeoJofreRios|leojofrerios|LeonardoJofreR', case=False, na=False)
        # Filtro clave: NO mostrar posteos donde el autor sea el cliente
        filtro_no_cliente = ~df_total['Cuenta / Autor'].str.contains('LeoJofreRios|leojofrerios|LeonardoJofreR', case=False, na=False)
        
        df_oficial = df_total[filtro_cuentas & filtro_no_cliente]
        
        if not df_oficial.empty:
            st.success(f"Se han detectado {len(df_oficial)} menciones directas por parte de terceros hacia los perfiles oficiales.")
            for _, row in df_oficial.head(10).iterrows():
                
                # Asignamos color según la valoración
                color_sent = "#00cc96" if row['Sentimiento'] == 'Positivo' else ("#ff4b4b" if row['Sentimiento'] == 'Negativo' else "#7f7f7f")
                
                st.markdown(f"""
                <div style='padding:15px; border-left: 6px solid {color_sent}; background-color: #f8f9fa; margin-bottom: 15px; border-radius: 5px;'>
                    <div style='display: flex; justify-content: space-between; margin-bottom: 8px;'>
                        <span><strong>{row['Fuente']}</strong> | Fecha: {row['Fecha']}</span>
                        <span style='color:{color_sent}; font-weight: bold;'>Valoración: {row['Sentimiento']} ({row['Puntaje']:.1f})</span>
                    </div>
                    <i style='font-size: 1.1em;'>{row['Título / Mención']}</i> <br><br>
                    <a href='{row['Link']}' target='_blank' style='text-decoration: none; color: #1f77b4;'>🔗 Ver publicación original</a>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No se han detectado interacciones recientes de terceros hacia las cuentas oficiales.")

if __name__ == "__main__":
    main()
