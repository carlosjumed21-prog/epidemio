import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

st.set_page_config(page_title="Esquemas de Vacunación 2026", page_icon="💉", layout="wide")

# --- 1. CONEXIÓN A GOOGLE SHEETS ---
@st.cache_data(ttl=3600)
def cargar_matrices():
    sheet_id = "1xsRlV-Rf4wxvRUTxrcQqZCOO-sYIBZCv9lCvAkgv7_s"
    url_excel = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    
    df_cat = pd.read_excel(url_excel, sheet_name=0)
    df_comor = pd.read_excel(url_excel, sheet_name=1)
    df_esquema = pd.read_excel(url_excel, sheet_name=2)
    return df_cat, df_comor, df_esquema

try:
    df_biologicos, df_riesgos, df_esquema = cargar_matrices()
except Exception as e:
    st.error(f"⚠️ Error al conectar con Google Sheets. Detalles: {e}")
    st.stop()

# Diccionario para mostrar nombres limpios en la interfaz
MAPEO_RIESGOS = {
    "VIH_SIDA": "VIH / SIDA",
    "INMUNOSUPRESION": "Inmunosupresión (Primaria o Adquirida)",
    "DIABETES_MELLITUS": "Diabetes Mellitus",
    "INSUFICIENCIA_RENAL": "Insuficiencia Renal (Incluye Diálisis)",
    "HEPATOPATIA_CRONICA": "Hepatopatía Crónica",
    "CARDIOPATIA": "Cardiopatía (Aguda o Crónica)",
    "HIPERTENSION_ARTERIAL": "Hipertensión Arterial Esencial",
    "NEUMOPATIA_CRONICA": "Neumopatía Crónica (EPOC / Asma)",
    "OBESIDAD_MORBIDA": "Obesidad Mórbida",
    "DISCAPACIDAD_NEURO_MOTORA": "Discapacidad Neuromotora",
    "CONSUMO_SALICILATOS": "Consumo Prolongado de Salicilatos",
    "PROTOCOLO_VIOLACION_SEXUAL": "Protocolo de Violación Sexual",
    "ASPLENIA": "Asplenia (Anatómica o Funcional)",
    "FISTULA_LCR": "Fístula de LCR",
    "IMPLANTE_COCLEAR": "Implante Coclear"
}

# --- 2. ENTRADA DE DATOS DEL PACIENTE ---
st.title("💉 Esquemas de Vacunación 2026")
st.divider()

col_form1, col_form2 = st.columns([1, 1])
with col_form1:
    fecha_nacimiento = st.date_input("📅 Fecha de nacimiento:", value=None, min_value=date(1900, 1, 1), max_value=date.today(), format="DD/MM/YYYY")
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

# --- 4. CONDICIONALES DE SALUD CONGRUENTES ---
esta_embarazada = False
es_personal_salud = False
asiste_guarderia = False
factores_seleccionados = []

col_cond1, col_cond2 = st.columns([1, 1])

with col_cond1:
    # Congruencia: Embarazo solo en mujeres >= 10 años
    if es_mujer and anios >= 10:
        esta_embarazada = st.checkbox("🤰 ¿Está embarazada?")
    if anios <= 4:
        asiste_guarderia = st.checkbox("🧸 ¿Asiste a guardería o centro de cuidado?")

with col_cond2:
    # Personal de salud asume mayoría de edad o estudiantes avanzados
    if anios >= 18:
        es_personal_salud = st.checkbox("🩺 ¿Es personal de salud?")

# Filtro de comorbilidades según la edad actual
if 'Variable_Riesgo' in df_riesgos.columns:
    riesgos_validos_edad = df_riesgos[(df_riesgos['Edad_Minima_Anios'] <= anios) & (df_riesgos['Edad_Maxima_Anios'] >= anios)]
    opciones_crudas = riesgos_validos_edad['Variable_Riesgo'].dropna().unique().tolist()
    
    # Traducir a etiquetas amigables
    opciones_ui = [MAPEO_RIESGOS.get(r, r) for r in opciones_crudas]
    
    seleccion_ui = st.multiselect("⚠️ Selecciona factores de riesgo o comorbilidades (si aplican):", options=opciones_ui)
    
    # Revertir a la clave original para que Pandas pueda buscar
    factores_seleccionados = [clave for clave, valor in MAPEO_RIESGOS.items() if valor in seleccion_ui]

# --- 5. PERFIL Y TABLAS VISUALES (HTML ORIGINAL) ---
st.markdown("### 🏷️ Perfil Detectado y Esquema Histórico")

