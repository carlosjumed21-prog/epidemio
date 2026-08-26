import streamlit as st
import pandas as pd
import re

st.header("📊 Módulo de Validación y Vigilancia Epidemiológica - SUIVE")
st.markdown("""
Cargue el archivo institucional de Excel del **SUIVE** para escanear automáticamente los padecimientos, 
grupos de afectación, CIE-10 y la clasificación operativa de notificación (**Inmediata, Especial y Brote**).
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
                        current_group = b_str
                        
                if pd.notna(d):
                    d_str = " ".join(str(d).split())
                    if any(w in d_str for w in ['Diagnóstico', 'NOTIFICACIÓN', 'Nota:', 'Vo. Bo.', 'Número']):
                        continue
                        
                    # Detección de símbolos de notificación en el texto del diagnóstico
                    es_inmediata = 1 if '*' in d_str else 0
                    es_especial = 1 if '+' in d_str else 0
                    es_brote = 1 if '#' in d_str else 0
                    
                    # Limpieza básica del texto para aislar CIE-10 si es posible
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
            st.success(f"✅ Archivo procesado con éxito. Se detectaron **{len(df_suive)}** registros de padecimientos.")
            
            # Filtros interactivos en barra lateral o superior
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filtro_grupo = st.selectbox("Filtrar por Grupo Epidemiológico:", ["TODOS"] + sorted(df_suive['Grupo'].unique().tolist()))
            with col_f2:
                filtro_aviso = st.selectbox("Filtrar por Tipo de Notificación:", ["TODOS", "Inmediata (*)", "Vig. Especial (+)", "Brote (#)"])
                
            df_filtrado = df_suive.copy()
            if filtro_grupo != "TODOS":
                df_filtrado = df_filtrado[df_filtrado['Grupo'] == filtro_grupo]
            if filtro_aviso == "Inmediata (*)":
                df_filtrado = df_filtrado[df_filtrado['Inmediata (*)'] == 1]
            elif filtro_aviso == "Vig. Especial (+)":
                df_filtrado = df_filtrado[df_filtrado['Vig. Especial (+)'] == 1]
            elif filtro_aviso == "Brote (#)":
                df_filtrado = df_filtrado[df_filtrado['Brote (#)'] == 1]

            # Función para aplicar colorimetría y transparencia (50%) acorde a la imagen de referencia
            def color_notificacion(val, color_hex):
                if val == 1:
                    # Color de fondo con 50% de opacidad aproximada en formato RGBA o Hex con canal alfa
                    return f'background-color: {color_hex}80; color: white; font-weight: bold; text-align: center;'
                return 'text-align: center; color: #555;'

            def estilo_tabla(row):
                styles = [''] * len(row)
                # Índices de columnas de interés
                # 'Inmediata (*)', 'Vig. Especial (+)', 'Brote (#)'
                if row['Inmediata (*)'] == 1:
                    styles[df_filtrado.columns.get_loc('Inmediata (*)')] = 'background-color: rgba(239, 68, 68, 0.5); color: white; text-align: center; font-weight: bold;' # Rojo
                if row['Vig. Especial (+)'] == 1:
                    styles[df_filtrado.columns.get_loc('Vig. Especial (+)')] = 'background-color: rgba(13, 148, 136, 0.5); color: white; text-align: center; font-weight: bold;' # Turquesa
                if row['Brote (#)'] == 1:
                    styles[df_filtrado.columns.get_loc('Brote (#)')] = 'background-color: rgba(249, 115, 22, 0.5); color: white; text-align: center; font-weight: bold;' # Naranja
                return styles

            st.markdown("### 📋 Matriz de Padecimientos y Criterios de Notificación")
            st.caption("Los campos con cumplimiento normativo se resaltan con el código de colores institucional y 50% de transparencia.")
            
            # Mostrar dataframe estilizado
            st.dataframe(
                df_filtrado.style.apply(estilo_tabla, axis=1),
                use_container_width=True,
                height=500
            )
            
            # Métricas rápidas
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
