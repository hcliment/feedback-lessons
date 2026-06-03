import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Feedback de Clase", layout="wide")

# 1. Establecer la conexión con Google Sheets
# Streamlit busca automáticamente la URL en el archivo secrets.toml
conn = st.connection("gsheets", type=GSheetsConnection)

# Crear las pestañas para el aula
pestaña_profesor, pestaña_alumno = st.tabs(["📊 Vista del Profesor", "📱 Formulario Alumno"])

# --- VISTA DEL ALUMNO (Formulario) ---
with pestaña_alumno:
    st.header("Cuestionario Anónimo")
    
    with st.form("form_feedback", clear_on_submit=True):
        ritmo = st.select_slider("1. ¿Qué tal el ritmo de la clase?", options=["Muy lento", "Adecuado", "Muy rápido"], value="Adecuado")
        comprension = st.slider("2. ¿Cuánto has comprendido hoy? (1 al 5)", 1, 5, 3)
        comentarios = st.text_area("3. ¿Alguna duda o comentario?")
        
        enviar = st.form_submit_button("Enviar Feedback")
        
        if enviar:
            try:
                # Leer los datos existentes para no borrar lo que ya hay
                datos_existentes = conn.read(ttl=0) # ttl=0 fuerza a leer los datos más frescos
                
                # Crear la nueva fila con la respuesta del alumno
                nueva_respuesta = pd.DataFrame([{
                    "Ritmo": ritmo,
                    "Comprensión": comprension,
                    "Comentarios": comentarios
                }])
                
                # Combinar los datos viejos con los nuevos
                datos_actualizados = pd.concat([datos_existentes, nueva_respuesta], ignore_index=True)
                
                # Volver a escribir todo el bloque en Google Sheets
                conn.update(data=datos_actualizados)
                
                st.success("¡Muchas gracias! Tu respuesta se ha guardado de forma anónima.")
            except Exception as e:
                st.error(f"Error al guardar: {e}. Revisa que la hoja esté en modo 'Editor' para cualquiera con el enlace.")

# --- VISTA DEL PROFESOR (Resultados) ---
with pestaña_profesor:
    st.title("Resultados del Feedback en Directo")
    
    # Botón manual para actualizar los datos en la pantalla
    if st.button("🔄 Actualizar Gráficos"):
        st.rerun()
        
    try:
        # Leer datos de la nube (ttl=0 para evitar que use la caché vieja)
        df = conn.read(ttl=0)
        
        # Eliminar filas completamente vacías si las hubiera
        df = df.dropna(how="all")
        
        st.metric(label="Alumnos que han respondido", value=len(df))
        
        if not df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Ritmo acumulado")
                conteo_ritmo = df["Ritmo"].value_counts()
                st.bar_chart(conteo_ritmo)
                
            with col2:
                st.subheader("Nivel de Comprensión")
                # Asegurar que la columna sea numérica para la media
                df["Comprensión"] = pd.to_numeric(df["Comprensión"])
                promedio = df["Comprensión"].mean()
                st.metric(label="Media de la clase", value=f"{promedio:.1f} / 5")
                
            st.subheader("Comentarios de los alumnos")
            # Mostrar los comentarios que no estén vacíos
            for com in df["Comentarios"].dropna():
                if str(com).strip() != "" and str(com) != "nan":
                    st.chat_message("user").write(com)
        else:
            st.info("Aún no hay respuestas de alumnos en esta sesión.")
            
    except Exception as e:
        st.warning("Configurando la conexión o esperando datos de la hoja...")