# Lógica original de colores para tablas HTML
C_INACTIVO = "#FBFBFB"
if anios < 10:
    act_bcg = dias_vida >= 0
    act_hepb = dias_vida >= 0
    act_m2 = total_meses >= 2
    act_m4 = total_meses >= 4
    act_m6 = total_meses >= 6
    act_m12 = total_meses >= 12
    act_m18 = total_meses >= 18
    act_m48 = total_meses >= 48
    act_m59 = total_meses >= 59
    
    tabla_pediatrica_html = f"""
    <table style="width:100%;border-collapse:separate;border-spacing:4px;font-family:'Segoe UI',sans-serif;margin-top:10px;margin-bottom:20px;">
    <thead>
    <tr><th colspan="7" style="color:#881337;background-color:#FCE4EC;font-size:1.2rem;font-weight:800;text-align:center;padding:8px;border-radius:4px;">Panorama de Vacunación (0 a 9 años) - Coloreado indica dosis que ya debería tener</th></tr>
    </thead>
    <tbody>
    <tr>
    <td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:6px;border-radius:3px;">Nacimiento</td>
    <td colspan="2" style="background-color:{'#D9D2E9' if act_bcg else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:6px;border-radius:3px;">BCG</td>
    <td colspan="4" style="background-color:{'#F9CB9C' if act_hepb else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:6px;border-radius:3px;">Anti hepatitis B</td>
    </tr>
    <tr>
    <td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:6px;border-radius:3px;">2 meses</td>
    <td colspan="2" style="background-color:{'#CFE2F3' if act_m2 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:6px;border-radius:3px;">Hexavalente acelular</td>
    <td colspan="2" style="background-color:{'#D9EAD3' if act_m2 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:6px;border-radius:3px;">Anti rotavirus</td>
    <td colspan="2" style="background-color:{'#E7F3FE' if act_m2 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:6px;border-radius:3px;">Anti neumocócica 20v</td>
    </tr>
    <tr>
    <td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:6px;border-radius:3px;">12 meses</td>
    <td colspan="2" style="background-color:{'#FFF2CC' if act_m12 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:6px;border-radius:3px;">SRP (1ª dosis)</td>
    <td colspan="2" style="background-color:{'#E7F3FE' if act_m12 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:6px;border-radius:3px;">Anti neumocócica 20v</td>
    <td colspan="2" style="background-color:{'#E1BEE7' if act_m12 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:6px;border-radius:3px;">Anti varicela (Si aplica)</td>
    </tr>
    <tr>
    <td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:6px;border-radius:3px;">18 meses</td>
    <td colspan="2" style="background-color:{'#CFE2F3' if act_m18 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:6px;border-radius:3px;">Hexavalente acelular</td>
    <td colspan="2" style="background-color:{'#FFF2CC' if act_m18 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:6px;border-radius:3px;">SRP (2ª dosis)</td>
    <td colspan="2" style="background-color:{'#FFE0B2' if act_m18 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:6px;border-radius:3px;">Anti hepatitis A</td>
    </tr>
    <tr>
    <td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:6px;border-radius:3px;">4 años</td>
    <td colspan="6" style="background-color:{'#FFE082' if act_m48 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:6px;border-radius:3px;">DPT (Refuerzo)</td>
    </tr>
    </tbody>
    </table>
    """
    st.markdown(tabla_pediatrica_html, unsafe_allow_html=True)

if anios >= 10:
    st.warning("⚠️ **Nota Clínica:** Para este grupo de edad, se asume que el esquema básico de la infancia está completo. Sin embargo, es vital interrogar al paciente y solicitar la Cartilla Nacional de Salud para identificar e iniciar esquemas rezagados.")

# --- 6. MOTOR DE REGLAS (PANDAS) ---
st.subheader("📋 Biológicos Correspondientes a su Edad Actual")

esquema_aplicable = df_esquema[
    (df_esquema['Edad_Minima_Dias'] <= dias_vida) & 
    (df_esquema['Edad_Maxima_Dias'] >= dias_vida)
].copy()

if es_mujer:
    esquema_aplicable = esquema_aplicable[esquema_aplicable['Aplica_Mujer'] == True]
else:
    esquema_aplicable = esquema_aplicable[esquema_aplicable['Aplica_Hombre'] == True]

condiciones_cumplidas = ["NINGUNA"]
if esta_embarazada: condiciones_cumplidas.extend(["EMBARAZO", "EMBARAZO_20_SDG", "EMBARAZO_32_36_SDG"])
if asiste_guarderia: condiciones_cumplidas.append("ASISTE_GUARDERIA")
if fecha_nacimiento >= date(2020, 7, 1): condiciones_cumplidas.append("NACIDOS_DESPUES_JULIO_2020")
else: condiciones_cumplidas.append("NACIDOS_ANTES_JULIO_2020")

esquema_aplicable = esquema_aplicable[
    esquema_aplicable['Condicion_Especial'].isin(condiciones_cumplidas) |
    (esquema_aplicable['Condicion_Especial'] == "SIN_ESQUEMA_PREVIO") 
]

if esta_embarazada:
    esquema_aplicable = esquema_aplicable[~esquema_aplicable['Biologico'].isin(['SR', 'SRP', 'VAR'])]

