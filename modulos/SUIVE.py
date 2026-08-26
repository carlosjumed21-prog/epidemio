import streamlit as st
import pandas as pd
import re
import os
import glob

@st.cache_data(ttl=3600)
def obtener_archivo_suive():
    """
    Busca de forma inteligente el archivo SUIVE oficial en el repositorio 
    y extrae el año dinámicamente de su nombre.
    """
    patrones = [
        "ANEXO 1 - Formato_SUIVE_1*.xlsx",
        "modulos/ANEXO 1 - Formato_SUIVE_1*.xlsx",
        "*SUIVE*.xlsx",
        "*suive*.xlsx",
        "*.xlsx"
    ]
    
    archivo_encontrado = None
    for patron in patrones:
        coincidencias = glob.glob(patron)
        if not coincidencias:
            coincidencias = glob.glob(f"**/{patron}", recursive=True)
            
        if coincidencias:
            archivo_encontrado = coincidencias[0]
            break
            
    if archivo_encontrado and os.path.exists(archivo_encontrado):
        match_anio = re.search(r'(20\d{2})', archivo_encontrado)
        anio_detectado = match_anio.group(1) if match_anio else "2026"
        return archivo_encontrado, anio_detectado
        
    return None, "2026"

# Ejecutar carga inicial de la ruta
ruta_archivo, anio_suive = obtener_archivo_suive()

if ruta_archivo is not None and os.path.exists(ruta_archivo):
    st.session_state['suive_activo_path'] = ruta_archivo
    st.session_state['suive_anio'] = anio_suive

anio_activo = st.session_state.get('suive_anio', anio_suive)
path_actual = st.session_state.get('suive_activo_path', ruta_archivo)

# --- ENCABEZADO ORIGINAL CON TÍTULO Y BOTÓN ROJO INTEGRADO ---
col_head1, col_head2 = st.columns([2.2, 1.8], vertical_alignment="bottom")

with col_head1:
    st.header("📊 Módulo de Validación y Vigilancia Epidemiológica - SUIVE")
    st.markdown(f"### Formato Oficial: **SUIVE ACTUAL {anio_activo}**")

with col_head2:
    if path_actual and os.path.exists(path_actual):
        # Estilo CSS personalizado para el botón rojo llamativo
        st.markdown("""
            <style>
            div.stButton > button {
                background-color: #dc2626 !important;
                color: white !important;
                font-weight: bold !important;
                border-radius: 6px !important;
                border: none !important;
                padding: 0.4rem 0.8rem !important;
                width: 100% !important;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            div.stButton > button:hover {
                background-color: #b91c1c !important;
                color: white !important;
            }
            </style>
        """, unsafe_allow_html=True)

        with open(path_actual, "rb") as file_btn:
            st.download_button(
                label="📥 Descargar ANEXO SUIVE 1",
                data=file_btn,
                file_name=os.path.basename(path_actual),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Descargue el archivo Excel exacto que el sistema está analizando en este momento.",
                use_container_width=True
            )

st.divider()

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
                b = row.iloc[1]  # Columna B: Grupo
                d = row.iloc[3]  # Columna C/D: Diagnóstico y CIE-10
                e = row.iloc[4]  # Columna D/E: EPI Clave
                
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
            st.success(f"✅ Archivo analizado y sincronizado en memoria con éxito. Total de padecimientos detectados: **{len(df_suive)}**.")
            
            # --- FILTROS EN LA PARTE SUPERIOR ---
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
            
            # 1. Aplicar filtro por Grupo
            if filtro_grupo != "TODOS":
                df_filtrado = df_filtrado[df_filtrado['Grupo'] == filtro_grupo]
                
            # 2. Aplicar filtro estricto por Tipo de Notificación y recortar columnas
            if filtro_aviso == "Inmediata (*)":
                df_filtrado = df_filtrado[df_filtrado['Inmediata (*)'] == 1]
                columnas_a_mantener = ['Padecimiento', 'EPI Clave', 'Inmediata (*)']
                df_filtrado = df_filtrado[[col for col in columnas_a_mantener if col in df_filtrado.columns]]
            elif filtro_aviso == "Vig. Especial (+)":
                df_filtrado = df_filtrado[df_filtrado['Vig. Especial (+)'] == 1]
                columnas_a_mantener = ['Padecimiento', 'EPI Clave', 'Vig. Especial (+)']
                df_filtrado = df_filtrado[[col for col in columnas_a_mantener if col in df_filtrado.columns]]
            elif filtro_aviso == "Brote (#)":
                df_filtrado = df_filtrado[df_filtrado['Brote (#)'] == 1]
                columnas_a_mantener = ['Padecimiento', 'EPI Clave', 'Brote (#)']
                df_filtrado = df_filtrado[[col for col in columnas_a_mantener if col in df_filtrado.columns]]
            else:
                columnas_a_omitir = ['Pestaña', 'Grupo']
                df_filtrado = df_filtrado.drop(columns=[col for col in columnas_a_omitir if col in df_filtrado.columns])

            df_filtrado = df_filtrado.dropna(how='all')

            # Convertir 1 y 0 a marca limpia de verificación
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

            # --- MÉTRICAS INDIVIDUALES ARRIBA DE LA VISTA PREVIA ---
            col1, col2, col3 = st.columns(3)
            col1.metric("🚨 Total Inmediatas (*)", int(df_suive['Inmediata (*)'].sum()))
            col2.metric("📋 Total Vig. Especiales (+)", int(df_suive['Vig. Especial (+)'].sum()))
            col3.metric("⚠️ Total Brotes (#)", int(df_suive['Brote (#)'].sum()))

            st.markdown(f"### 📋 Matriz de Padecimientos ({len(df_visual)} registros mostrados)")
            
            if not df_visual.empty:
                st.dataframe(
                    df_visual.style.apply(estilo_tabla, axis=1),
                    use_container_width=True,
                    height=500
                )
            else:
                st.info("ℹ️ No hay registros que coincidan con los filtros seleccionados.")
            
        else:
            st.warning("⚠️ No se pudieron extraer filas válidas de padecimientos.")
            
    except Exception as e:
        st.error(f"❌ Error al procesar el archivo Excel: {e}")
else:
    st.error("❌ No se encontró el archivo Excel del SUIVE en el repositorio.")
