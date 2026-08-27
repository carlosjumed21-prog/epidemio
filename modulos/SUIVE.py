import streamlit as st
import pandas as pd
import re
import os
import requests

# --- CONFIGURACIÓN DE GOOGLE DRIVE ---
# Este es el ID exacto de tu archivo Excel dentro de la carpeta que compartiste.
FILE_ID_DRIVE = "1AJPgYoA71bqTwEV1M8VjN4s18dzTNUd5cXH96NzmPmE"

@st.cache_data(ttl=3600, show_spinner="Descargando SUIVE desde Google Drive...")
def obtener_archivo_desde_drive(file_id):
    """
    Descarga el archivo directamente desde Google Drive y lo guarda en la 
    memoria temporal del servidor. Se actualiza cada hora (ttl=3600).
    """
    # Construimos el enlace de descarga directa de Google Drive
    url_descarga = f"https://drive.google.com/uc?id={file_id}&export=download"
    ruta_temporal = "SUIVE_TEMP.xlsx"
    anio_detectado = "2026" # Año por defecto
    
    try:
        # Descargar el archivo
        respuesta = requests.get(url_descarga)
        respuesta.raise_for_status() # Verifica que la descarga fue exitosa
        
        # Guardarlo como un archivo local temporal en el servidor
        with open(ruta_temporal, "wb") as f:
            f.write(respuesta.content)
            
        # Extraer el año dinámicamente leyendo el contenido del Excel
        # (Buscamos en las primeras filas del documento)
        df_prueba = pd.read_excel(ruta_temporal, header=None, nrows=5)
        for fila in df_prueba.values:
            for celda in fila:
                match = re.search(r'(20\d{2})', str(celda))
                if match:
                    anio_detectado = match.group(1)
                    return ruta_temporal, anio_detectado
                    
        return ruta_temporal, anio_detectado
        
    except Exception as e:
        st.error(f"Error de conexión con Google Drive: {e}")
        return None, "2026"

# 1. Ejecutar la descarga o recuperar de la memoria caché
ruta_archivo, anio_suive = obtener_archivo_desde_drive(FILE_ID_DRIVE)

if ruta_archivo is not None and os.path.exists(ruta_archivo):
    st.session_state['suive_activo_path'] = ruta_archivo
    st.session_state['suive_anio'] = anio_suive

anio_activo = st.session_state.get('suive_anio', anio_suive)
path_actual = st.session_state.get('suive_activo_path', ruta_archivo)

# --- ESTILOS CSS DEFINITIVOS ---
st.markdown("""
    <style>
    .suive-container {
        background-color: #1e293b;
        border: 1px solid #334155;
        padding: 12px 16px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.15);
        text-align: center;
    }
    .suive-container p {
        color: #e2e8f0;
        font-size: 0.95rem;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .stDownloadButton button {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        border-radius: 6px !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        width: 100% !important;
        box-shadow: 0 3px 6px rgba(239, 68, 68, 0.3) !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stDownloadButton button:hover {
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 8px rgba(220, 38, 38, 0.4) !important;
        transform: translateY(-1px);
    }
    </style>
""", unsafe_allow_html=True)

# --- ENCABEZADO PRINCIPAL Y BLOQUE DE DESCARGA ---
col_head1, col_head2 = st.columns([1.6, 2.4], vertical_alignment="center")

with col_head1:
    st.header("📊 Módulo de Validación y Vigilancia Epidemiológica - SUIVE")
    st.markdown(f"### Formato Oficial: **SUIVE ACTUAL {anio_activo}**")

with col_head2:
    if path_actual and os.path.exists(path_actual):
        with open(path_actual, "rb") as file_btn:
            st.markdown('<div class="suive-container"><p>📥 ¿Necesitas el formato oficial vigente?</p>', unsafe_allow_html=True)
            st.download_button(
                label="👉 SI DESEA DESCARGAR EL ANEXO SUIVE 1 ACTUAL DE CLIC AQUÍ 📥",
                data=file_btn,
                file_name=f"Formato_SUIVE_{anio_activo}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Descargue el archivo Excel exacto que el sistema está analizando en este momento.",
                use_container_width=True
            )
            st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# --- PROCESAMIENTO DEL EXCEL DESCARGADO ---
