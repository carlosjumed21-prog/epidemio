def consolidar_paciente(group):
    # 1. Si no tiene tipo de aislamiento en ninguna fila, ignoramos el grupo
    if group[col_tipo].dropna().empty: 
        return None
            
    res = group.iloc[0].copy()
    
    # 2. Unimos tipos y protectores (evitando duplicados)
    tipos = group[col_tipo].dropna().unique()
    res[col_tipo] = " / ".join(tipos) if len(tipos) > 0 else "SIN ESPECIFICAR"
    
    prots = group[col_protector].dropna().unique()
    res[col_protector] = " / ".join(prots) if len(prots) > 0 else "VACIO"
    
    # --- CORRECCIÓN AQUÍ ---
    # Un paciente está ACTIVO si al menos UNA de sus filas NO tiene fecha de término (es NaN)
    # Solo será FINALIZADO si TODAS las filas del grupo tienen una fecha de término.
    esta_activo = group[col_termino].isna().any() 
    
    res[col_termino] = "ACTIVO" if esta_activo else "FINALIZADO"
    
    # Para los días, tomamos el máximo de las filas activas si es posible
    if esta_activo:
        # Calculamos días solo de las filas que no han terminado
        dias_activos = group[group[col_termino].isna()][col_dias]
        res[col_dias] = dias_activos.max() if not dias_activos.empty else group[col_dias].max()
    else:
        res[col_dias] = group[col_dias].max()
        
    return res
