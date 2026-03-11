def enviar_a_google_sheets(df):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            service_account_info = st.secrets["connections"]["gsheets"]
        else:
            service_account_info = st.secrets["connections.gsheets"]
            
        creds = Credentials.from_service_account_info(service_account_info, scopes=scope)
        client = gspread.authorize(creds)
        sh = client.open_by_key(DESTINATION_SHEET_ID)
        worksheet = sh.get_worksheet(0) 
        
        # 1. Limpiar TODA la hoja antes de enviar
        worksheet.clear()
        
        # 2. Convertir DataFrame a lista de listas (asegurando que los datos son strings/números simples)
        # Esto evita errores de serialización de fechas de pandas
        df_envio = df.copy()
        for col in df_envio.columns:
            df_envio[col] = df_envio[col].astype(str)
            
        datos = [df_envio.columns.values.tolist()] + df_envio.values.tolist()
        
        # 3. Actualización forzada
        worksheet.update('A1', datos)
        return True
    except Exception as e:
        st.error(f"Error de conexión/escritura: {e}")
        return False

def cargar_aislamientos():
    # Carga desde origen
    df = pd.read_csv(SHEET_URL_READ, skiprows=1, engine='python', encoding='utf-8')
    df = df.iloc[:, 1:10] 
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    col_cama = df.columns[0]
    col_nombre = df.columns[1]
    col_tipo = df.columns[2]
    col_protector = df.columns[3]
    col_inicio = df.columns[5]    # Columna G
    col_dias = df.columns[6]      # Columna H
    col_termino = df.columns[7]   # Columna I

    # Rellenar combinadas
    df[col_cama] = df[col_cama].replace(['nan', 'None', ''], np.nan).ffill()
    df[col_nombre] = df[col_nombre].replace(['nan', 'None', ''], np.nan).ffill()

    def consolidar(group):
        res = group.iloc[0].copy()
        nulos = ['nan', 'None', 'none', '', 'NULL', 'NAN']
        
        tipos = [t for t in group[col_tipo].unique() if str(t).strip() not in nulos]
        res[col_tipo] = " / ".join(tipos) if tipos else "SIN ESPECIFICAR"
        
        prots = [p for p in group[col_protector].unique() if str(p).strip() not in nulos]
        res[col_protector] = " / ".join(prots) if prots else "VACIO"
        
        res[col_inicio] = next((i for i in group[col_inicio].values if str(i).strip() not in nulos), "VACIO")
        res[col_termino] = next((f for f in group[col_termino].values if str(f).strip() not in nulos), "VACIO")
        return res

    df = df.groupby([col_cama, col_nombre], as_index=False, sort=False).apply(consolidar)
    df = df[df[col_termino] == "VACIO"]

    # CÁLCULO DE DÍAS (Columna H)
    def calcular_dias(fecha_str):
        if str(fecha_str).strip() in ['VACIO', 'nan', '']: return 0
        try:
            # Forzamos la limpieza del string de fecha
            limpia = str(fecha_str).split(' ')[0]
            fecha_inicio = pd.to_datetime(limpia, dayfirst=True, errors='coerce')
            if pd.isna(fecha_inicio): return "Error"
            
            hoy = datetime.now()
            dias = (hoy - fecha_inicio).days + 1
            return dias if dias >= 0 else 0
        except:
            return 0

    df[col_dias] = df[col_inicio].apply(calcular_dias)
    
    # Quitar columna de término para el censo final
    df = df.drop(columns=[col_termino])
    df = df[df[col_cama].notna()].sort_values(by=col_cama)
    return df