if path_actual and os.path.exists(path_actual):
    try:
        xls = pd.ExcelFile(path_actual)
        registros_totales = []
        
        def limpiar_texto_grupo(texto):
            cleaned = re.sub(r'(\w+)-\s*(\w+)', r'\1\2', texto)
            return " ".join(cleaned.split())

        # Recorrido por cada pestaña del archivo
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet)
            current_group = "GENERAL"
            
            for idx in range(len(df)):
                row = df.iloc[idx]
                b = row.iloc[1]  
                d = row.iloc[3]  
                e = row.iloc[4]  
                
                if idx < 19:
                    continue
                    
                if pd.notna(b):
                    b_str = " ".join(str(b).split())
                    if not any(w in b_str for w in ['Instrucciones', 'Unidad:', 'Localidad:', 'Institución:', 'Grupo', 'Nota:', 'Vo. Bo.', 'Los códigos']):
                        current_group = limpiar_texto_grupo(b_str)
                        
                if pd.notna(d):
                    d_str = " ".join(str(d).split())
                    if any(w in d_str for w in ['Diagnóstico', 'NOTIFICACIÓN', 'Nota:', 'Vo. Bo.', 'Número', 'Los códigos', 'Secretaría de Salud']):
                        continue
                    
                    epi = str(e).strip() if pd.notna(e) else ""
                    if not epi or epi == 'nan':
                        continue
                        
                    es_inmediata = 1 if '*' in d_str else 0
                    es_especial = 1 if '+' in d_str else 0
                    es_brote = 1 if '#' in d_str else 0
                    
                    registros_totales.append({
                        'Pestaña': sheet,
                        'Grupo': current_group,
                        'Padecimiento': d_str,
                        'EPI Clave': epi,
                        'Inmediata (*)': es_inmediata,
                        'Vig. Especial (+)': es_especial,
                        'Brote (#)': es_brote
                    })
                    
        df_suive = pd.DataFrame(registros_totales)
        
        if not df_suive.empty:
            st.success(f"✅ Archivo obtenido desde Drive y sincronizado con éxito. Padecimientos detectados: **{len(df_suive)}**.")
            
            # --- FILTROS ---
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filtro_grupo = st.selectbox(
                    "Filtrar por Grupo Epidemiológico:", 
                    ["TODOS"] + sorted(df_suive['Grupo'].unique().tolist())
                )
            with col_f2:
                filtro_aviso = st.selectbox(
                    "Filtrar por Tipo de Notificación:", 
                    ["TODOS", "Inmediata (*)", "Vig. Especial (+)", "Brote (#)"]
                )
                
            df_filtrado = df_suive.copy()
            
            if filtro_grupo != "TODOS":
                df_filtrado = df_filtrado[df_filtrado['Grupo'] == filtro_grupo]
                
            if filtro_aviso == "Inmediata (*)":
                df_filtrado = df_filtrado[df_filtrado['Inmediata (*)'] == 1]
                df_filtrado = df_filtrado[['Padecimiento', 'EPI Clave', 'Inmediata (*)']]
            elif filtro_aviso == "Vig. Especial (+)":
                df_filtrado = df_filtrado[df_filtrado['Vig. Especial (+)'] == 1]
                df_filtrado = df_filtrado[['Padecimiento', 'EPI Clave', 'Vig. Especial (+)']]
            elif filtro_aviso == "Brote (#)":
                df_filtrado = df_filtrado[df_filtrado['Brote (#)'] == 1]
                df_filtrado = df_filtrado[['Padecimiento', 'EPI Clave', 'Brote (#)']]
            else:
                df_filtrado = df_filtrado.drop(columns=['Pestaña', 'Grupo'])

            df_filtrado = df_filtrado.dropna(how='all')

            df_visual = df_filtrado.copy()
            for col in ['Inmediata (*)', 'Vig. Especial (+)', 'Brote (#)']:
                if col in df_visual.columns:
                    df_visual[col] = df_visual[col].apply(lambda x: "✓" if x == 1 else "")

            def estilo_tabla(row):
                styles = [''] * len(row)
                orig_idx = row.name
                if orig_idx in df_suive.index:
                    if 'Inmediata (*)' in df_filtrado.columns and df_suive.loc[orig_idx, 'Inmediata (*)'] == 1:
                        styles[df_filtrado.columns.get_loc('Inmediata (*)')] = 'background-color: rgba(239, 68, 68, 0.5); color: white; text-align: center; font-weight: bold;'
                    if 'Vig. Especial (+)' in df_filtrado.columns and df_suive.loc[orig_idx, 'Vig. Especial (+)'] == 1:
                        styles[df_filtrado.columns.get_loc('Vig. Especial (+)')] = 'background-color: rgba(13, 148, 136, 0.5); color: white; text-align: center; font-weight: bold;'
                    if 'Brote (#)' in df_filtrado.columns and df_suive.loc[orig_idx, 'Brote (#)'] == 1:
                        styles[df_filtrado.columns.get_loc('Brote (#)')] = 'background-color: rgba(249, 115, 22, 0.5); color: white; text-align: center; font-weight: bold;'
                return styles

            st.divider()

            col1, col2, col3 = st.columns(3)
            col1.metric("🚨 Total Inmediatas (*)", int(df_suive['Inmediata (*)'].sum()))
            col2.metric("📋 Total Vig. Especiales (+)", int(df_suive['Vig. Especial (+)'].sum()))
            col3.metric("⚠️ Total Brotes (#)", int(df_suive['Brote (#)'].sum()))

            st.markdown(f"### 📋 Matriz de Padecimientos ({len(df_visual)} registros mostrados)")
            
            if not df_visual.empty:
                st.dataframe(df_visual.style.apply(estilo_tabla, axis=1), use_container_width=True, height=500)
            else:
                st.info("ℹ️ No hay registros que coincidan con los filtros.")
            
    except Exception as e:
        st.error(f"❌ Error al procesar el archivo Excel: {e}")
else:
    st.error("❌ No se pudo cargar el archivo desde Google Drive.")
