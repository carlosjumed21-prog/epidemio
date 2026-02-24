def limpiar_registro(reg):
    """Limpia y normaliza el registro para asegurar el match."""
    if pd.isna(reg): return None
    # Elimina cualquier carácter que no sea número y quita ceros a la izquierda
    reg_clean = re.sub(r'\D', '', str(reg))
    return reg_clean.lstrip('0')

def cargar_aislamientos_limpios():
    try:
        # 1. Carga con tipos de datos controlados
        df_ais = pd.read_csv(SHEET_URL_AISLAMIENTOS, skiprows=1, engine='python', dtype=str)
        df_ais.columns = [str(c).strip().upper() for c in df_ais.columns]
        
        cols = ["CAMA", "REGISTRO", "NOMBRE", "TIPO DE AISLAMIENTO", "FECHA DE TÉRMINO"]
        df_ais = df_ais[[c for c in cols if c in df_ais.columns]].copy()
        
        # 2. Limpieza de filas vacías y ruido
        df_ais = df_ais.dropna(subset=["REGISTRO"])
        ruido = ["1111", "PACIENTES", "TOTAL", "SUBTOTAL", "NOMBRE"]
        df_ais = df_ais[~df_ais["REGISTRO"].str.contains('|'.join(ruido), na=False, case=False)]
        
        # 3. Normalización del Registro para el cruce (Key)
        df_ais["REG_KEY"] = df_ais["REGISTRO"].apply(limpiar_registro)
        
        # 4. Filtrar solo los activos (donde FECHA DE TÉRMINO está vacío)
        df_ais = df_ais[df_ais["FECHA DE TÉRMINO"].isna() | (df_ais["FECHA DE TÉRMINO"].str.strip() == "")]
        
        # 5. Rellenado y consolidación de aislamientos por paciente
        df_ais["CAMA"] = df_ais["CAMA"].ffill()
        df_ais["NOMBRE"] = df_ais["NOMBRE"].ffill()
        
        # Agrupar por REG_KEY para no perder aislamientos múltiples (ej. Gotas + Contacto)
        df_ais["TIPO DE AISLAMIENTO"] = df_ais.groupby("REG_KEY")["TIPO DE AISLAMIENTO"].transform(
            lambda x: " / ".join(x.dropna().unique())
        )
        
        return df_ais.drop_duplicates("REG_KEY")
    except Exception as e:
        st.error(f"Error al cargar Google Sheets: {e}")
        return pd.DataFrame()

# --- DENTRO DE LA INTERFAZ (Donde procesas el HTML) ---
# Al crear df_ref_html, añade la normalización del registro:
if 'archivo_compartido' in st.session_state:
    # ... (tu código previo de extracción de tablas)
    df_ref_html = pd.DataFrame(datos_html)
    if not df_ref_html.empty:
        df_ref_html["REG_KEY"] = df_ref_html["REGISTRO"].apply(limpiar_registro)

    # --- EL MERGE OPTIMIZADO ---
    if 'df_ais_mapeado' not in st.session_state:
        df_base = cargar_aislamientos_limpios()
        if not df_base.empty:
            # Cruzamos por la llave normalizada REG_KEY
            df_f = pd.merge(df_base, df_ref_html, on="REG_KEY", how="left", suffixes=('_AIS', '_HTML'))
            
            # Prioridad: Si está en el HTML (Censo real de hoy), usamos esos datos. 
            # Si no, mantenemos lo del Excel de aislamientos.
            df_f["CAMA_FINAL"] = df_f["CAMA_HTML"].fillna(df_f["CAMA_AIS"])
            df_f["PACIENTE_FINAL"] = df_f["PACIENTE"].fillna(df_f["NOMBRE"])
            df_f["REGISTRO_FINAL"] = df_f["REGISTRO_HTML"].fillna(df_f["REGISTRO_AIS"])
            
            df_f["TIPO DE PRECAUCIONES"] = df_f["TIPO DE AISLAMIENTO"]
            df_f["INSUMO"] = "JABÓN/SANITAS"
            
            for c in ["SEXO", "EDAD", "FECHA DE INGRESO"]:
                df_f[c] = df_f[c].fillna("Pendiente")
            
            # Seleccionamos columnas finales
            st.session_state.df_ais_mapeado = df_f[[
                "CAMA_FINAL", "REGISTRO_FINAL", "PACIENTE_FINAL", 
                "SEXO", "EDAD", "FECHA DE INGRESO", 
                "TIPO DE PRECAUCIONES", "INSUMO"
            ]].rename(columns={
                "CAMA_FINAL": "CAMA", 
                "REGISTRO_FINAL": "REGISTRO", 
                "PACIENTE_FINAL": "PACIENTE"
            })
