import streamlit as st
import pandas as pd
import re
from io import BytesIO
from datetime import datetime, timedelta
from openpyxl.styles import Alignment, Font, Border, Side, PatternFill
from openpyxl.utils import get_column_letter

# --- CONFIGURACIÓN ---
SHEET_URL_AISLAMIENTOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

SERVICIOS_INSUMOS_FILTRO = [
    "HEMATOLOGIA", "HEMATOLOGIA PEDIATRICA", "ONCOLOGIA PEDIATRICA",
    "NEONATOLOGIA", "INFECTOLOGIA PEDIATRICA", "U.C.I.N.",
    "U.T.I.P.", "TERAPIA POSQUIRURGICA", "UNIDAD DE QUEMADOS",
    "ONCOLOGIA MEDICA", "UCIA"
]

# --- FUNCIONES DE FORMATO Y LÓGICA ---

def aplicar_formato_oficial(writer, sheet_name, df, servicio_nombre):
    """Aplica encabezados azules, vigencia de 7 días, bordes, NOM-045 y Firma."""
    ws = writer.sheets[sheet_name]
    hoy = datetime.now()
    vencimiento = hoy + timedelta(days=7)
    f_hoy = hoy.strftime("%d/%m/%Y")
    f_venc = vencimiento.strftime("%d/%m/%Y")
    
    # Estilos de celda
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # 1. Título de Vigencia (Fila 1)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=8)
    titulo = f"{servicio_nombre} DEL {f_hoy} AL {f_venc} (PARA LOS 3 TURNOS Y FINES DE SEMANA)"
    cell_h = ws.cell(row=1, column=1, value=titulo)
    cell_h.alignment = center_align
    cell_h.font = Font(bold=True, size=11)

    # 2. Encabezados de Columna (Fila 2)
    for col_num, value in enumerate(df.columns, 1):
        cell = ws.cell(row=2, column=col_num, value=value)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align
        cell.border = border

    # 3. Cuerpo de datos y Bordes
    for row in ws.iter_rows(min_row=3, max_row=len(df)+2, min_col=1, max_col=8):
        for cell in row:
            cell.border = border
            cell.alignment = center_align
    
    # Autoajuste de columnas
    for i in range(1, 9):
        ws.column_dimensions[get_column_letter(i)].width = 20

    # 4. Pie de Página (NOM y Autorizó)
    lr = ws.max_row
    ws.merge_cells(start_row=lr + 1, start_column=1, end_row=lr + 1, end_column=8)
    leyenda = "Comentario: de acuerdo con la Norma Oficial Mexicana NOM-045-SSA2-2005, Para la vigilancia epidemiológica, prevención y control de las infecciones nosocomiales. NINGUN RECIPIENTE QUE CONTENGA EL INSUMO DEBERÁ SER RELLENADO O REUTILIZADO."
    cell_nom = ws.cell(row=lr + 1, column=1, value=leyenda)
    cell_nom.alignment = center_align
    cell_nom.font = Font(size=9, italic=True)
    ws.row_dimensions[lr + 1].height = 50

    ws.merge_cells(start_row=lr + 2, start_column=1, end_row=lr + 2, end_column=8)
    cell_auth = ws.cell(row=lr + 2, column=1, value="AUTORIZÓ: DRA. BRENDA CASTILLO MATUS")
    cell_auth.alignment = center_align
    cell_auth.font = Font(bold=True)

def obtener_especialidad_real(cama, esp_html):
    c = str(cama).strip().upper()
    esp_html_clean = esp_html.replace("ESPECIALIDAD:", "").replace("&NBSP;", "").strip().upper()
    if c.startswith("55"): return "U.C.I.N."
    if c.startswith("45"): return "NEONATOLOGIA" 
    if c.startswith("56"): return "U.T.I.P."
    if c.startswith("85"): return "UNIDAD DE QUEMADOS"
    if c.startswith("73"): return "UCIA"
    if c.isdigit() and 7401 <= int(c) <= 7409: return "TERAPIA POSQUIRURGICA"
    return esp_html_clean

def cargar_aislamientos_limpios():
    try:
        df_ais = pd.read_csv(SHEET_URL_AISLAMIENTOS, skiprows=1, engine='python')
        df_ais.columns = [str(c).strip().upper() for c in df_ais.columns]
        cols = ["CAMA", "REGISTRO", "NOMBRE", "TIPO DE AISLAMIENTO", "FECHA DE TÉRMINO"]
        df_ais = df_ais[[c for c in cols if c in df_ais.columns]]
        df_ais = df_ais.replace(['nan', 'None', 'none', 'NAN', ' '], pd.NA)
        df_ais = df_ais[df_ais["FECHA DE TÉRMINO"].isna()]
        df_ais["CAMA"] = df_ais["CAMA"].ffill()
        df_ais["NOMBRE"] = df_ais["NOMBRE"].ffill()
        df_ais["TIPO DE AISLAMIENTO"] = df_ais.groupby(["CAMA", "NOMBRE"])["TIPO DE AISLAMIENTO"].transform(
            lambda x: " / ".join(x.dropna().astype(str).unique())
        )
        return df_ais.drop_duplicates(["CAMA", "NOMBRE"]).dropna(subset=["REGISTRO"])
    except:
        return pd.DataFrame()

# --- INTERFAZ ---
st.title("📦 Censo de Insumos")

if 'archivo_compartido' not in st.session_state:
    st.info("👈 Sube el archivo HTML en 'Configuración' para iniciar.")
