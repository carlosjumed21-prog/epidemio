# --- 3. NAVEGACIÓN Y ESTRUCTURA DE PÁGINAS ---
pg = st.navigation([
    st.Page(
        "modulos/censo_diario.py", 
        title="Censo Epidemiológico", 
        icon="📋", 
        default=True
    ),
    st.Page(
        "modulos/filtrado_pacientes.py", 
        title="Filtrado de Pacientes", 
        icon="🔍"
    ),
    st.Page(
        "modulos/hojadiaria.py", 
        title="Hoja Diaria Piso", 
        icon="📝" 
    ),
    st.Page(
        "modulos/insumos.py", 
        title="Censo de Insumos", 
        icon="📦"
    ),
    st.Page(
        "modulos/aislamientos.py", 
        title="Aislamientos", 
        icon="🦠"
    ),
    st.Page(
        "modulos/piso.py", 
        title="Seguimiento de Piso", 
        icon="🏥"
    ),
    st.Page(
        "modulos/vigilancia_piso.py", 
        title="Vigilancia Activa de Piso", 
        icon="🛡️" 
    ),
    st.Page(
        "modulos/estadisticas_iaas.py", 
        title="Estadísticas IAAS", 
        icon="📊"
    ),
    st.Page(
        "modulos/impresion_excel.py",  # <--- NUEVO MÓDULO
        title="Gestor de Impresión", 
        icon="🖨️"
    ),
])
