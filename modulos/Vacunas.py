import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

st.set_page_config(page_title="Esquemas de Vacunación 2026", page_icon="💉", layout="wide")

# --- 1. CONEXIÓN A GOOGLE SHEETS (BASE DE DATOS AUTOMÁTICA) ---
@st.cache_data(ttl=3600)  # Se actualiza cada hora para no saturar la conexión
def cargar_matrices():
    # ID de tu documento público consolidado
    sheet_id = "1xsRlV-Rf4wxvRUTxrcQqZCOO-sYIBZCv9lCvAkgv7_s"
    
    # Exportamos todo el documento como un Excel a la memoria
    url_excel = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    
    # Leemos cada pestaña por su índice (0=primera, 1=segunda, 2=tercera)
    # Según tu orden: 0: biologicos, 1: comorbilidades, 2: Esquema base
    df_cat = pd.read_excel(url_excel, sheet_name=0)
    df_comor = pd.read_excel(url_excel, sheet_name=1)
    df_esquema = pd.read_excel(url_excel, sheet_name=2)
    
    return df_cat, df_comor, df_esquema

# Ejecutar la carga de datos
try:
    df_biologicos, df_riesgos, df_esquema = cargar_matrices()
except Exception as e:
    st.error(f"⚠️ Error al conectar con Google Sheets. Detalles: {e}")
    st.stop()

# --- 2. ENTRADA DE DATOS DEL PACIENTE ---
st.title("💉 Esquemas de Vacunación 2026")
st.caption("Evaluación etaria y perfil de vacunación epidemiológica (Motor conectado a Google Sheets ☁️).")
st.divider()

col_form1, col_form2 = st.columns([1, 1])

with col_form1:
    fecha_nacimiento = st.date_input(
        "📅 Fecha de nacimiento:",
        value=None,
        min_value=date(1900, 1, 1),
        max_value=date.today(),
        format="DD/MM/YYYY"
    )

with col_form2:
    sexo = st.radio("⚧ Sexo:", options=["Hombre", "Mujer"], index=None, horizontal=True)

if not fecha_nacimiento or not sexo:
    st.info("👋 **Ingresa la fecha de nacimiento y selecciona el sexo** del paciente para calcular automáticamente el esquema.")
    st.stop()

# --- 3. CÁLCULO DE EDAD EXACTA ---
hoy = date.today()
dias_vida = (hoy - fecha_nacimiento).days
edad_delta = relativedelta(hoy, fecha_nacimiento)

anios, meses, dias = edad_delta.years, edad_delta.months, edad_delta.days
total_meses = (anios * 12) + meses
es_mujer = (sexo == "Mujer")

partes_grandes = []
if anios > 0: partes_grandes.append(f"{anios} año{'s' if anios != 1 else ''}")
if meses > 0: partes_grandes.append(f"{meses} mes{'es' if meses != 1 else ''}")
if dias > 0 or not partes_grandes: partes_grandes.append(f"{dias} día{'s' if dias != 1 else ''}")
edad_texto_grande = " / ".join(partes_grandes)

# --- 4. CONDICIONALES DE SALUD Y COMORBILIDADES ---
esta_embarazada = False
es_personal_salud = False
asiste_guarderia = False
factores_seleccionados = []

col_cond1, col_cond2 = st.columns([1, 1])

with col_cond1:
    if es_mujer and anios >= 10:
        esta_embarazada = st.checkbox("🤰 ¿Está embarazada?")
    if anios <= 4:
        asiste_guarderia = st.checkbox("🧸 ¿Asiste a guardería o centro de cuidado?")

with col_cond2:
    if anios >= 18:
        es_personal_salud = st.checkbox("🩺 ¿Es personal de salud?")

# Selector dinámico extraído directamente de la Pestaña 2 (Comorbilidades)
if 'Variable_Riesgo' in df_riesgos.columns:
    lista_comorbilidades = df_riesgos['Variable_Riesgo'].dropna().unique().tolist()
    factores_seleccionados = st.multiselect(
        "⚠️ Selecciona factores de riesgo o comorbilidades (si aplican):",
        options=lista_comorbilidades,
        help="Modificará el esquema base agregando refuerzos o biológicos."
    )
