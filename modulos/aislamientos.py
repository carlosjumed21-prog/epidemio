# ... (todo el código anterior de carga y limpieza se mantiene igual)

    # --- 5. CONSOLIDACIÓN (LÓGICA MODIFICADA) ---
    def consolidar_paciente(group):
        # Si el grupo está totalmente vacío en tipos de aislamiento, ignorar
        if group[col_tipo].dropna().empty: 
            return None
            
        res = group.iloc[0].copy()
        
        # 1. Aplicamos tu nueva condición de término:
        # Contamos cuántas filas tienen dato en la columna 'término' (no son nulas)
        filas_con_termino = group[col_termino].notna().sum()
        total_filas_grupo = len(group)

        # CONDICIÓN: 
        # Si TODAS las filas tienen fecha de término -> FINALIZADO (No se contará después)
        # Si al menos una NO tiene fecha (está vacía) -> ACTIVO
        if filas_con_termino == total_filas_grupo:
            res[col_termino] = "FINALIZADO"
        else:
            res[col_termino] = "ACTIVO"
        
        # 2. Unimos tipos y protectores para el resumen
        tipos = group[col_tipo].dropna().unique()
        res[col_tipo] = " / ".join(tipos) if len(tipos) > 0 else "SIN ESPECIFICAR"
        
        prots = group[col_protector].dropna().unique()
        res[col_protector] = " / ".join(prots) if len(prots) > 0 else "VACIO"
        
        # 3. Tomamos el máximo de días registrados
        res[col_dias] = group[col_dias].max()
        
        return res

    # Agrupar y aplicar la nueva lógica
    df_consolidado = df.groupby([col_cama, col_nombre], as_index=False, sort=False).apply(consolidar_paciente)
    
    # Limpiar nulos del groupby
    df_consolidado = df_consolidado.reset_index(drop=True)
    df_consolidado = df_consolidado.dropna(subset=[col_cama])

    # 6. FILTRO FINAL
    # Aquí es donde se descartan los "NO aislamiento" (los que quedaron como FINALIZADO)
    df_final = df_consolidado[df_consolidado[col_termino] == "ACTIVO"].copy()
    
    if col_termino in df_final.columns:
        df_final = df_final.drop(columns=[col_termino])
    
    df_final[col_dias] = pd.to_numeric(df_final[col_dias], errors='coerce').fillna(0).astype(int)
    
    return df_final.sort_values(by=col_cama)

# ... (el resto de la interfaz de Streamlit se mantiene igual)
