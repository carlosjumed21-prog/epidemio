import streamlit as st
import pandas as pd
import plotly.express as px

def app():
    st.title("📊 Cronología de Eventos Clínicos")
    st.markdown("Carga tu archivo Excel para visualizar la línea de tiempo.")

    # 1. Carga del archivo Excel
    archivo_subido = st.file_uploader("Selecciona tu archivo Excel", type=["xlsx"])

    if archivo_subido is not None:
        try:
            # Leemos el archivo
            xls = pd.ExcelFile(archivo_subido)
            lista_df = []
            
            for nombre_hoja in xls.sheet_names:
                df_temp = pd.read_excel(xls, sheet_name=nombre_hoja)
                df_temp['Paciente'] = nombre_hoja
                lista_df.append(df_temp)
            
            df = pd.concat(lista_df, ignore_index=True)
            
            # 2. LIMPIEZA DE FECHAS (Corrección del error 21-22/06/2026)
            # Convertimos a string primero
            df['Fecha_str'] = df['Fecha'].astype(str)
            
            # Si el formato contiene un rango (ej: "21-22/06/2026"), extraemos solo la parte del inicio
            # Esto toma el texto antes de un guion que no sea separador de fecha estándar
            df['Fecha_procesada'] = df['Fecha_str'].apply(lambda x: x.split('-')[0] if '-' in x.split('/')[0] else x)
            
            # Convertimos a formato datetime
            df['Fecha'] = pd.to_datetime(df['Fecha_procesada'], dayfirst=True, errors='coerce')
            
            # Eliminamos filas que no pudieron convertirse (datos basura)
            df = df.dropna(subset=['Fecha'])
            
            # 3. Gráfico
            st.success("Archivo procesado con éxito")
            
            fig = px.timeline(
                df, 
                x_start="Fecha", 
                x_end="Fecha", 
                y="Paciente", 
                color="Procedimientos",
                hover_data=['Dispositivos Invasivos', 'Cultivos / Fiebre / Antibióticos', 'Servicio', 'Cama'],
                title="Línea Cronológica de Pacientes"
            )
            
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)
            
            # 4. Tabla de datos
            with st.expander("Ver datos procesados"):
                st.dataframe(df.drop(columns=['Fecha_str', 'Fecha_procesada']))

        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")
            st.info("Asegúrate de que la columna 'Fecha' tenga un formato compatible (DD/MM/AAAA).")
    else:
        st.info("Por favor, carga un archivo Excel para comenzar.")

if __name__ == "__main__":
    app()