else:
    st.error("No se encontró la columna 'Variable_Riesgo' en la pestaña de comorbilidades.")

# --- 5. CLASIFICACIÓN CLÍNICA Y DISPLAY (Mismo diseño UI) ---
if dias_vida <= 28: tipo_paciente, icono = ("Recién nacida", "👶") if es_mujer else ("Recién nacido", "👶")
elif anios < 2: tipo_paciente, icono = "Lactante", "🍼"
elif 2 <= anios <= 5: tipo_paciente, icono = "Preescolar", "🧸"
elif 6 <= anios <= 11: tipo_paciente, icono = ("Escolar (Niña)", "👧") if es_mujer else ("Escolar (Niño)", "👦")
elif 12 <= anios < 18: tipo_paciente, icono = ("Adolescente", "👧") if es_mujer else ("Adolescente", "👦")
elif 18 <= anios < 60: tipo_paciente, icono = ("Mujer adulta", "👩") if es_mujer else ("Hombre adulto", "👨")
else: tipo_paciente, icono = ("Adulta mayor", "👵") if es_mujer else ("Adulto mayor", "👴")

color_fondo, color_borde, color_texto, badge_bg = ("#FCE4EC", "#D81B60", "#880E4F", "#C2185B") if es_mujer else ("#E3F2FD", "#1976D2", "#0D47A1", "#1565C0")

st.markdown("### 🏷️ Perfil Detectado")
condiciones_tags = []
if esta_embarazada: condiciones_tags.append("<strong style='color:#C2185B;'>Embarazo 🤰</strong>")
if es_personal_salud: condiciones_tags.append("<strong style='color:#0277BD;'>Personal de Salud 🩺</strong>")
if factores_seleccionados: condiciones_tags.append("<strong style='color:#E65100;'>Alto Riesgo ⚠️</strong>")

extra_info = " &nbsp;|&nbsp; " + " &nbsp;|&nbsp; ".join(condiciones_tags) if condiciones_tags else ""

tarjeta_html = (
    f'<div style="background-color:{color_fondo};border-left:8px solid {color_borde};border-radius:8px;padding:16px 20px;margin-bottom:25px;">'
    f'<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">'
    f'<div><span style="font-size:1.45rem;font-weight:700;color:{color_texto};">{icono} {tipo_paciente}</span>'
    f'<div style="font-size:0.95rem;color:#37474F;margin-top:4px;">'
    f'<strong>Sexo:</strong> {sexo} &nbsp;|&nbsp; <strong>Nacimiento:</strong> {fecha_nacimiento.strftime("%d/%m/%Y")}{extra_info}'
    f'</div></div>'
    f'<div style="background-color:{badge_bg};color:#FFFFFF;padding:8px 20px;border-radius:24px;font-size:1.15rem;font-weight:800;">'
    f'Edad: {edad_texto_grande}</div></div></div>'
)
st.markdown(tarjeta_html, unsafe_allow_html=True)

# --- 6. MOTOR DE REGLAS (FILTRADO DE MATRICES) ---
st.subheader("📋 Biológicos Recomendados (Motor Activo)")

# 6.1 Filtrar Esquema Base (Pestaña 3) por Edad
esquema_aplicable = df_esquema[
    (df_esquema['Edad_Minima_Dias'] <= dias_vida) & 
    (df_esquema['Edad_Maxima_Dias'] >= dias_vida)
].copy()

# 6.2 Filtrar por Sexo
if es_mujer:
    esquema_aplicable = esquema_aplicable[esquema_aplicable['Aplica_Mujer'] == True]
else:
    esquema_aplicable = esquema_aplicable[esquema_aplicable['Aplica_Hombre'] == True]

# 6.3 Filtros de Condiciones Especiales
condiciones_cumplidas = ["NINGUNA"]
if esta_embarazada:
    condiciones_cumplidas.extend(["EMBARAZO", "EMBARAZO_20_SDG", "EMBARAZO_32_36_SDG"])
if asiste_guarderia:
    condiciones_cumplidas.append("ASISTE_GUARDERIA")

if fecha_nacimiento >= date(2020, 7, 1):
    condiciones_cumplidas.append("NACIDOS_DESPUES_JULIO_2020")
else:
    condiciones_cumplidas.append("NACIDOS_ANTES_JULIO_2020")

