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
            # Leemos todas las hojas del Excel
            # Se asume que cada hoja es un paciente diferente
            xls = pd.ExcelFile(archivo_subido)
            
            lista_df = []
            for nombre_hoja in xls.sheet_names:
                df_temp = pd.read_excel(xls, sheet_name=nombre_hoja)
                df_temp['Paciente'] = nombre_hoja  # Usamos el nombre de la hoja como ID del paciente
                lista_df.append(df_temp)
            
            df = pd.concat(lista_df, ignore_index=True)
            
            # 2. Asegurar formato de fecha
            # Asegúrate de que tu columna se llame exactamente "Fecha"
            df['Fecha'] = pd.to_datetime(df['Fecha'])
            
            # 3. Gráfico de línea de tiempo
            st.success("Archivo cargado con éxito")
            
            fig = px.timeline(
                df, 
                x_start="Fecha", 
                x_end="Fecha", 
                y="Paciente", 
                color="Procedimientos", # Asegúrate de tener esta columna
                hover_data=['Dispositivos Invasivos', 'Cultivos / Fiebre / Antibióticos'],
                title="Línea Cronológica de Pacientes"
            )
            
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)
            
            # 4. Tabla de datos
            with st.expander("Ver datos brutos"):
                st.dataframe(df)

        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")
            st.info("Asegúrate de que tus columnas se llamen: Fecha, Servicio, Cama, Dispositivos Invasivos, Procedimientos, Cultivos / Fiebre / Antibióticos, Origen")
    else:
        st.info("Por favor, carga un archivo Excel para comenzar.")

if __name__ == "__main__":
    app()
