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
    if es_mujer and anios >= 10:
        esta_embarazada = st.checkbox("🤰 ¿Está embarazada?")
    if anios <= 4:
        asiste_guarderia = st.checkbox("🧸 ¿Asiste a guardería o centro de cuidado?")

with col_cond2:
    if anios >= 18:
        es_personal_salud = st.checkbox("🩺 ¿Es personal de salud?")

# Filtro de comorbilidades según la edad actual (Evita incongruencias en neonatos)
if 'Variable_Riesgo' in df_riesgos.columns:
    # Excluimos PERSONAL_SALUD por si sigue en el Excel, ya que tiene su propio checkbox
    riesgos_validos_edad = df_riesgos[
        (df_riesgos['Edad_Minima_Anios'] <= anios) & 
        (df_riesgos['Edad_Maxima_Anios'] >= anios) & 
        (df_riesgos['Variable_Riesgo'] != "PERSONAL_SALUD")
    ]
    opciones_crudas = riesgos_validos_edad['Variable_Riesgo'].dropna().unique().tolist()
    opciones_ui = [MAPEO_RIESGOS.get(r, r) for r in opciones_crudas]
    
    seleccion_ui = st.multiselect("⚠️ Selecciona factores de riesgo o comorbilidades (si aplican):", options=opciones_ui)
    factores_seleccionados = [clave for clave, valor in MAPEO_RIESGOS.items() if valor in seleccion_ui]

# --- 5. PERFIL Y PANORAMA HISTÓRICO VISUAL ---
st.markdown("### 🏷️ Perfil Detectado")

if dias_vida <= 28: tipo_paciente, icono = ("Recién nacida", "👶") if es_mujer else ("Recién nacido", "👶")
elif anios < 2: tipo_paciente, icono = "Lactante", "🍼"
elif 2 <= anios <= 5: tipo_paciente, icono = "Preescolar", "🧸"
elif 6 <= anios <= 11: tipo_paciente, icono = ("Escolar (Niña)", "👧") if es_mujer else ("Escolar (Niño)", "👦")
elif 12 <= anios < 18: tipo_paciente, icono = ("Adolescente", "👧") if es_mujer else ("Adolescente", "👦")
elif 18 <= anios < 60: tipo_paciente, icono = ("Mujer adulta", "👩") if es_mujer else ("Hombre adulto", "👨")
else: tipo_paciente, icono = ("Adulta mayor", "👵") if es_mujer else ("Adulto mayor", "👴")

color_fondo, color_borde, color_texto, badge_bg = ("#FCE4EC", "#D81B60", "#880E4F", "#C2185B") if es_mujer else ("#E3F2FD", "#1976D2", "#0D47A1", "#1565C0")

condiciones_tags = []
if esta_embarazada: condiciones_tags.append("<strong style='color:#C2185B;'>Embarazo 🤰</strong>")
if es_personal_salud: condiciones_tags.append("<strong style='color:#0277BD;'>Personal de Salud 🩺</strong>")
if factores_seleccionados: condiciones_tags.append("<strong style='color:#E65100;'>Comorbilidad ⚠️</strong>")
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