esquema_aplicable = esquema_aplicable[
    esquema_aplicable['Condicion_Especial'].isin(condiciones_cumplidas) |
    (esquema_aplicable['Condicion_Especial'] == "SIN_ESQUEMA_PREVIO") 
]

# Si está embarazada, eliminar vacunas atenuadas por seguridad absoluta
if esta_embarazada:
    esquema_aplicable = esquema_aplicable[~esquema_aplicable['Biologico'].isin(['SR', 'SRP', 'VAR'])]

# 6.4 Incorporar Comorbilidades (Pestaña 2)
vacunas_riesgo = []
if factores_seleccionados:
    for factor in factores_seleccionados:
        reglas_riesgo = df_riesgos[
            (df_riesgos['Variable_Riesgo'] == factor) &
            (df_riesgos['Edad_Minima_Anios'] <= anios) &
            (df_riesgos['Edad_Maxima_Anios'] >= anios)
        ]
        for _, regla in reglas_riesgo.iterrows():
            vacunas_riesgo.append({
                "Biologico": regla['Biologico_Afectado'],
                "Dosis_Num": regla['Detalle_Esquema'],
                "Edad_Recomendada_Texto": f"Riesgo detectado: {factor}",
                "Origen": "Riesgo"
            })

if vacunas_riesgo:
    df_vacunas_riesgo = pd.DataFrame(vacunas_riesgo)
    esquema_aplicable['Origen'] = "Base"
    esquema_consolidado = pd.concat([esquema_aplicable, df_vacunas_riesgo], ignore_index=True)
    esquema_consolidado = esquema_consolidado.drop_duplicates(subset=['Biologico'])
else:
    esquema_aplicable['Origen'] = "Base"
    esquema_consolidado = esquema_aplicable

# --- 7. RENDERIZADO VISUAL ---
COLORES_VACUNAS = {
    "BCG": "#6A1B9A", "HEPB": "#E65100", "HEXA": "#0277BD", 
    "RV1": "#2E7D32", "VCN20": "#00838F", "INFL": "#AD1457", 
    "COVID": "#1B5E20", "SRP": "#E65100", "DPT": "#5D4037", 
    "VAR": "#4A148C", "HEPA": "#E65100", "VPH": "#F57F17", 
    "TD": "#3949AB", "SR": "#D81B60", "TDPA": "#2E7D32", "VSR": "#004D40"
}

if esquema_consolidado.empty:
    st.success("✅ **Esquema al día.** No se detectan vacunas programadas en el esquema base para esta edad exacta sin otros factores de riesgo.")
else:
    for _, row in esquema_consolidado.iterrows():
        bio_id = row['Biologico']
        
        # Buscar el nombre oficial en el catálogo (Pestaña 1)
        nombre_oficial = df_biologicos.loc[df_biologicos['ID_Biologico'] == bio_id, 'Nombre_Oficial'].values
        nombre_display = nombre_oficial[0] if len(nombre_oficial) > 0 else bio_id
        
        color_tema = COLORES_VACUNAS.get(bio_id, "#455A64")
        
        with st.container(border=True):
            col_v1, col_v2 = st.columns([3, 2])
            with col_v1:
                st.markdown(f"<h4 style='color:{color_tema};margin:0;'>{nombre_display}</h4>", unsafe_allow_html=True)
                st.markdown(f"<span style='color:#37474F;font-weight:500;font-size:1.1rem;'>{row['Dosis_Num']}</span>", unsafe_allow_html=True)
            with col_v2:
                if row['Origen'] == "Riesgo":
                    badge_html = f"<span style='background-color:#FFF3E0;color:#E65100;padding:6px 12px;border-radius:12px;font-size:0.85rem;font-weight:700;'>⚠️ {row['Edad_Recomendada_Texto']}</span>"
                else:
                    badge_html = f"<span style='background-color:#E3F2FD;color:#0D47A1;padding:6px 12px;border-radius:12px;font-size:0.85rem;font-weight:700;'>✅ Etapa: {row['Edad_Recomendada_Texto']}</span>"
                
                st.markdown(f"<div style='text-align:right; margin-top:10px;'>{badge_html}</div>", unsafe_allow_html=True)