vacunas_riesgo = []
if factores_seleccionados:
    for factor in factores_seleccionados:
        reglas_riesgo = df_riesgos[(df_riesgos['Variable_Riesgo'] == factor) & (df_riesgos['Edad_Minima_Anios'] <= anios) & (df_riesgos['Edad_Maxima_Anios'] >= anios)]
        for _, regla in reglas_riesgo.iterrows():
            vacunas_riesgo.append({
                "Biologico": regla['Biologico_Afectado'],
                "Dosis_Num": regla['Detalle_Esquema'],
                "Edad_Recomendada_Texto": f"Riesgo: {MAPEO_RIESGOS.get(factor, factor)}",
                "Edad_Minima_Dias": 0, "Edad_Maxima_Dias": 0, "Origen": "Riesgo"
            })

if vacunas_riesgo:
    df_vacunas_riesgo = pd.DataFrame(vacunas_riesgo)
    esquema_aplicable['Origen'] = "Base"
    esquema_consolidado = pd.concat([esquema_aplicable, df_vacunas_riesgo], ignore_index=True).drop_duplicates(subset=['Biologico'])
else:
    esquema_aplicable['Origen'] = "Base"
    esquema_consolidado = esquema_aplicable

# --- 7. RENDERIZADO VISUAL DETALLADO ---
COLORES_VACUNAS = {"BCG": "#6A1B9A", "HEPB": "#E65100", "HEXA": "#0277BD", "RV1": "#2E7D32", "VCN20": "#00838F", "INFL": "#AD1457", "COVID": "#1B5E20", "SRP": "#E65100", "DPT": "#5D4037", "VAR": "#4A148C", "HEPA": "#E65100", "VPH": "#F57F17", "TD": "#3949AB", "SR": "#D81B60", "TDPA": "#2E7D32", "VSR": "#004D40"}

# Diccionario auxiliar visual para las etiquetas de simultaneidad y rangos de texto
INFO_EXTRA = {
    "BCG": {"min": "Al nacer", "max": "< 5 años", "simul": "Hepatitis B, Hexavalente, VCN20, Rotavirus, Influenza"},
    "HEXA": {"min": "6 semanas", "max": "< 5 años", "simul": "Influenza, Rotavirus, Neumococo, Hepatitis A"},
    "RV1": {"min": "6 semanas", "max": "7 meses 29 días", "simul": "Hexavalente, Influenza, Neumococo"},
    "VCN20": {"min": "6 semanas", "max": "59 meses", "simul": "Hexavalente, Influenza, Rotavirus, Hepatitis A"},
    "SRP": {"min": "12 meses", "max": "< 10 años", "simul": "Influenza, Neumococo, Hepatitis A, Hexavalente"}
}

if esquema_consolidado.empty:
    st.success("✅ **Esquema al día.** No se detectan vacunas programadas en el esquema base para esta edad.")
else:
    for _, row in esquema_consolidado.iterrows():
        bio_id = row['Biologico']
        nombre_oficial = df_biologicos.loc[df_biologicos['ID_Biologico'] == bio_id, 'Nombre_Oficial'].values
        nombre_display = nombre_oficial[0] if len(nombre_oficial) > 0 else bio_id
        color_tema = COLORES_VACUNAS.get(bio_id, "#455A64")
        
        info = INFO_EXTRA.get(bio_id, {"min": "Según lineamiento", "max": "Según lineamiento", "simul": "Otras inactivadas"})
        
        with st.container(border=True):
            col_v1, col_v2 = st.columns([3, 2])
            with col_v1:
                st.markdown(f"<h4 style='color:{color_tema};margin:0;'>{nombre_display}</h4>", unsafe_allow_html=True)
                st.markdown(f"<span style='color:#37474F;font-weight:500;font-size:1.1rem;'>{row['Dosis_Num']}</span>", unsafe_allow_html=True)
            with col_v2:
                badge_html = f"<span style='background-color:#FFF3E0;color:#E65100;padding:6px 12px;border-radius:12px;font-size:0.85rem;font-weight:700;'>⚠️ {row['Edad_Recomendada_Texto']}</span>" if row['Origen'] == "Riesgo" else f"<span style='background-color:#E3F2FD;color:#0D47A1;padding:6px 12px;border-radius:12px;font-size:0.85rem;font-weight:700;'>✅ Etapa: {row['Edad_Recomendada_Texto']}</span>"
                st.markdown(f"<div style='text-align:right; margin-top:10px;'>{badge_html}</div>", unsafe_allow_html=True)
            
            st.write("")
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f"**🔹 Edad mínima:**<br><span style='color:#0D47A1;'>{info['min']}</span>", unsafe_allow_html=True)
            with c2: st.markdown(f"**🔸 Edad máxima:**<br><span style='color:#B71C1C;'>{info['max']}</span>", unsafe_allow_html=True)
            with c3: st.markdown(f"**💉 Simultáneo con:**<br><span style='color:#2E7D32;'>{info['simul']}</span>", unsafe_allow_html=True)