else:
    try:
        tablas = pd.read_html(st.session_state['archivo_compartido'])
        df_html_raw = max(tablas, key=len)
        col0_str = df_html_raw.iloc[:, 0].fillna("").astype(str).str.upper()
        
        datos_html = []
        pacs_11_esp = []
        esp_actual = ""

        for i, val in enumerate(col0_str):
            if "ESPECIALIDAD:" in val:
                esp_actual = val; continue
            fila = [str(x).strip() for x in df_html_raw.iloc[i].values]
            if len(fila) > 1 and len(fila[1]) >= 5 and any(char.isdigit() for char in fila[1]):
                esp_real = obtener_especialidad_real(fila[0], esp_actual)
                pac_data = {
                    "CAMA_HTML": fila[0], "REGISTRO": fila[1], "PACIENTE": fila[2],
                    "SEXO": fila[3], "EDAD": "".join(re.findall(r'\d+', fila[4])),
                    "FECHA DE INGRESO": fila[9], "ESP_REAL": esp_real
                }
                datos_html.append(pac_data)
                if esp_real in SERVICIOS_INSUMOS_FILTRO:
                    pacs_11_esp.append(pac_data)

        df_mapeo_html = pd.DataFrame(datos_html)

        # SECCIÓN A: 11 ESPECIALIDADES
        st.header("📋 INSUMOS: ESPECIALIDADES")
        if pacs_11_esp:
            df_11 = pd.DataFrame(pacs_11_esp)
            for serv in sorted(df_11["ESP_REAL"].unique()):
                with st.expander(f"🔍 Vista Previa: {serv}"):
                    df_v = df_11[df_11["ESP_REAL"] == serv].copy()
                    df_v["TIPO DE PRECAUCIONES"] = "ESTÁNDAR"
                    df_v["INSUMO"] = "JABÓN/SANITAS"
                    st.table(df_v[["CAMA_HTML", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]])
        
        st.markdown("<br><hr><br>", unsafe_allow_html=True)

        # SECCIÓN B: AISLAMIENTOS
        st.header("🦠 INSUMOS: AISLAMIENTOS")
        
        if 'df_ais_mapeado' not in st.session_state:
            df_base = cargar_aislamientos_limpios()
            if not df_base.empty:
                df_f = pd.merge(df_base, df_mapeo_html, on="REGISTRO", how="left")
                df_f["CAMA"] = df_f["CAMA_HTML"].fillna(df_f["CAMA"])
                df_f["PACIENTE"] = df_f["PACIENTE"].fillna(df_f["NOMBRE"])
                df_f["TIPO DE PRECAUCIONES"] = df_f["TIPO DE AISLAMIENTO"]
                df_f["INSUMO"] = "JABÓN/SANITAS"
                for c in ["SEXO", "EDAD", "FECHA DE INGRESO"]:
                    df_f[c] = df_f[c].fillna("Pendiente")
                st.session_state.df_ais_mapeado = df_f[["CAMA", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]]
            else:
                st.session_state.df_ais_mapeado = pd.DataFrame()

        if not st.session_state.df_ais_mapeado.empty:
            df_actual = st.session_state.df_ais_mapeado
            mask_pendientes = df_actual.astype(str).apply(lambda x: x.str.contains('Pendiente')).any(axis=1)
            df_pendientes = df_actual[mask_pendientes].copy()

            if not df_pendientes.empty:
                st.subheader("⚠️ Pacientes por completar (Edición)")
                edited_pendientes = st.data_editor(
                    df_pendientes.style.apply(lambda x: ['background-color: #FFF9C4' for _ in x], axis=1),
                    use_container_width=True, hide_index=True, key="editor_pendientes"
                )
                if not edited_pendientes.equals(df_pendientes):
                    st.session_state.df_ais_mapeado.update(edited_pendientes)
                    st.rerun()

            st.subheader("📋 Tabla Oficial de Insumos (Aislamientos)")
            st.table(st.session_state.df_ais_mapeado)

            # --- GENERACIÓN DE EXCEL TOTAL CON FORMATO ---
            if st.button("🚀 GENERAR EXCEL TOTAL", use_container_width=True, type="primary"):
                hoy_f = datetime.now().strftime('%d%m%Y')
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    # 1. Hoja Aislamientos
                    df_ais_final = st.session_state.df_ais_mapeado
                    df_ais_final.to_excel(writer, index=False, sheet_name="AISLAMIENTOS", startrow=1)
                    aplicar_formato_oficial(writer, "AISLAMIENTOS", df_ais_final, "INSUMOS AISLAMIENTOS")
                    
                    # 2. Hojas Especialidades
                    if pacs_11_esp:
                        for serv in sorted(df_11["ESP_REAL"].unique()):
                            df_s = df_11[df_11["ESP_REAL"] == serv].copy()
                            df_s["INSUMO"] = "JABÓN/SANITAS"
                            df_s["TIPO DE PRECAUCIONES"] = "ESTÁNDAR"
                            df_s = df_s[["CAMA_HTML", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]]
                            df_s.columns = ["CAMA", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]
                            nombre_hoja = serv[:30].replace("/", "-")
                            df_s.to_excel(writer, index=False, sheet_name=nombre_hoja, startrow=1)
                            aplicar_formato_oficial(writer, nombre_hoja, df_s, f"INSUMOS {serv}")
                
                st.success("✅ Reporte con metadatos y firmas generado.")
                st.download_button("💾 DESCARGAR REPORTE", output.getvalue(), f"Insumos_Epidemio_{hoy_f}.xlsx", use_container_width=True)
        else:
            st.info("No hay aislamientos activos registrados.")

    except Exception as e:
        st.error(f"Error: {e}")
