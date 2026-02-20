import streamlit as st
import pandas as pd
import re
from io import BytesIO
from datetime import datetime, timedelta
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, Border, Side
from openpyxl.utils import get_column_letter

# --- CONFIGURACIÓN ---
SHEET_URL_AISLAMIENTOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8qN_ymtBcRCY2DcyEAANAzPPasVeYL6h0l4-AhuL2JYXpBOQ0e-mtrtoeSRvcnnl66HEh9aCJQwpx/pub?gid=0&single=true&output=csv"

# --- LÓGICA DE APOYO ---
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

def cargar_aislamientos_base():
    try:
        # Cargamos saltando la primera fila de título
        df_ais = pd.read_csv(SHEET_URL_AISLAMIENTOS, skiprows=1, engine='python')
        # Limpiar nombres de columnas
        df_ais.columns = [str(c).strip().upper() for c in df_ais.columns]
        # Seleccionar solo lo necesario para el empalme
        # Ajustamos nombres según tu Sheets (B=CAMA, C=REGISTRO, D=NOMBRE, E=TIPO DE AISLAMIENTO)
        cols_necesarias = ["REGISTRO", "TIPO DE AISLAMIENTO", "FECHA DE TÉRMINO"]
        df_ais = df_ais[[c for c in cols_necesarias if c in df_ais.columns]]
        # Filtrar solo los activos (Fecha de término vacía)
        col_venc = "FECHA DE TÉRMINO"
        if col_venc in df_ais.columns:
            df_ais = df_ais[df_ais[col_venc].isna() | (df_ais[col_venc].astype(str).str.strip() == "")]
        return df_ais
    except:
        return pd.DataFrame()

# --- INTERFAZ ---
st.title("📦 Censo de Insumos (Aislamientos)")

if 'archivo_compartido' not in st.session_state:
    st.info("👈 Por favor, sube el archivo HTML en el apartado de 'Configuración' de la izquierda.")
else:
    try:
        # 1. Extraer TODOS los pacientes del HTML para tener la base demográfica y camas reales
        tablas = pd.read_html(st.session_state['archivo_compartido'])
        df_html_raw = max(tablas, key=len)
        col0_str = df_html_raw.iloc[:, 0].fillna("").astype(str).str.upper()
        
        lista_html = []
        esp_actual = "SIN_ESPECIALIDAD"
        IGNORAR = ["PACIENTES", "TOTAL", "SUBTOTAL", "PÁGINA", "IMPRESIÓN", "1111"]

        for i, val in enumerate(col0_str):
            if "ESPECIALIDAD:" in val:
                esp_actual = val
                continue
            fila = [str(x).strip() for x in df_html_raw.iloc[i].values]
            if any(x in fila[0] for x in IGNORAR): continue
            
            # Validar que sea una fila de paciente (Registro en col 1)
            if len(fila[1]) >= 5 and any(char.isdigit() for char in fila[1]):
                lista_html.append({
                    "CAMA": fila[0], 
                    "REGISTRO": fila[1], 
                    "PACIENTE": fila[2], 
                    "SEXO": fila[3], 
                    "EDAD": "".join(re.findall(r'\d+', fila[4])), 
                    "FECHA DE INGRESO": fila[9]
                })
        
        df_html_total = pd.DataFrame(lista_html)

        # 2. Cargar datos de Aislamientos desde Google Sheets
        df_aislamientos = cargar_aislamientos_base()

        if df_aislamientos.empty:
            st.warning("⚠️ No se pudieron obtener datos de la tabla de Aislamientos.")
        else:
            # 3. EMPALME (Merge)
            # El REGISTRO es nuestra llave. Buscamos los datos del HTML para los pacientes en aislamiento.
            df_final_previa = pd.merge(
                df_aislamientos, 
                df_html_total, 
                on="REGISTRO", 
                how="inner" # Solo pacientes que estén en ambas listas
            )

            # 4. Ajustes finales de columnas
            df_final_previa["TIPO DE PRECAUCIONES"] = df_final_previa["TIPO DE AISLAMIENTO"]
            df_final_previa["INSUMO"] = "JABÓN/SANITAS"

            # Reordenar según tu requerimiento
            cols_vista = ["CAMA", "REGISTRO", "PACIENTE", "SEXO", "EDAD", "FECHA DE INGRESO", "TIPO DE PRECAUCIONES", "INSUMO"]
            df_final_previa = df_final_previa[cols_vista]

            st.subheader("👁️ Vista Previa de Insumos para Aislamientos")
            st.caption("Nota: La CAMA se actualizó automáticamente según el censo HTML del día.")
            st.table(df_final_previa)

            # --- BOTÓN GENERAR EXCEL ---
            if st.button("🚀 GENERAR EXCEL DE INSUMOS", use_container_width=True, type="primary"):
                hoy = datetime.now()
                venc = hoy + timedelta(days=7)
                output = BytesIO()
                thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    # En este caso, el reporte suele ser una sola hoja de Aislamientos
                    df_final_previa.to_excel(writer, index=False, sheet_name="Aislamientos", startrow=1)
                    ws = writer.sheets["Aislamientos"]
                    
                    # Encabezado
                    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(cols_vista))
                    cell_h = ws.cell(row=1, column=1, value=f"INSUMOS AISLAMIENTOS DEL {hoy.strftime('%d/%m/%Y')} AL {venc.strftime('%d/%m/%Y')}")
                    cell_h.alignment = Alignment(horizontal="center", vertical="center")
                    cell_h.font = Font(bold=True)

                    # Estilos y Autoajuste
                    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=len(cols_vista)):
                        for cell in row:
                            cell.border = thin_border
                            cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")

                    for i, _ in enumerate(cols_vista):
                        ws.column_dimensions[get_column_letter(i + 1)].width = 22

                st.success("✅ Reporte generado.")
                st.download_button(
                    label="💾 DESCARGAR REPORTE", 
                    data=output.getvalue(), 
                    file_name=f"Insumos_Aislamientos_{hoy.strftime('%d%m%Y')}.xlsx",
                    use_container_width=True
                )

    except Exception as e:
        st.error(f"Error al procesar: {e}")
