# --- 5. CONSOLIDACIÓN MODIFICADA ---
    def consolidar_paciente(group):
        # 1. Ignorar si el grupo no tiene información de tipo de aislamiento
        if group[col_tipo].dropna().empty: 
            return None
            
        res = group.iloc[0].copy()
        
        # 2. LÓGICA DE ACTIVACIÓN (Tu nueva condición)
        # Contamos cuántas filas tienen fecha de término (no son nulas)
        filas_con_fecha_termino = group[col_termino].notna().sum()
        total_filas_en_grupo = len(group)

        # Condición: Si TODAS las filas del paciente tienen fecha de término, se acabó.
        # Si hay al menos una fila SIN fecha de término, sigue ACTIVO.
        if filas_con_fecha_termino == total_filas_en_grupo:
            res[col_termino] = "FINALIZADO"
        else:
            res[col_termino] = "ACTIVO"
        
        # 3. Unir los textos de las filas agrupadas (Tipos y Protectores)
        tipos = group[col_tipo].dropna().unique()
        res[col_tipo] = " / ".join(tipos) if len(tipos) > 0 else "SIN ESPECIFICAR"
        
        prots = group[col_protector].dropna().unique()
        res[col_protector] = " / ".join(prots) if len(prots) > 0 else "VACIO"
        
        # 4. Días (el máximo de las filas agrupadas)
        res[col_dias] = group[col_dias].max()
        
        return res

    # Aplicar la agrupación
    df_consolidado = df.groupby([col_cama, col_nombre], as_index=False, sort=False).apply(consolidar_paciente)
    
    # Limpieza de nulos generados por el apply
    df_consolidado = df_consolidado.reset_index(drop=True)
    df_consolidado = df_consolidado.dropna(subset=[col_cama])

    # 6. FILTRO FINAL
    # Ahora sí, el registro 18 debería aparecer porque una de sus filas está vacía (ACTIVO)
    df_final = df_consolidado[df_consolidado[col_termino] == "ACTIVO"].copy()
