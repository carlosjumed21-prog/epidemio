def conectar_piso_activo():
    try:
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # Abrir archivos
        ss_origen = client.open_by_key("1yKgI1CxWGxIFSRNaG8WoTTmZ__mEkkfhNqcL-2T_ePM")
        ss_salida = client.open_by_key("1GWFWY1PyfUERC9S0QYvOsugpvrIPQiRS7vyCval9ZTc")
        
        # --- VALIDACIÓN DE HOJAS ---
        # Origen: Datos Limpios (Suele ser la segunda hoja del censo)
        h_datos_limpios = ss_origen.get_worksheet(1) 
        
        # Salida: Plantilla y Seguimiento
        h_plantilla = ss_salida.get_worksheet(0) # Hoja 1 (Debe existir)
        
        # Intentar obtener la Hoja 2, si no existe, la creamos
        try:
            h_seguimiento = ss_salida.get_worksheet(1)
        except gspread.exceptions.WorksheetNotFound:
            # Crea la hoja "Seguimiento" si no existe
            h_seguimiento = ss_salida.add_worksheet(title="Seguimiento", rows="1000", cols="40")
            st.info("💡 Se creó automáticamente la hoja 'Seguimiento' en tu archivo.")
            
        return ss_salida, h_plantilla, h_datos_limpios, h_seguimiento
    except Exception as e:
        st.error(f"⚠️ Error detallado: {e}")
        return None, None, None, None
