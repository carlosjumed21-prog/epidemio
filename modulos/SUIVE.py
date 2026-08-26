import streamlit as st
import pandas as pd
import re
import os
import gdown

st.header("📊 Módulo de Validación y Vigilancia Epidemiológica - SUIVE")

# URL pública de la carpeta de Google Drive provista
DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1Bdgn2B04cjV_RdQ7hnuJZuWHfS6FH9G6?usp=sharing"

@st.cache_data(ttl=3600)
def descargar_y_obtener_archivo_suive(folder_url):
    """
    Descarga el archivo más reciente de la carpeta pública de Google Drive
    y extrae automáticamente el año del nombre del archivo.
    """
    output_dir = "temp_suive"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Descarga la carpeta completa o el contenido público usando gdown
        gdown.download_folder(folder_url, output=output_dir, quiet=True, use_cookies=False)
        
        # Buscar archivos Excel descargados en el directorio
        archivos_encontrados = []
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file.lower().endswith(('.xlsx', '.xls')):
                    archivos_encontrados.append(os.path.join(root, file))
                    
        if not archivos_encontrados:
            return None, "2026" # Valor por defecto si no encuentra archivo inmediato
            
        # Seleccionar el archivo más reciente basado en la fecha de modificación
        archivo_mas_reciente = max(archivos_encontrados, key=os.path.getmtime)
        nombre_archivo = os.path.basename(archivo_mas_reciente)
        
        # Extraer el año del nombre del archivo mediante expresiones regulares (ej. 2026)
        match_anio = re.search(r'(20\d{2})', nombre_archivo)
        anio_detectado = match_anio.group(1) if match_anio else "2026"
        
        return archivo_mas_reciente, anio_detectado
        
    except Exception as e:
        return None, "2026"

# Ejecutar la carga automática en segundo plano
with st.spinner("🔄 Conectando con Google Drive y descargando el formato SUIVE más reciente..."):
    ruta_archivo, anio_suive = descargar_y_obtener_archivo_suive(DRIVE_FOLDER_URL)

# Mostrar la leyenda dinámica solicitada
st.markdown(f"### 📥 Formato Oficial: **SUIVE ACTUAL {anio_suive}**")
st.markdown("Carga automatizada y sincronizada directamente desde el repositorio institucional en la nube.")

if ruta_archivo is not None and os.path.exists(ruta_archivo):
    try:
        xls = pd.ExcelFile(ruta_archivo)
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
            st.success(f"✅ Archivo sincronizado con éxito. Total de padecimientos detectados: **{len(df_suive)}**.")
            
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
            st.warning("⚠️ No se pudieron extraer filas válidas de padecimientos. Verifique la estructura del archivo en Google Drive.")
            
    except Exception as e:
        st.error(f"❌ Error al procesar el archivo Excel descargado: {e}")
else:
    st.error("❌ No se pudo establecer conexión con la carpeta de Google Drive o no contiene archivos Excel válidos.")

# --- CÓDIGO QR DE ACCESO AL MÓDULO ---
st.divider()
st.subheader("📱 Código QR de Acceso al Módulo SUIVE")
url_app = "https://epidemio-ztqx4t3swz3bqkxxubp4tn.streamlit.app/SUIVE"
st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={url_app}", width=200)
