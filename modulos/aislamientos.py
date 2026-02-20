import streamlit as st
import pandas as pd

st.title("🦠 Control de Aislamientos (Tiempo Real)")

# Reemplaza este link con el tuyo (debe terminar en output=csv)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

def cargar_datos_sheets(url):
    # Agregamos una columna de caché para que no tarde en cargar siempre, 
    # pero se actualice con el botón de "Refrescar"
    return pd.read_csv(url)

with st.container(border=True):
    st.markdown("### 📋 Listado Maestro de Aislamientos")
    st.caption("Los datos se extraen directamente desde Google Sheets.")

    try:
        # Botón para forzar la actualización de datos
        if st.button("🔄 Refrescar Datos"):
            st.cache_data.clear()

        df_aislamientos = cargar_datos_sheets(SHEET_URL)

        # Buscador rápido
        busqueda = st.text_input("🔍 Buscar paciente o cama:", placeholder="Ej. 4210 o Juan Perez")
        
        if busqueda:
            # Filtra en todas las columnas
            mask = df_aislamientos.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
            df_mostrar = df_aislamientos[mask]
        else:
            df_mostrar = df_aislamientos

        # Visualización de la tabla
        st.dataframe(
            df_mostrar, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Fecha": st.column_config.DateColumn("Fecha de Registro"),
                "Estado": st.column_config.SelectboxColumn("Estatus", options=["Activo", "Alta", "Defunción"])
            }
        )

    except Exception as e:
        st.error("No se pudo conectar con Google Sheets. Verifica que el archivo esté publicado como CSV.")
        st.info("Asegúrate de que el enlace termine en `export?format=csv`.")

st.write("---")
st.info("💡 **Nota:** Cualquier cambio realizado en el Google Sheets se reflejará aquí al refrescar la página.")
