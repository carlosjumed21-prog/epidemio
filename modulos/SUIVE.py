import streamlit as st
import pandas as pd
import re

st.header("📊 Módulo de Validación y Vigilancia Epidemiológica - SUIVE")
st.markdown("""
Cargue el archivo institucional de Excel del **SUIVE** para escanear automáticamente los padecimientos, 
la clave CIE-10 y la clasificación operativa de notificación.
""")

# Componente para cargar el archivo Excel del SUIVE
archivo_suive = st.file_uploader(
    "📁 Arrastre o seleccione el archivo Excel del SUIVE (Ej. ANEXO 1 - Formato_SUIVE_1 2026.xlsx)",
    type=["xlsx", "xls"]
)

if archivo_suive is not None:
    try:
        xls = pd.ExcelFile(archivo_suive)
        registros_totales = []
        
        def limpiar_texto_grupo(texto):
            # Elimina guiones y espacios generados por saltos de línea en celdas estrechas
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
                
                # Omitir cabeceras o notas al pie institucionales
                if idx < 19:
                    continue
                    
                if pd.notna(b):
                    b_str = " ".join(str(b).split())
                    if not any(w in b_str for w in ['Instrucciones', 'Unidad:', 'Localidad:', 'Institución:', 'Grupo', 'Nota:', 'Vo. Bo.', 'Los códigos']):
                        current_group = limpiar_texto_grupo(b_str)
                        
                if pd.notna(d):
                    d_str = " ".join(str(d).split())
                    if any(w in d_str for w in ['Diagnóstico', 'NOTIFICACIÓN', 'Nota:', 'Vo. Bo.', 'Número']):
                        continue
                        
                    # Detección de símbolos de notificación en el texto del diagnóstico
                    es_inmediata = 1 if '*' in d_str else 0
                    es_especial = 1 if '+' in d_str else 0
                    es_brote = 1 if '#' in d_str else 0
                    
                    epi = str(e).strip() if pd.notna(e) else ""
                    
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
            st.success(f"✅ Archivo procesado con éxito. Total de padecimientos detectados: **{len(df_suive)}**.")
            
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
                
            # 2. Aplicar filtro estricto por Tipo de Notificación y recortar columnas correspondientes
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
                # Si se selecciona "TODOS", omitimos 'Pestaña' y 'Grupo' pero dejamos las 3 columnas de notificación
                columnas_a_omitir = ['Pestaña', 'Grupo']
                df_filtrado = df_filtrado.drop(columns=[col for col in columnas_a_omitir if col in df_filtrado.columns])

            # Convertir 1 y 0 a texto vacío o marcas visuales limpias para que no se muestren los números
            df_visual = df_filtrado.copy()
            for col in ['Inmediata (*)', 'Vig. Especial (+)', 'Brote (#)']:
                if col in df_visual.columns:
                    df_visual[col] = df_visual[col].apply(lambda x: "✓" if x == 1 else "")

            def estilo_tabla(row):
                styles = [''] * len(row)
                # Evaluamos sobre el dataframe original numérico de respaldo
                orig_idx = row.name
                if 'Inmediata (*)' in df_filtrado.columns and df_suive.loc[orig_idx, 'Inmediata (*)'] == 1:
                    styles[df_filtrado.columns.get_loc('Inmediata (*)')] = 'background-color: rgba(239, 68, 68, 0.5); color: white; text-align: center; font-weight: bold;'
                if 'Vig. Especial (+)' in df_filtrado.columns and df_suive.loc[orig_idx, 'Vig. Especial (+)'] == 1:
                    styles[df_filtrado.columns.get_loc('Vig. Especial (+)')] = 'background-color: rgba(13, 148, 136, 0.5); color: white; text-align: center; font-weight: bold;'
                if 'Brote (#)' in df_filtrado.columns and df_suive.loc[orig_idx, 'Brote (#)'] == 1:
                    styles[df_filtrado.columns.get_loc('Brote (#)')] = 'background-color: rgba(249, 115, 22, 0.5); color: white; text-align: center; font-weight: bold;'
                return styles

            st.markdown(f"### 📋 Matriz de Padecimientos ({len(df_visual)} registros mostrados)")
            
            # Mostrar dataframe estilizado con texto limpio
            st.dataframe(
                df_visual.style.apply(estilo_tabla, axis=1),
                use_container_width=True,
                height=500
            )
            
            # Métricas rápidas globales
            col1, col2, col3 = st.columns(3)
            col1.metric("🚨 Total Inmediatas (*)", int(df_suive['Inmediata (*)'].sum()))
            col2.metric("📋 Total Vig. Especiales (+)", int(df_suive['Vig. Especial (+)'].sum()))
            col3.metric("⚠️ Total Brotes (#)", int(df_suive['Brote (#)'].sum()))
            
        else:
            st.warning("⚠️ No se pudieron extraer filas válidas de padecimientos. Verifique la estructura del archivo.")
            
    except Exception as e:
        st.error(f"❌ Error al procesar el archivo Excel: {e}")
else:
    st.info("💡 Por favor, cargue un archivo Excel del formato SUIVE en la parte superior para visualizar la matriz interactiva.")