# Cuadro visual panorámico para menores de 10 años
if anios < 10:
    C_INACTIVO = "#FBFBFB"
    act_bcg = dias_vida >= 0
    act_hepb = dias_vida >= 0
    act_m2 = total_meses >= 2
    act_m4 = total_meses >= 4
    act_m6 = total_meses >= 6
    act_m12 = total_meses >= 12
    act_m18 = total_meses >= 18
    act_m48 = total_meses >= 48
    
    tabla_pediatrica_html = f"""
    <table style="width:100%;border-collapse:separate;border-spacing:4px;font-family:'Segoe UI',sans-serif;margin-bottom:25px;">
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
    <td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:6px;border-radius:3px;">2 y 4 meses</td>
    <td colspan="2" style="background-color:{'#CFE2F3' if act_m4 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:6px;border-radius:3px;">Hexavalente (1ª y 2ª)</td>
    <td colspan="2" style="background-color:{'#D9EAD3' if act_m4 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:6px;border-radius:3px;">Anti rotavirus (1ª y 2ª)</td>
    <td colspan="2" style="background-color:{'#E7F3FE' if act_m4 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:6px;border-radius:3px;">Anti neumocócica 20v (1ª y 2ª)</td>
    </tr>
    <tr>
    <td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:6px;border-radius:3px;">12 meses</td>
    <td colspan="2" style="background-color:{'#FFF2CC' if act_m12 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:6px;border-radius:3px;">SRP (1ª dosis)</td>
    <td colspan="2" style="background-color:{'#E7F3FE' if act_m12 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:6px;border-radius:3px;">Anti neumocócica 20v (3ª dosis)</td>
    <td colspan="2" style="background-color:{'#E1BEE7' if act_m12 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:6px;border-radius:3px;">Anti varicela (Si asiste a guardería)</td>
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
    st.warning("⚠️ **Nota Clínica:** Para este grupo de edad, se asume que el esquema básico de la infancia está completo. Sin embargo, es responsabilidad del personal interrogar al paciente y solicitar la Cartilla Nacional de Salud para identificar e iniciar esquemas rezagados.")

# --- 6. ESQUEMA SUGERIDO ACTUAL (MOTOR DE REGLAS) ---
st.subheader("📋 Biológicos Correspondientes a su Edad Actual")

# Filtrado Base
esquema_aplicable = df_esquema[
    (df_esquema['Edad_Minima_Dias'] <= dias_vida) & 
    (df_esquema['Edad_Maxima_Dias'] >= dias_vida)
].copy()

if es_mujer: esquema_aplicable = esquema_aplicable[esquema_aplicable['Aplica_Mujer'] == True]
else: esquema_aplicable = esquema_aplicable[esquema_aplicable['Aplica_Hombre'] == True]

condiciones_cumplidas = ["NINGUNA"]
if esta_embarazada: condiciones_cumplidas.extend(["EMBARAZO", "EMBARAZO_20_SDG", "EMBARAZO_32_36_SDG"])
if asiste_guarderia: condiciones_cumplidas.append("ASISTE_GUARDERIA")
if es_personal_salud: condiciones_cumplidas.append("PERSONAL_SALUD")

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
                "Edad_Recomendada_Texto": f"Riesgo detectado: {MAPEO_RIESGOS.get(factor, factor)}",
                "Origen": "Riesgo"
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

# Diccionario auxiliar visual para recuperar los campos de edad y aplicación simultánea
INFO_EXTRA = {
    "BCG": {"min": "Al nacer", "max": "< 5 años (Excepto <14 años)", "simul": "Hepatitis B, Hexavalente, VCN20, Rotavirus, Influenza"},
    "HEPB": {"min": "Al nacer", "max": "7 días de vida", "simul": "Rotavirus, Neumo, BCG"},
    "HEXA": {"min": "6 semanas", "max": "< 5 años", "simul": "Influenza, Rotavirus, Neumococo, Hepatitis A"},
    "RV1": {"min": "6 semanas", "max": "7 meses 29 días", "simul": "Hexavalente, Influenza, Neumococo"},
    "VCN20": {"min": "6 semanas", "max": "59 meses (Dosis 1 y 2) / 60+ años (Única)", "simul": "Hexavalente, Influenza, Rotavirus, Hepatitis A"},
    "SRP": {"min": "12 meses", "max": "< 10 años", "simul": "Influenza, Neumococo, Hepatitis A, Hexavalente"},
    "VAR": {"min": "12 meses", "max": "59 meses", "simul": "SRP (o separar 4 semanas)"},
    "HEPA": {"min": "18 meses", "max": "59 meses", "simul": "Hexavalente, VCN20, Influenza, COVID"},
    "DPT": {"min": "4 años", "max": "< 7 años", "simul": "VCN20, Influenza, SRP, SR"},
    "VPH": {"min": "5º primaria o 11 años", "max": "11 años (Esquema base)", "simul": "Cualquier vacuna inactivada"},
    "TD": {"min": "15 años", "max": "Sin límite", "simul": "Cualquier vacuna inactivada"},
    "SR": {"min": "10 años", "max": "49 años", "simul": "Hepatitis B, Td (En sitios distintos)"},
    "INFL": {"min": "6 meses", "max": "Sin límite", "simul": "Hexavalente, Rotavirus, VCN20, Hepatitis A, COVID"},
    "COVID": {"min": "6 meses", "max": "Sin límite", "simul": "Influenza (Ampliamente recomendada)"},
    "TDPA": {"min": "20 SDG", "max": "Fin del embarazo", "simul": "Influenza, COVID-19"},
    "VSR": {"min": "32 SDG", "max": "36 SDG", "simul": "Cualquier vacuna inactivada"}
}

if esquema_consolidado.empty:
    st.success("✅ **Esquema al día.** No se detectan vacunas programadas en el esquema base para esta edad exacta sin otros factores de riesgo.")
else:
    for _, row in esquema_consolidado.iterrows():
        bio_id = row['Biologico']
        nombre_oficial = df_biologicos.loc[df_biologicos['ID_Biologico'] == bio_id, 'Nombre_Oficial'].values
        nombre_display = nombre_oficial[0] if len(nombre_oficial) > 0 else bio_id
        color_tema = COLORES_VACUNAS.get(bio_id, "#455A64")
        
        info = INFO_EXTRA.get(bio_id, {"min": "Ver Lineamiento", "max": "Ver Lineamiento", "simul": "Otras inactivadas"})
        
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
            
            st.write("")
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f"**🔹 Edad mínima:**<br><span style='color:#0D47A1;'>{info['min']}</span>", unsafe_allow_html=True)
            with c2: st.markdown(f"**🔸 Edad máxima:**<br><span style='color:#B71C1C;'>{info['max']}</span>", unsafe_allow_html=True)
            with c3: st.markdown(f"**💉 Simultáneo con:**<br><span style='color:#2E7D32;'>{info['simul']}</span>", unsafe_allow_html=True)
