import streamlit as st
import pandas as pd
import plotly.express as px

def app():
    st.title("📊 Línea de Tiempo de Eventos Clínicos")
    
    archivo_subido = st.file_uploader("Carga tu archivo Excel", type=["xlsx"])

    if archivo_subido is not None:
        try:
            xls = pd.ExcelFile(archivo_subido)
            lista_df = []
            
            for nombre_hoja in xls.sheet_names:
                df_temp = pd.read_excel(xls, sheet_name=nombre_hoja)
                df_temp['Paciente'] = nombre_hoja
                lista_df.append(df_temp)
            
            df = pd.concat(lista_df, ignore_index=True)
            
            # --- LIMPIEZA DE FECHAS PARA INICIO Y FIN ---
            # Asegúrate de que en tu Excel existan las columnas 'Fecha_Inicio' y 'Fecha_Fin'
            for col in ['Fecha_Inicio', 'Fecha_Fin']:
                df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
            
            # Eliminamos filas sin fechas válidas
            df = df.dropna(subset=['Fecha_Inicio', 'Fecha_Fin'])
            
            # --- GRÁFICO DE LÍNEA DE TIEMPO CON DURACIÓN ---
            fig = px.timeline(
                df, 
                x_start="Fecha_Inicio", 
                x_end="Fecha_Fin", 
                y="Paciente", 
                color="Procedimientos", # La categoría de evento
                hover_data=['Dispositivos Invasivos', 'Cultivos / Fiebre / Antibióticos', 'Servicio'],
                title="Duración de Intervenciones y Estancia"
            )
            
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error: {e}")
            st.info("Asegúrate de que tu archivo tenga las columnas: 'Fecha_Inicio' y 'Fecha_Fin'.")

if __name__ == "__main__":
    app()
