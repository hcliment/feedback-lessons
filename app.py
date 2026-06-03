import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

st.set_page_config(page_title="Sistema de Respuestas en Clase", layout="wide")

# 1. Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

pestaña_profesor, pestaña_alumno = st.tabs(["📊 Vista del Profesor", "📱 Formulario Alumno"])

# --- VISTA DEL ALUMNO ---
with pestaña_alumno:
    st.header("Envía tu respuesta")
    st.write("Selecciona la pregunta actual y tu respuesta. Es 100% anónimo.")
    
    with st.form("form_test", clear_on_submit=True):
        lista_preguntas = [f"Pregunta {i}" for i in range(1, 11)]
        pregunta_seleccionada = st.selectbox("Selecciona la pregunta:", options=lista_preguntas)
        respuesta_seleccionada = st.selectbox("Selecciona tu respuesta:", options=["A", "B", "C", "D"])
        
        enviar = st.form_submit_button("Enviar Respuesta")
        
        if enviar:
            try:
                datos_existentes = conn.read(ttl=0)
                
                # Capturar hora actual en España
                zona_espana = ZoneInfo("Europe/Madrid")
                ahora = datetime.now(zona_espana).strftime("%Y-%m-%d %H:%M:%S")
                
                nueva_fila = pd.DataFrame([{
                    "Fecha y Hora": ahora,
                    "Pregunta": pregunta_seleccionada,
                    "Respuesta": respuesta_seleccionada
                }])
                
                datos_actualizados = pd.concat([datos_existentes, nueva_fila], ignore_index=True)
                conn.update(data=datos_actualizados)
                
                st.success(f"¡Hecho! Tu respuesta '{respuesta_seleccionada}' para la '{pregunta_seleccionada}' ha sido enviada.")
            except Exception as e:
                st.error(f"Error al guardar: {e}")

# --- VISTA DEL PROFESOR ---
with pestaña_profesor:
    st.title("Resultados del Test en Directo")
    
    # Añadimos un pequeño selector para que, si una clase se alarga, puedas cambiar el rango de tiempo desde la propia pantalla
    horas_filtro = st.sidebar.slider("Mostrar respuestas de las últimas (horas):", min_value=1, max_value=8, value=3)
    
    if st.button("🔄 Actualizar Gráficos"):
        st.rerun()
        
    try:
        # Leer datos de la nube
        df = conn.read(ttl=0)
        df = df.dropna(how="all")
        
        if not df.empty:
            # 1. Convertir la columna "Fecha y Hora" de texto a formato fecha de pandas para poder operar con ella
            df["Fecha y Hora"] = pd.to_datetime(df["Fecha y Hora"])
            
            # 2. Calcular el momento exacto "hace X horas" usando la misma zona horaria
            zona_espana = ZoneInfo("Europe/Madrid")
            ahora_mismo = datetime.now(zona_espana)
            hace_unas_horas = ahora_mismo - timedelta(hours=horas_filtro)
            
            # 3. FILTRAR: Nos quedamos solo con las filas cuya fecha sea posterior al límite que hemos calculado
            # Como df["Fecha y Hora"] puede no tener zona horaria explícita al leer de Sheets, le quitamos la zona horaria a 'hace_unas_horas' para poder compararlos
            hace_unas_horas_naive = hace_unas_horas.replace(tzinfo=None)
            df_reciente = df[df["Fecha y Hora"] >= hace_unas_horas_naive]
            
            st.metric(label=f"Respuestas recibidas en las últimas {horas_filtro} horas", value=len(df_reciente))
            
            if not df_reciente.empty:
                st.markdown("---")
                lista_preguntas_profesor = [f"Pregunta {i}" for i in range(1, 11)]
                pregunta_a_mostrar = st.selectbox("📊 Selecciona qué pregunta quieres analizar en pantalla:", options=lista_preguntas_profesor)
                
                # Filtrar el DataFrame ya recortado por tiempo, ahora por la pregunta elegida
                df_filtrado = df_reciente[df_reciente["Pregunta"] == pregunta_a_mostrar]
                
                st.subheader(f"Distribución de respuestas recientes para la {pregunta_a_mostrar}")
                st.metric(label=f"Alumnos que han respondido a esta pregunta en esta sesión", value=len(df_filtrado))
                
                if not df_filtrado.empty:
                    conteo_respuestas = df_filtrado["Respuesta"].value_counts()
                    
                    for letra in ["A", "B", "C", "D"]:
                        if letra not in conteo_respuestas:
                            conteo_respuestas[letra] = 0
                    
                    conteo_respuestas = conteo_respuestas.reindex(["A", "B", "C", "D"])
                    st.bar_chart(conteo_respuestas)
                    
                    with st.expander("Ver historial reciente de esta pregunta (Anónimo)"):
                        # Mostramos la hora en formato bonito de nuevo para la tabla
                        df_tabla = df_filtrado.copy()
                        df_tabla["Fecha y Hora"] = df_tabla["Fecha y Hora"].dt.strftime("%H:%M:%S")
                        st.dataframe(df_tabla[["Fecha y Hora", "Respuesta"]].sort_values(by="Fecha y Hora", ascending=False))
                else:
                    st.info(f"Nadie ha respondido aún a la {pregunta_a_mostrar} en esta sesión.")
            else:
                st.info(f"No se han recibido respuestas en las últimas {horas_filtro} horas. Las respuestas antiguas están guardadas de forma segura en tu Google Sheets, pero ocultas en esta pantalla.")
        else:
            st.info("La hoja de cálculo está completamente vacía.")
            
    except Exception as e:
        st.warning(f"Esperando datos o configurando la conexión... (Detalle: {e})")
