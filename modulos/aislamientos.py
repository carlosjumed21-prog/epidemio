import streamlit as st

import pandas as pd

import numpy as np

import time



st.set_page_config(page_title="Control de Aislamientos", page_icon="🦠")

st.title("🦠 Control de Aislamientos Activos")



# URL de publicación

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmU8ibxYHge7Mq0bcdBz5oa7TPtWt6-3uxungBZlfHCM7oUzUy2TNL43tOmeHOzHebX-xGfvqFcxiy/pub?gid=1090111501&single=true&output=csv"



@st.cache_data(ttl=2)

def cargar_censo_total():

    # Forzar lectura fresca

    url_final = f"{SHEET_URL}&cachebust={time.time()}"

    

    # 1. Leemos el archivo. Skiprows=1 para saltar el título "AISLAMIENTOS"

    df = pd.read_csv(url_final, skiprows=1, engine='python', encoding='utf-8')

    

    # 2. Recorte manual de columnas B a J (Índices 1 al 9)

    df = df.iloc[:, 1:10]

    

    # 3. Normalizar encabezados (quitar espacios, saltos de línea y a mayúsculas)

    df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]

    

    # Definición de nombres de columnas para uso interno

    c_cama = "CAMA"

    c_nombre = "NOMBRE"

    c_tipo = "TIPO DE AISLAMIENTO"

    c_termino = "FECHA DE TÉRMINO"



    # --- LIMPIEZA DE DATOS ---

    # Convertimos todo a string y limpiamos espacios para no ignorar la última fila

    df = df.astype(str).apply(lambda x: x.str.strip())

    df = df.replace(['nan', 'None', 'none', 'NULL', '', ' '], np.nan)



    # 4. LÓGICA DE FILAS DOBLES

    # Rellenamos Cama y Nombre hacia abajo para no perder la relación en filas dobles

    df[c_cama] = df[c_cama].ffill()

    df[c_nombre] = df[c_nombre].ffill()



    def consolidar_evento(group):

        res = group.iloc[0].copy()

        # Combinar tipos de aislamiento

        tipos = group[c_tipo].dropna().unique()

        res[c_tipo] = " / ".join(tipos) if len(tipos) > 0 else np.nan

        # Rescatar datos de otras columnas que puedan estar en la fila de abajo

        for col in group.columns:

            if col not in [c_tipo, c_cama, c_nombre]:

                val_real = group[col].dropna()

                res[col] = val_real.iloc[0] if not val_real.empty else np.nan

        return res



    # Agrupamos para consolidar las filas dobles en una sola

    df = df.groupby([c_cama, c_nombre], as_index=False, sort=False).apply(consolidar_evento)



    # 5. FILTRO DE ACTIVOS (Celdas vacías en Fecha de Término)

    if c_termino in df.columns:

        df = df[df[c_termino].isna()]



    # Filtro final: que la cama no sea nula (elimina filas vacías del final del Excel)

    df = df[df[c_cama].notna()]

    

    return df



# --- INTERFAZ ---

try:

    if st.button("🔄 Actualizar Censo (Escanear hasta fila final)", use_container_width=True):

        st.cache_data.clear()

        st.rerun()



    df_final = cargar_censo_total()



    if not df_final.empty:

        # Buscador

        busqueda = st.text_input("🔍 Buscar por cama, nombre o microorganismo:")

        if busqueda:

            mask = df_final.apply(lambda r: r.astype(str).str.contains(busqueda, case=False).any(), axis=1)

            df_final = df_final[mask]



        st.dataframe(df_final, use_container_width=True, hide_index=True)

        

        st.success(f"📋 **{len(df_final)}** Aislamientos Activos detectados.")

        

        # Mostramos el último dato para confirmar que leyó la fila 50

        ultimo_p = df_final.iloc[-1]

        st.info(f"📍 Último registro detectado: Cama {ultimo_p['CAMA']} - {ultimo_p['NOMBRE']}")

        

    else:

        st.warning("⚠️ No se encontraron pacientes activos sin fecha de término.")



except Exception as e:

    st.error(f"Error al procesar el archivo: {e}")

    st.info("Asegúrate de que el Google Sheets esté publicado correctamente (Archivo > Compartir > Publicar en la web).")



Ayudame a generar un censo en formato tabla el cual ira en una hoja de sheets, la cual te pasare el link de pagina web, para que copies todo es esa hoja nueva.



deberas de autoajustar la celda acorde al texto. https://docs.google.com/spreadsheets/d/e/2PACX-1vSD2cPIZRxh-b5NyaVARl3Ioa5B0KeIqdLhtDkQ1nldthyu6TIT4KrWG5NWSNiUeY0XWiL1icDafU0P/pub?gid=0&single=true&output=csv

Gemini dijo
