import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Sistema de Respuestas en Clase", layout="wide")

# 1. Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

pestaña_profesor, pestaña_alumno = st.tabs(["📊 Vista del Profesor", "📱 Formulario Alumno"])

# --- VISTA DEL ALUMNO ---
with pestaña_alumno:
    st.header("Envía tu respuesta")
    st.write("Selecciona la pregunta actual y tu respuesta. Es 100% anónimo.")
    
    with st.form("form_test", clear_on_submit=True):
        # Desplegable de preguntas (Pregunta 1 a Pregunta 10)
        lista_preguntas = [f"Pregunta {i}" for i in range(1, 11)]
        pregunta_seleccionada = st.selectbox("Selecciona la pregunta:", options=lista_preguntas)
        
        # Desplegable de opciones (A, B, C, D)
        respuesta_seleccionada = st.selectbox("Selecciona tu respuesta:", options=["A", "B", "C", "D"])
        
        enviar = st.form_submit_button("Enviar Respuesta")
        
        if enviar:
            try:
                # Leer datos existentes (ttl=0 para evitar caché)
                datos_existentes = conn.read(ttl=0)
                
                # Capturar la fecha y hora actual en formato legible (ej: 2026-06-03 14:30:22)
                ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Crear la nueva fila con la estructura solicitada
                nueva_fila = pd.DataFrame([{
                    "Fecha y Hora": ahora,
                    "Pregunta": pregunta_seleccionada,
                    "Respuesta": respuesta_seleccionada
                }])
                
                # Combinar y actualizar en Google Sheets
                datos_actualizados = pd.concat([datos_existentes, nueva_fila], ignore_index=True)
                conn.update(data=datos_actualizados)
                
                st.success(f"¡Hecho! Tu respuesta '{respuesta_seleccionada}' para la '{pregunta_seleccionada}' ha sido enviada.")
            except Exception as e:
                st.error(f"Error al guardar: {e}")

# --- VISTA DEL PROFESOR ---
with pestaña_profesor:
    st.title("Resultados del Test en Directo")
    
    if st.button("🔄 Actualizar Gráficos"):
        st.rerun()
        
    try:
        # Leer datos de la nube
        df = conn.read(ttl=0)
        df = df.dropna(how="all")
        
        st.metric(label="Total de respuestas recibidas (todas las preguntas)", value=len(df))
        
        if not df.empty:
            st.markdown("---")
            # Selector para que el profesor elija qué pregunta quiere proyectar en el gráfico
            lista_preguntas_profesor = [f"Pregunta {i}" for i in range(1, 11)]
            pregunta_a_mostrar = st.selectbox("📊 Selecciona qué pregunta quieres analizar en pantalla:", options=lista_preguntas_profesor)
            
            # Filtrar el DataFrame solo para la pregunta elegida
            df_filtrado = df[df["Pregunta"] == pregunta_a_mostrar]
            
            st.subheader(f"Distribución de respuestas para la {pregunta_a_mostrar}")
            st.metric(label=f"Alumnos que han respondido a esta pregunta", value=len(df_filtrado))
            
            if not df_filtrado.empty:
                # Contar cuántas veces aparece cada letra (A, B, C, D)
                conteo_respuestas = df_filtrado["Respuesta"].value_counts()
                
                # Para asegurar que el gráfico muestre siempre las 4 opciones aunque nadie haya votado a alguna:
                for letra in ["A", "B", "C", "D"]:
                    if letra not in conteo_respuestas:
                        conteo_respuestas[letra] = 0
                
                # Ordenar el índice para que salga A, B, C, D en orden en el gráfico
                conteo_respuestas = conteo_respuestas.reindex(["A", "B", "C", "D"])
                
                # Mostrar gráfico de barras
                st.bar_chart(conteo_respuestas)
                
                # Mostrar tabla con el detalle de las últimas respuestas por si acaso
                with st.expander("Ver historial de esta pregunta (Anónimo)"):
                    st.dataframe(df_filtrado[["Fecha y Hora", "Respuesta"]].sort_values(by="Fecha y Hora", ascending=False))
            else:
                st.info(f"Nadie ha respondido aún a la {pregunta_a_mostrar} en esta sesión.")
        else:
            st.info("Esperando las primeras respuestas de los alumnos...")
            
    except Exception as e:
        st.warning("Configurando la conexión o esperando datos...")
