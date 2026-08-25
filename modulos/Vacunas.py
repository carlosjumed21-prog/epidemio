import streamlit as st
from datetime import date
from dateutil.relativedelta import relativedelta

st.set_page_config(page_title="Esquemas de Vacunación 2026", page_icon="💉", layout="wide")

st.title("💉 Esquemas de Vacunación 2026")
st.caption("Evaluación etaria y perfil de vacunación epidemiológica.")

st.divider()

# --- 1. ENTRADA DE DATOS DEL PACIENTE ---
col_form1, col_form2 = st.columns([1, 1])

with col_form1:
    fecha_nacimiento = st.date_input(
        "📅 Fecha de nacimiento:",
        value=None,
        min_value=date(1900, 1, 1),
        max_value=date.today(),
        format="DD/MM/YYYY",
        help="Escribe la fecha (dd/mm/aaaa) y presiona Enter, o usa el calendario"
    )

with col_form2:
    sexo = st.radio(
        "⚧ Sexo:",
        options=["Hombre", "Mujer"],
        index=None,
        horizontal=True,
        help="Selecciona el sexo del paciente"
    )

# --- 2. CONTROL DE INTERFAZ EN BLANCO ---
if not fecha_nacimiento or not sexo:
    st.info("👋 **Ingresa la fecha de nacimiento y selecciona el sexo** del paciente para calcular automáticamente el esquema y las recomendaciones de vacunación.")
    st.stop()

# --- 3. CÁLCULO DE EDAD EXACTA ---
hoy = date.today()
dias_vida = (hoy - fecha_nacimiento).days
edad_delta = relativedelta(hoy, fecha_nacimiento)

anios = edad_delta.years
meses = edad_delta.months
dias = edad_delta.days

total_meses = (anios * 12) + meses
es_mujer = (sexo == "Mujer")

# Construcción de etiqueta destacada en grande
partes_grandes = []
if anios > 0:
    partes_grandes.append(f"{anios} año{'s' if anios != 1 else ''}")
if meses > 0:
    partes_grandes.append(f"{meses} mes{'es' if meses != 1 else ''}")
if dias > 0 or len(partes_grandes) == 0:
    partes_grandes.append(f"{dias} día{'s' if dias != 1 else ''}")

edad_texto_grande = " / ".join(partes_grandes)

# Condición de cohorte SRP: Corte en julio de 2020
es_nacido_pre_julio_2020 = (fecha_nacimiento < date(2020, 7, 1))

# --- 4. CONDICIONALES DE SALUD (SOLO HABILITADOS EN >= 10 AÑOS) ---
esta_embarazada = False
es_personal_salud = False

if anios >= 10:
    col_cond1, col_cond2 = st.columns([1, 1])

    with col_cond1:
        if es_mujer:
            embarazo_resp = st.radio(
                "🤰 ¿Embarazo?",
                options=["No", "Sí"],
                index=0,
                horizontal=True,
                help="Selecciona si la paciente se encuentra actualmente en periodo de gestación"
            )
            esta_embarazada = (embarazo_resp == "Sí")

    with col_cond2:
        personal_salud_resp = st.radio(
            "🩺 ¿Personal de salud?",
            options=["No", "Sí"],
            index=0,
            horizontal=True,
            help="Selecciona si el paciente es personal de salud activo o en formación clínica"
        )
        es_personal_salud = (personal_salud_resp == "Sí")

# --- 5. CLASIFICACIÓN CLÍNICA ---
if dias_vida <= 28:
    tipo_paciente = "Recién nacida (Neonata)" if es_mujer else "Recién nacido (Neonato)"
    icono = "👶"
elif anios < 1:
    tipo_paciente = "Lactante menor"
    icono = "🍼"
elif anios < 2:
    tipo_paciente = "Lactante mayor"
    icono = "🍼"
elif 2 <= anios <= 5:
    tipo_paciente = "Preescolar"
    icono = "🧸"
elif 6 <= anios <= 11:
    tipo_paciente = "Escolar (Niña)" if es_mujer else "Escolar (Niño)"
    icono = "👧" if es_mujer else "👦"
elif 12 <= anios < 18:
    tipo_paciente = "Adolescente"
    icono = "👧" if es_mujer else "👦"
elif 18 <= anios < 60:
    tipo_paciente = "Mujer adulta" if es_mujer else "Hombre adulto"
    icono = "👩" if es_mujer else "👨"
else:  # anios >= 60
    tipo_paciente = "Adulta mayor" if es_mujer else "Adulto mayor"
    icono = "👵" if es_mujer else "👴"

if es_mujer:
    color_fondo, color_borde, color_texto, badge_bg = "#FCE4EC", "#D81B60", "#880E4F", "#C2185B"
else:
    color_fondo, color_borde, color_texto, badge_bg = "#E3F2FD", "#1976D2", "#0D47A1", "#1565C0"

# --- 6. DISPLAY DE PERFIL ---
st.markdown("### 🏷️ Perfil Detectado")

condiciones_tags = []
if esta_embarazada:
    condiciones_tags.append("<strong style='color:#C2185B;'>Embarazo 🤰</strong>")
if es_personal_salud:
    condiciones_tags.append("<strong style='color:#0277BD;'>Personal de Salud 🩺</strong>")

extra_info = " &nbsp;|&nbsp; " + " &nbsp;|&nbsp; ".join(condiciones_tags) if condiciones_tags else ""

tarjeta_html = (
    f'<div style="background-color:{color_fondo};border-left:8px solid {color_borde};border-radius:8px;padding:16px 20px;margin-top:10px;margin-bottom:25px;">'
    f'<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">'
    f'<div>'
    f'<span style="font-size:1.45rem;font-weight:700;color:{color_texto};">{icono} {tipo_paciente}</span>'
    f'<div style="font-size:0.95rem;color:#37474F;margin-top:4px;">'
    f'<strong>Sexo:</strong> {sexo} &nbsp;|&nbsp; <strong>Fecha de Nacimiento:</strong> {fecha_nacimiento.strftime("%d/%m/%Y")}{extra_info}'
    f'</div>'
    f'</div>'
    f'<div style="background-color:{badge_bg};color:#FFFFFF;padding:8px 20px;border-radius:24px;font-size:1.15rem;font-weight:800;letter-spacing:0.5px;box-shadow:0 2px 5px rgba(0,0,0,0.15);">'
    f'Edad: {edad_texto_grande}'
    f'</div>'
    f'</div>'
    f'</div>'
)
st.markdown(tarjeta_html, unsafe_allow_html=True)

# --- 7. TABLAS DE ESQUEMAS VISUALES ---
if anios < 10:
    st.markdown("### 📋 Esquema Oficial de Vacunación (< 10 años)")
    
    C_BCG = "#D9D2E9"
    C_HEPB = "#F9CB9C"
    C_HEXA = "#CFE2F3"
    C_ROTA = "#D9EAD3"
    C_NEUMO = "#E7F3FE"
    C_INFL = "#FADCE9"
    C_COVID = "#C8E6C9"
    C_SRP = "#FFF2CC"
    C_DPT = "#FFE082"
    C_VARI = "#E1BEE7"
    C_HEPA = "#FFE0B2"
    C_INACTIVO = "#FBFBFB"

    # Evaluaciones clínicas por edad cumplida
    act_bcg = dias_vida >= 0
    act_hepb = dias_vida >= 0
    act_m2 = (total_meses >= 2) or (dias_vida >= 60)
    act_m4 = (total_meses >= 4) or (dias_vida >= 120)
    act_m6 = (total_meses >= 6) or (dias_vida >= 180)
    act_m7 = (total_meses >= 7) or (dias_vida >= 210)
    act_m12 = (total_meses >= 12) or (anios >= 1)
    act_m24 = (total_meses >= 24) or (anios >= 2)
    act_m36 = (total_meses >= 36) or (anios >= 3)
    act_m48 = (total_meses >= 48) or (anios >= 4)
    act_m59 = (total_meses >= 59) or (anios >= 5)

    if es_nacido_pre_julio_2020:
        act_srp_18 = False
        act_srp_72 = (total_meses >= 72) or (anios >= 6)
    else:
        act_srp_18 = (total_meses >= 18) or (anios >= 2) or (anios == 1 and meses >= 6)
        act_srp_72 = False

    act_m18_general = (total_meses >= 18) or (anios >= 2) or (anios == 1 and meses >= 6)

    tabla_pediatrica_html = f"""
<table style="width:100%;border-collapse:separate;border-spacing:4px;font-family:'Segoe UI',sans-serif;margin-top:10px;">
<thead>
<tr><th colspan="7" style="color:#881337;background-color:#FCE4EC;font-size:1.45rem;font-weight:800;text-align:center;padding:12px;border-radius:4px;">Esquema de vacunación para niñas y niños de 0 a 9 años de edad</th></tr>
<tr>
<th style="background-color:#795548;color:#FFF;font-weight:700;font-size:0.95rem;text-align:center;padding:10px;width:18%;border-radius:3px;">Edad</th>
<th colspan="6" style="background-color:#795548;color:#FFF;font-weight:700;font-size:0.95rem;text-align:center;padding:10px;border-radius:3px;">Vacunas a aplicar</th>
</tr>
</thead>
<tbody>
<tr>
<td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:10px 6px;border-radius:3px;">Nacimiento</td>
<td colspan="2" style="background-color:{C_BCG if act_bcg else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:{'#263238' if act_bcg else '#BDBDBD'};">BCG</td>
<td colspan="4" style="background-color:{C_HEPB if act_hepb else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:{'#263238' if act_hepb else '#BDBDBD'};">Anti hepatitis B</td>
</tr>
<tr>
<td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:10px 6px;border-radius:3px;">2 meses</td>
<td colspan="2" style="background-color:{C_HEXA if act_m2 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:{'#263238' if act_m2 else '#BDBDBD'};">Hexavalente acelular</td>
<td colspan="2" style="background-color:{C_ROTA if act_m2 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:{'#263238' if act_m2 else '#BDBDBD'};">Anti rotavirus</td>
<td colspan="2" style="background-color:{C_NEUMO if act_m2 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:{'#263238' if act_m2 else '#BDBDBD'};">Anti neumocócica conjugada 20 valente</td>
</tr>
<tr>
<td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:10px 6px;border-radius:3px;">4 meses</td>
<td colspan="2" style="background-color:{C_HEXA if act_m4 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:{'#263238' if act_m4 else '#BDBDBD'};">Hexavalente acelular</td>
<td colspan="2" style="background-color:{C_ROTA if act_m4 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:{'#263238' if act_m4 else '#BDBDBD'};">Anti rotavirus</td>
<td colspan="2" style="background-color:{C_NEUMO if act_m4 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:{'#263238' if act_m4 else '#BDBDBD'};">Anti neumocócica conjugada 20 valente</td>
</tr>
<tr>
<td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:10px 6px;border-radius:3px;">6 meses</td>
<td colspan="2" style="background-color:{C_HEXA if act_m6 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:{'#263238' if act_m6 else '#BDBDBD'};">Hexavalente acelular</td>
<td colspan="2" style="background-color:{C_INFL if act_m6 else C_INACTIVO};font-size:0.82rem;font-weight:600;text-align:center;padding:10px 6px;border-radius:3px;color:{'#263238' if act_m6 else '#BDBDBD'};">Anti influenza estacional (1ª dosis)<br><span style="font-size:0.75rem;">en temporada invernal</span></td>
<td colspan="2" style="background-color:{C_COVID if act_m6 else C_INACTIVO};font-size:0.82rem;font-weight:600;text-align:center;padding:10px 6px;border-radius:3px;color:{'#1B5E20' if act_m6 else '#BDBDBD'};">Anti COVID-19 (1ª dosis)<br><span style="font-size:0.75rem;">en temporada invernal</span></td>
</tr>
<tr>
<td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:10px 6px;border-radius:3px;">7 meses</td>
<td colspan="3" style="background-color:{C_INFL if act_m7 else C_INACTIVO};font-size:0.8rem;font-weight:600;text-align:center;padding:8px 6px;border-radius:3px;color:{'#263238' if act_m7 else '#BDBDBD'};">Anti influenza estacional (2ª dosis) en la misma temporada invernal, luego refuerzo anual</td>
<td colspan="3" style="background-color:{C_COVID if act_m7 else C_INACTIVO};font-size:0.8rem;font-weight:600;text-align:center;padding:8px 6px;border-radius:3px;color:{'#1B5E20' if act_m7 else '#BDBDBD'};">Anti COVID-19 (2ª dosis) en la misma temporada invernal, luego refuerzo anual</td>
</tr>
<tr>
<td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:10px 6px;border-radius:3px;">12 meses (1 año)</td>
<td colspan="2" style="background-color:{C_SRP if act_m12 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:{'#263238' if act_m12 else '#BDBDBD'};">SRP (1ª dosis)</td>
<td colspan="2" style="background-color:{C_NEUMO if act_m12 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:{'#263238' if act_m12 else '#BDBDBD'};">Anti neumocócica conjugada 20 valente</td>
<td colspan="1" style="background-color:{C_VARI if act_m12 else C_INACTIVO};font-size:0.82rem;font-weight:600;text-align:center;padding:10px 6px;border-radius:3px;color:{'#4A148C' if act_m12 else '#BDBDBD'};">Anti varicela</td>
<td colspan="1" style="background-color:{C_INFL if act_m12 else C_INACTIVO};font-size:0.82rem;font-weight:600;text-align:center;padding:10px 6px;border-radius:3px;color:{'#263238' if act_m12 else '#BDBDBD'};">Anti influenza (refuerzo anual)</td>
</tr>
<tr>
<td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:10px 6px;border-radius:3px;">18 meses</td>
<td colspan="2" style="background-color:{C_HEXA if act_m18_general else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:{'#263238' if act_m18_general else '#BDBDBD'};">Hexavalente acelular</td>
<td colspan="2" style="background-color:{C_SRP if act_srp_18 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:{'#263238' if act_srp_18 else '#BDBDBD'};">SRP (2ª dosis)</td>
<td colspan="1" style="background-color:{C_HEPA if act_m18_general else C_INACTIVO};font-size:0.82rem;font-weight:600;text-align:center;padding:10px 6px;border-radius:3px;color:{'#E65100' if act_m18_general else '#BDBDBD'};">Anti hepatitis A</td>
<td colspan="1" style="background-color:{C_INFL if act_m18_general else C_INACTIVO};font-size:0.82rem;font-weight:600;text-align:center;padding:10px 6px;border-radius:3px;color:{'#263238' if act_m18_general else '#BDBDBD'};">Anti influenza (refuerzo anual)</td>
</tr>
<tr>
<td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:10px 6px;border-radius:3px;">24 meses<br><span style="font-size:0.78rem;">(2 años)</span></td>
<td colspan="6" style="background-color:{C_INFL if act_m24 else C_INACTIVO};font-size:0.88rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:{'#263238' if act_m24 else '#BDBDBD'};">Anti influenza estacional (refuerzo anual)</td>
</tr>
<tr>
<td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:10px 6px;border-radius:3px;">36 meses<br><span style="font-size:0.78rem;">(3 años)</span></td>
<td colspan="6" style="background-color:{C_INFL if act_m36 else C_INACTIVO};font-size:0.88rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:{'#263238' if act_m36 else '#BDBDBD'};">Anti influenza estacional (refuerzo anual)</td>
</tr>
<tr>
<td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:10px 6px;border-radius:3px;">48 meses<br><span style="font-size:0.78rem;">(4 años)</span></td>
<td colspan="3" style="background-color:{C_INFL if act_m48 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:{'#263238' if act_m48 else '#BDBDBD'};">Anti influenza estacional (refuerzo anual)</td>
<td colspan="3" style="background-color:{C_DPT if act_m48 else C_INACTIVO};font-size:0.95rem;font-weight:700;text-align:center;padding:10px 8px;border-radius:3px;color:{'#5D4037' if act_m48 else '#BDBDBD'};">DPT (refuerzo)</td>
</tr>
<tr>
<td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:10px 6px;border-radius:3px;">59 meses<br><span style="font-size:0.78rem;">(5 años)</span></td>
<td colspan="3" style="background-color:{C_INFL if act_m59 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:{'#263238' if act_m59 else '#BDBDBD'};">Anti influenza estacional (refuerzo anual)</td>
<td colspan="3" style="background-color:{C_COVID if act_m59 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:{'#1B5E20' if act_m59 else '#BDBDBD'};">Anti COVID-19 (refuerzo anual)</td>
</tr>
<tr>
<td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:10px 6px;border-radius:3px;">72 meses<br><span style="font-size:0.78rem;">(6 años)</span></td>
<td colspan="6" style="background-color:{C_SRP if act_srp_72 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:{'#263238' if act_srp_72 else '#BDBDBD'};">SRP (2ª dosis - Nacidos antes de julio 2020)</td>
</tr>
</tbody>
</table>
"""
    st.markdown(tabla_pediatrica_html, unsafe_allow_html=True)

else:
    # --- ESQUEMA >= 10 AÑOS Y ADULTOS ---
    st.markdown("### 📋 Esquema Oficial de Vacunación (10 a 19 años y Adultos)")
    
    C_TD = "#D2D4EA"
    C_SR = "#F8E5DB"
    C_HEPB_AD = "#F9CCA7"
    C_VPH = "#FEF9BE"
    C_TDPA = "#DCEBD6"
    C_VSR = "#B2DFDB"
    C_NEUMO_AD = "#DCECF9"
    C_INFL_AD = "#FAD6E6"
    C_INACTIVO = "#F5F5F5"

    es_adulto_mayor = (anios >= 60)

    act_td = (anios >= 15) or es_personal_salud
    act_sr = (10 <= anios <= 39) or (es_personal_salud and not esta_embarazada)
    act_hepb = (anios >= 11) or es_personal_salud
    act_vph = (10 <= anios <= 49) and not esta_embarazada
    act_tdpa = esta_embarazada or es_personal_salud
    act_neumo = es_adulto_mayor
    act_infl = True

    fila_vsr_html = ""
    if esta_embarazada:
        fila_vsr_html = f"""
<tr>
<td style="background-color:{C_VSR};font-size:0.95rem;font-weight:700;text-align:center;padding:12px;border-radius:3px;color:#004D40;">VSR</td>
<td style="background-color:{C_VSR};font-size:0.95rem;font-weight:500;text-align:center;padding:12px;border-radius:3px;color:#004D40;">Casos graves por el virus respiratorio sincitial (VRS) en lactantes desde el nacimiento hasta los 6 meses de edad mediante la inmunización activa de mujeres embarazadas</td>
</tr>
"""

    tabla_adultos_html = f"""
<table style="width:100%;border-collapse:separate;border-spacing:4px;font-family:'Segoe UI',sans-serif;margin-top:10px;">
<thead>
<tr><th colspan="2" style="color:#A07248;font-size:1.55rem;font-weight:800;text-align:center;padding-bottom:12px;">Esquema de vacunación para población de 10 a 19 años y adultos a partir de los 20 años</th></tr>
<tr>
<th style="background-color:#555;color:#FFF;font-weight:700;font-size:1.05rem;text-align:center;padding:12px;border-radius:3px;width:45%;">Vacunas</th>
<th style="background-color:#555;color:#FFF;font-weight:700;font-size:1.05rem;text-align:center;padding:12px;border-radius:3px;width:55%;">Enfermedad que previene</th>
</tr>
</thead>
<tbody>
<tr>
<td style="background-color:{C_TD if act_td else C_INACTIVO};font-size:0.95rem;font-weight:600;text-align:center;padding:12px;border-radius:3px;color:{'#212121' if act_td else '#9E9E9E'};">Td</td>
<td style="background-color:{C_TD if act_td else C_INACTIVO};font-size:0.95rem;font-weight:500;text-align:center;padding:12px;border-radius:3px;color:{'#212121' if act_td else '#9E9E9E'};">Tétanos, difteria</td>
</tr>
<tr>
<td style="background-color:{C_SR if act_sr else C_INACTIVO};font-size:0.95rem;font-weight:600;text-align:center;padding:12px;border-radius:3px;color:{'#212121' if act_sr else '#9E9E9E'};">SR</td>
<td style="background-color:{C_SR if act_sr else C_INACTIVO};font-size:0.95rem;font-weight:500;text-align:center;padding:12px;border-radius:3px;color:{'#212121' if act_sr else '#9E9E9E'};">Sarampión, rubéola</td>
</tr>
<tr>
<td style="background-color:{C_HEPB_AD if act_hepb else C_INACTIVO};font-size:0.95rem;font-weight:600;text-align:center;padding:12px;border-radius:3px;color:{'#212121' if act_hepb else '#9E9E9E'};">Anti hepatitis B</td>
<td style="background-color:{C_HEPB_AD if act_hepb else C_INACTIVO};font-size:0.95rem;font-weight:500;text-align:center;padding:12px;border-radius:3px;color:{'#212121' if act_hepb else '#9E9E9E'};">Hepatitis B</td>
</tr>
<tr>
<td style="background-color:{C_VPH if act_vph else C_INACTIVO};font-size:0.95rem;font-weight:600;text-align:center;padding:12px;border-radius:3px;color:{'#212121' if act_vph else '#9E9E9E'};">VPH</td>
<td style="background-color:{C_VPH if act_vph else C_INACTIVO};font-size:0.95rem;font-weight:500;text-align:center;padding:12px;border-radius:3px;color:{'#212121' if act_vph else '#9E9E9E'};">Infección por Virus del Papiloma Humano</td>
</tr>
<tr>
<td style="background-color:{C_TDPA if act_tdpa else C_INACTIVO};font-size:0.95rem;font-weight:600;text-align:center;padding:12px;border-radius:3px;color:{'#212121' if act_tdpa else '#9E9E9E'};">Tdpa</td>
<td style="background-color:{C_TDPA if act_tdpa else C_INACTIVO};font-size:0.95rem;font-weight:500;text-align:center;padding:12px;border-radius:3px;color:{'#212121' if act_tdpa else '#9E9E9E'};">Tétanos, difteria, tos ferina</td>
</tr>
{fila_vsr_html}
<tr>
<td style="background-color:{C_NEUMO_AD if act_neumo else C_INACTIVO};font-size:0.95rem;font-weight:600;text-align:center;padding:12px;border-radius:3px;color:{'#212121' if act_neumo else '#9E9E9E'};">Anti neumocócica conjugada 20 valente (VCN20)</td>
<td style="background-color:{C_NEUMO_AD if act_neumo else C_INACTIVO};font-size:0.95rem;font-weight:500;text-align:center;padding:12px;border-radius:3px;color:{'#212121' if act_neumo else '#9E9E9E'};">Infección por neumococo</td>
</tr>
<tr>
<td style="background-color:{C_INFL_AD if act_infl else C_INACTIVO};font-size:0.95rem;font-weight:600;text-align:center;padding:12px;border-radius:3px;color:{'#212121' if act_infl else '#9E9E9E'};">Anti influenza estacional</td>
<td style="background-color:{C_INFL_AD if act_infl else C_INACTIVO};font-size:0.95rem;font-weight:500;text-align:center;padding:12px;border-radius:3px;color:{'#212121' if act_infl else '#9E9E9E'};">Influenza</td>
</tr>
</tbody>
</table>
"""
    st.markdown(tabla_adultos_html, unsafe_allow_html=True)

# --- 8. CATÁLOGO TÉCNICO PEDIÁTRICO SEGÚN CUADRO 7.1 OFICIAL ---
CATALOGO_PEDIATRICO = [
    {
        "nombre": "BCG (Bacilo de Calmette - Guérin)",
        "dosis": "Dosis única contra formas graves de Tuberculosis",
        "hito_meses": 0,
        "edad_rec_str": "Al nacer",
        "edad_min_str": "Al nacer",
        "edad_max_str": "< 5 años (Excepcionalmente < 14 años)",
        "es_candidato": lambda a, m, d, tm: (a < 5),
        "intervalo_rec": "No Aplica",
        "intervalo_min": "No Aplica",
        "simultaneas": ["Hexavalente", "Influenza", "Rotavirus", "Neumococo", "Hepatitis A y B"],
        "cualquier_intervalo": ["SRP o SR y Varicela"],
        "intervalo_especial": [],
        "color": "#6A1B9A"
    },
    {
        "nombre": "Hepatitis B",
        "dosis": "Dosis al nacimiento",
        "hito_meses": 0,
        "edad_rec_str": "Al nacer o a los 7 días de vida",
        "edad_min_str": "Al nacer",
        "edad_max_str": "Preferentemente no después de los 7 días",
        "es_candidato": lambda a, m, d, tm: (dias_vida <= 7),
        "intervalo_rec": "No Aplica",
        "intervalo_min": "No Aplica",
        "simultaneas": ["Rotavirus", "Neumococo", "BCG (en ausencia potencial de Hexavalente)"],
        "cualquier_intervalo": [],
        "intervalo_especial": [],
        "color": "#E65100"
    },
    {
        "nombre": "*(DPaT+IPV+HB+Hib)-1ª",
        "dosis": "Hexavalente acelular 1ª Dosis",
        "hito_meses": 2,
        "edad_rec_str": "2 meses",
        "edad_min_str": "6 semanas",
        "edad_max_str": "< 5 años",
        "es_candidato": lambda a, m, d, tm: (a < 5),
        "intervalo_rec": "8 semanas",
        "intervalo_min": "4 semanas",
        "simultaneas": ["Influenza", "Rotavirus", "Neumococo", "Hepatitis A"],
        "cualquier_intervalo": ["BCG", "SRP o SR"],
        "intervalo_especial": [("Varicela", "4 semanas de separación")],
        "color": "#0277BD"
    },
    {
        "nombre": "(Rv1)-1ª Antirrotavirus",
        "dosis": "Antirrotavirus 1ª Dosis",
        "hito_meses": 2,
        "edad_rec_str": "2 meses",
        "edad_min_str": "6 semanas",
        "edad_max_str": "7 meses 29 días",
        "es_candidato": lambda a, m, d, tm: (tm < 8),
        "intervalo_rec": "8 semanas",
        "intervalo_min": "4 semanas",
        "simultaneas": ["Hexavalente", "Influenza", "Neumococo"],
        "cualquier_intervalo": ["BCG"],
        "intervalo_especial": [],
        "color": "#2E7D32"
    },
    {
        "nombre": "(VCN20)-1ª Neumocócica conjugada 20v",
        "dosis": "Neumocócica conjugada 20 valente 1ª Dosis",
        "hito_meses": 2,
        "edad_rec_str": "2 meses",
        "edad_min_str": "6 semanas",
        "edad_max_str": "59 meses de edad",
        "es_candidato": lambda a, m, d, tm: (tm <= 59),
        "intervalo_rec": "8 semanas",
        "intervalo_min": "4 a 8 semanas",
        "simultaneas": ["Hexavalente", "Influenza", "Rotavirus", "Hepatitis A"],
        "cualquier_intervalo": ["BCG", "SRP o SR y Varicela"],
        "intervalo_especial": [],
        "color": "#00838F"
    },
    {
        "nombre": "*(DPaT+IPV+HB+Hib)-2ª",
        "dosis": "Hexavalente acelular 2ª Dosis",
        "hito_meses": 4,
        "edad_rec_str": "4 meses",
        "edad_min_str": "10 semanas",
        "edad_max_str": "< 5 años",
        "es_candidato": lambda a, m, d, tm: (a < 5),
        "intervalo_rec": "8 semanas",
        "intervalo_min": "4 semanas",
        "simultaneas": ["Influenza", "Rotavirus", "Neumococo", "Hepatitis A"],
        "cualquier_intervalo": ["BCG", "SRP o SR"],
        "intervalo_especial": [("Varicela", "4 semanas de separación")],
        "color": "#0277BD"
    },
    {
        "nombre": "(Rv1)-2ª Antirrotavirus",
        "dosis": "Antirrotavirus 2ª Dosis",
        "hito_meses": 4,
        "edad_rec_str": "4 meses",
        "edad_min_str": "10 semanas",
        "edad_max_str": "7 meses 29 días",
        "es_candidato": lambda a, m, d, tm: (tm < 8),
        "intervalo_rec": "No Aplica",
        "intervalo_min": "No Aplica",
        "simultaneas": ["Hexavalente", "Influenza", "Neumococo"],
        "cualquier_intervalo": ["BCG"],
        "intervalo_especial": [],
        "color": "#2E7D32"
    },
    {
        "nombre": "(VCN20)-2ª Neumocócica conjugada 20v",
        "dosis": "Neumocócica conjugada 20 valente 2ª Dosis",
        "hito_meses": 4,
        "edad_rec_str": "4 meses",
        "edad_min_str": "10 semanas",
        "edad_max_str": "59 meses de edad",
        "es_candidato": lambda a, m, d, tm: (tm <= 59),
        "intervalo_rec": "8 meses",
        "intervalo_min": "8 semanas",
        "simultaneas": ["Hexavalente", "Influenza", "Rotavirus", "Hepatitis A"],
        "cualquier_intervalo": ["BCG", "SRP o SR y Varicela"],
        "intervalo_especial": [],
        "color": "#00838F"
    },
    {
        "nombre": "*(DPaT+IPV+HB+Hib)-3ª",
        "dosis": "Hexavalente acelular 3ª Dosis",
        "hito_meses": 6,
        "edad_rec_str": "6 meses",
        "edad_min_str": "14 semanas",
        "edad_max_str": "< 5 años",
        "es_candidato": lambda a, m, d, tm: (a < 5),
        "intervalo_rec": "12 semanas",
        "intervalo_min": "6 semanas",
        "simultaneas": ["Influenza", "Rotavirus", "Neumococo", "Hepatitis A"],
        "cualquier_intervalo": ["BCG", "SRP o SR"],
        "intervalo_especial": [("Varicela", "4 semanas de separación")],
        "color": "#0277BD"
    },
    {
        "nombre": "Influenza Estacional (1ª Dosis)",
        "dosis": "1ª Dosis",
        "hito_meses": 6,
        "edad_rec_str": "6 meses",
        "edad_min_str": "6 meses",
        "edad_max_str": "59 meses",
        "es_candidato": lambda a, m, d, tm: (tm <= 59),
        "intervalo_rec": "4 semanas",
        "intervalo_min": "4 semanas",
        "simultaneas": ["Hexavalente", "Rotavirus", "Neumococo", "Hepatitis A y COVID-19"],
        "cualquier_intervalo": ["BCG, SRP o SR y Varicela"],
        "intervalo_especial": [],
        "color": "#AD1457"
    },
    {
        "nombre": "Influenza Estacional (2ª Dosis)",
        "dosis": "2ª Dosis",
        "hito_meses": 7,
        "edad_rec_str": "7 meses",
        "edad_min_str": "7 meses",
        "edad_max_str": "59 meses",
        "es_candidato": lambda a, m, d, tm: (tm <= 59),
        "intervalo_rec": "Anual",
        "intervalo_min": "4 semanas",
        "simultaneas": ["Hexavalente", "Rotavirus", "Neumococo", "Hepatitis A y COVID-19"],
        "cualquier_intervalo": ["BCG, SRP o SR y Varicela"],
        "intervalo_especial": [],
        "color": "#AD1457"
    },
    {
        "nombre": "(SRP)-1ª Sarampión, rubéola y parotiditis",
        "dosis": "Triple Viral 1ª Dosis",
        "hito_meses": 12,
        "edad_rec_str": "12 meses",
        "edad_min_str": "12 meses",
        "edad_max_str": "Menores de 10 años",
        "es_candidato": lambda a, m, d, tm: (a < 10),
        "intervalo_rec": "5 años",
        "intervalo_min": "4 semanas",
        "simultaneas": ["Influenza", "Neumococo", "Hepatitis A", "BCG y Hexavalente"],
        "cualquier_intervalo": [],
        "intervalo_especial": [("SR", "Intervalo de 4 semanas")],
        "color": "#E65100"
    },
    {
        "nombre": "(VCN20)-3ª Neumocócica conjugada 20v",
        "dosis": "Neumocócica conjugada 20 valente 3ª Dosis",
        "hito_meses": 12,
        "edad_rec_str": "12 meses",
        "edad_min_str": "12 semanas",
        "edad_max_str": "59 meses de edad",
        "es_candidato": lambda a, m, d, tm: (tm <= 59),
        "intervalo_rec": "No Aplica",
        "intervalo_min": "No Aplica",
        "simultaneas": ["Hexavalente", "Influenza", "Rotavirus", "Hepatitis A"],
        "cualquier_intervalo": ["BCG, SRP o SR y Varicela"],
        "intervalo_especial": [],
        "color": "#00838F"
    },
    {
        "nombre": "*(DPaT+IPV+HB+Hib)-4ª",
        "dosis": "Hexavalente acelular 4ª Dosis",
        "hito_meses": 18,
        "edad_rec_str": "18 meses",
        "edad_min_str": "12 meses",
        "edad_max_str": "< 5 años",
        "es_candidato": lambda a, m, d, tm: (a < 5),
        "intervalo_rec": "No Aplica",
        "intervalo_min": "No Aplica",
        "simultaneas": ["Influenza", "Rotavirus", "Neumococo", "Hepatitis A"],
        "cualquier_intervalo": ["BCG", "SRP o SR"],
        "intervalo_especial": [("Varicela", "4 semanas de separación")],
        "color": "#0277BD"
    },
    {
        "nombre": "(SRP)-2ª Sarampión, rubéola y parotiditis",
        "dosis": "Triple Viral 2ª Dosis (Nacidos a partir de julio 2020 / a partir del 2022)",
        "hito_meses": 18,
        "edad_rec_str": "Que cumplan 18 meses a partir del 2022",
        "edad_min_str": "18 meses",
        "edad_max_str": "Menores de 10 años",
        "es_candidato": lambda a, m, d, tm: (a < 10),
        "intervalo_rec": "No Aplica",
        "intervalo_min": "No Aplica",
        "simultaneas": ["Influenza", "Neumococo", "Hepatitis A", "BCG y Hexavalente"],
        "cualquier_intervalo": [],
        "intervalo_especial": [("SR", "Intervalo de 4 semanas")],
        "color": "#E65100"
    },
    {
        "nombre": "(SRP)-2ª Sarampión, rubéola y parotiditis",
        "dosis": "Triple Viral 2ª Dosis (Nacidos antes de julio 2020 / cohorte 2022-2026)",
        "hito_meses": 72,
        "edad_rec_str": "6 años (quienes cumplan esa edad de 2022-2026)",
        "edad_min_str": "6 años (quienes cumplan esa edad de 2022-2026)",
        "edad_max_str": "Menores de 10 años",
        "es_candidato": lambda a, m, d, tm: (a < 10),
        "intervalo_rec": "No Aplica",
        "intervalo_min": "No Aplica",
        "simultaneas": ["Influenza", "Neumococo", "Hepatitis A", "BCG y Hexavalente"],
        "cualquier_intervalo": [],
        "intervalo_especial": [("SR", "Intervalo de 4 semanas")],
        "color": "#E65100"
    }
]

# --- 9. PANEL INFERIOR DINÁMICO ---
st.divider()

if anios < 10:
    hitos_disponibles = [0, 2, 4, 6, 7, 12, 18, 24, 36, 48, 59, 72]
    
    if dias_vida <= 28:
        hito_objetivo = 0
    elif anios == 2:
        hito_objetivo = 24
    elif anios == 3:
        hito_objetivo = 36
    elif anios == 4:
        hito_objetivo = 48
    elif anios == 5:
        hito_objetivo = 59
    elif anios >= 6:
        hito_objetivo = 72
    else:
        hitos_pendientes = [h for h in hitos_disponibles if h >= total_meses]
        hito_objetivo = hitos_pendientes[0] if hitos_pendientes else 72

    candidatas = [v for v in CATALOGO_PEDIATRICO if v["hito_meses"] == hito_objetivo]
    
    vacunas_a_mostrar = []
    for v in candidatas:
        if "SRP" in v["nombre"] and v["hito_meses"] == 18 and es_nacido_pre_julio_2020:
            continue
        if "SRP" in v["nombre"] and v["hito_meses"] == 72 and not es_nacido_pre_julio_2020:
            continue
        vacunas_a_mostrar.append(v)

    texto_hito = vacunas_a_mostrar[0]["edad_rec_str"] if vacunas_a_mostrar else "Etapa actual"
    
    st.subheader(f"🎯 Cuadro 7.1 — Recomendación y Criterios Clínicos ({texto_hito})")
    st.caption(f"Evaluación de candidatura y compatibilidades según lineamientos para la edad calculada ({edad_texto_grande}):")

    for v in vacunas_a_mostrar:
        es_apto = v["es_candidato"](anios, meses, dias, total_meses)
        
        with st.container(border=True):
            col_t1, col_t2 = st.columns([3, 2])
            with col_t1:
                st.markdown(f"<h4 style='color:{v['color']};margin:0;'>{v['nombre']} — <span style='color:#37474F;font-weight:500;'>{v['dosis']}</span></h4>", unsafe_allow_html=True)
            with col_t2:
                if es_apto:
                    badge_status_html = "<span style='background-color:#E8F5E9;color:#2E7D32;padding:4px 10px;border-radius:12px;font-size:0.8rem;font-weight:700;'>✅ CANDIDATO VIGENTE</span>"
                else:
                    badge_status_html = "<span style='background-color:#D32F2F;color:#FFFFFF;padding:4px 10px;border-radius:12px;font-size:0.8rem;font-weight:700;'>⛔ FUERA DE RANGO</span>"
                
                badge_rec_html = f"<span style='background-color:#ECEFF1;color:#37474F;padding:4px 10px;border-radius:12px;font-size:0.8rem;font-weight:600;'>Recomendada: {v['edad_rec_str']}</span>"
                st.markdown(f"<div style='text-align:right;'>{badge_status_html} &nbsp; {badge_rec_html}</div>", unsafe_allow_html=True)

            if not es_apto:
                st.error(f"⚠️ **Alerta epidemiológica:** La edad actual del paciente ({edad_texto_grande}) sobrepasa la **edad máxima permitida** ({v['edad_max_str']}). No se recomienda su aplicación en este momento.")

            st.write("")
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f"**🔹 Edad mínima permitida:**<br><span style='color:#0D47A1;'>{v['edad_min_str']}</span>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"**🔸 Edad máxima permitida:**<br><span style='color:#B71C1C;'>{v['edad_max_str']}</span>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"**⏱️ Intervalo recomendado:**<br>{v['intervalo_rec']}", unsafe_allow_html=True)
            with c4:
                st.markdown(f"**⚠️ Intervalo mínimo:**<br><span style='color:#E65100;font-weight:600;'>{v['intervalo_min']}</span>", unsafe_allow_html=True)

            st.divider()
            
            st.markdown("**🔗 Aplicación entre biológicos (Compatibilidades e Intervalos):**")
            
            badges_html = []
            for sim in v["simultaneas"]:
                badges_html.append(f"<span style='background-color:#E8F5E9;color:#1B5E20;border:1px solid #A5D6A7;padding:3px 8px;border-radius:6px;font-size:0.8rem;font-weight:600;margin-right:5px;display:inline-block;margin-bottom:4px;'>💉 Se puede aplicar simultáneamente con: {sim}</span>")
            for ci in v["cualquier_intervalo"]:
                badges_html.append(f"<span style='background-color:#E0F2F1;color:#004D40;border:1px solid #80CBC4;padding:3px 8px;border-radius:6px;font-size:0.8rem;font-weight:600;margin-right:5px;display:inline-block;margin-bottom:4px;'>⏱️ Y con cualquier intervalo con: {ci}</span>")
            for ie in v["intervalo_especial"]:
                badges_html.append(f"<span style='background-color:#FFF3E0;color:#BF360C;border:1px solid #FFCC80;padding:3px 8px;border-radius:6px;font-size:0.8rem;font-weight:600;margin-right:5px;display:inline-block;margin-bottom:4px;'>⚠️ {ie[0]}: {ie[1]}</span>")
            
            st.markdown("".join(badges_html), unsafe_allow_html=True)

elif esta_embarazada:
    # --- PANEL EXCLUSIVO PARA EMBARAZO ---
    if es_personal_salud:
        st.subheader("🤰🩺 Biológicos Recomendados: Personal de Salud en Periodo de Gestación")
        st.info("Las personas trabajadoras de la salud en periodo de gestación deben cumplir con el control prenatal correspondiente y el médico tratante determinará la protección adicional que amerite; sin embargo, toda persona embarazada debe recibir la vacuna Tdpa en cada embarazo, independientemente de su antecedente vacunal con Td y del intervalo intergenésico; así como, la vacuna contra la influenza estacional, contra la COVID-19 y contra el Virus Sincitial Respiratorio, durante la temporada invernal.")
        
        # Tdpa
        with st.container(border=True):
            st.markdown("<h4 style='color:#2E7D32;margin:0;'>Tdpa</h4>", unsafe_allow_html=True)
            st.markdown("* **Indicación:** Una dosis de Tdpa en cada embarazo a partir de la semana 20 de gestación como sustitución o no de Td.")
        
        # VSR
        with st.container(border=True):
            st.markdown("<h4 style='color:#004D40;margin:0;'>Contra el VSR</h4>", unsafe_allow_html=True)
            st.markdown("* **Indicación:** Una dosis entre las semanas 32 y 36 de gestación.")
        
        # Influenza y COVID-19
        col_emb1, col_emb2 = st.columns(2)
        with col_emb1:
            with st.container(border=True):
                st.markdown("<h4 style='color:#AD1457;margin:0;'>Anti influenza estacional</h4>", unsafe_allow_html=True)
                st.markdown("* **Indicación:** Una dosis en cualquier trimestre del embarazo, durante la temporada invernal.")
        with col_emb2:
            with st.container(border=True):
                st.markdown("<h4 style='color:#1B5E20;margin:0;'>Contra la COVID-19</h4>", unsafe_allow_html=True)
                st.markdown("* **Indicación:** Una dosis en cualquier trimestre del embarazo, preferentemente a partir del segundo trimestre, derivado del beneficio de transmisión de anticuerpos al feto.")
        
        st.warning("⛔ **Contraindicación estricta en el embarazo:** Vacunas de virus vivos atenuados como **SR, SRP, Varicela y Fiebre Amarilla** están contraindicadas durante toda la gestación.")

    else:
        st.subheader("🤰 Biológicos Recomendados durante el Embarazo")
        st.caption("Lineamiento Oficial de Vacunación en Personas Embarazadas:")

        # 1. Tdpa
        with st.container(border=True):
            st.markdown("<h4 style='color:#2E7D32;margin:0;'>Tdpa (Tétanos, Difteria, Tos Ferina acelular)</h4>", unsafe_allow_html=True)
            st.markdown("""
            * **Indicación:** **En cada embarazo**, independientemente del antecedente de vacunación previa.
            * **Momento de aplicación:** A partir de la **semana 20 de gestación** (preferentemente entre las semanas 27 y 36).
            * **Dosis y Vía:** Dosis única de 0.5 mL intramuscular en región deltoidea.
            * **Objetivo:** Transferencia transplacentaria masiva de anticuerpos contra pertussis para proteger al recién nacido durante sus primeros meses de vida.
            """)

        # 2. VSR
        with st.container(border=True):
            st.markdown("<h4 style='color:#004D40;margin:0;'>Vacuna contra el Virus Sincitial Respiratorio (VSR)</h4>", unsafe_allow_html=True)
            st.markdown("""
            * **Indicación:** Personas embarazadas entre las **32 y 36 semanas de gestación**.
            * **Objetivo principal:** Prevenir casos graves por el virus respiratorio sincitial (VRS) en lactantes desde el nacimiento hasta los 6 meses de edad mediante la inmunización activa de mujeres embarazadas.
            * **Dosis y Vía:** Dosis única de 0.5 mL intramuscular en región deltoidea del brazo no dominante.
            """)

        # 3. Influenza y COVID-19
        col_emb1, col_emb2 = st.columns(2)
        with col_emb1:
            with st.container(border=True):
                st.markdown("<h4 style='color:#AD1457;margin:0;'>Anti Influenza Estacional</h4>", unsafe_allow_html=True)
                st.markdown("""
                * **Indicación:** En **cualquier trimestre** del embarazo durante la temporada invernal activa.
                * **Dosis y Vía:** 0.5 mL intramuscular en región deltoidea.
                """)
        with col_emb2:
            with st.container(border=True):
                st.markdown("<h4 style='color:#1B5E20;margin:0;'>Anti COVID-19</h4>", unsafe_allow_html=True)
                st.markdown("""
                * **Indicación:** A partir del **segundo trimestre** de gestación o según campaña invernal activa.
                * **Dosis y Vía:** Intramuscular en región deltoidea.
                """)

        st.warning("⛔ **Contraindicación estricta en el embarazo:** Vacunas de virus vivos atenuados como **SR, SRP, Varicela y Fiebre Amarilla** están contraindicadas durante toda la gestación.")

elif es_personal_salud:
    # --- PANEL EXCLUSIVO PARA PERSONAL DE SALUD ---
    st.subheader("🩺 Esquema de Inmunización para Trabajadores de la Salud (Cuadro 10)")
    st.caption("Adaptado de los lineamientos oficiales para protección ocupacional.")

    tabla_ps_html = """
    <table style="width:100%;border-collapse:collapse;font-family:'Segoe UI',sans-serif;margin-top:10px; border: 1px solid #ddd;">
    <thead style="background-color:#900C3F; color:white;">
    <tr>
    <th style="padding:10px; border: 1px solid #ddd; text-align:center;">VACUNA</th>
    <th style="padding:10px; border: 1px solid #ddd; text-align:center;">ENFERMEDAD QUE PREVIENE</th>
    <th style="padding:10px; border: 1px solid #ddd; text-align:center;">DOSIS/ESQUEMA</th>
    <th style="padding:10px; border: 1px solid #ddd; text-align:center;">FRECUENCIA</th>
    </tr>
    </thead>
    <tbody style="background-color:#FAFAFA; color:#333;">
    <tr>
    <td style="padding:10px; border: 1px solid #ddd; font-weight:bold; text-align:center;">Anti Influenza estacional</td>
    <td style="padding:10px; border: 1px solid #ddd;">Complicaciones severas y mortalidad por influenza</td>
    <td style="padding:10px; border: 1px solid #ddd; text-align:center;">Una aplicación de 0.5 mL.</td>
    <td style="padding:10px; border: 1px solid #ddd; text-align:center;">Anual (en época invernal)</td>
    </tr>
    <tr>
    <td style="padding:10px; border: 1px solid #ddd; font-weight:bold; text-align:center;">Contra la COVID-19</td>
    <td style="padding:10px; border: 1px solid #ddd;">Cuadros graves y letalidad por el virus SARS-CoV-2</td>
    <td style="padding:10px; border: 1px solid #ddd; text-align:center;">Una aplicación de 0.5 mL.*</td>
    <td style="padding:10px; border: 1px solid #ddd; text-align:center;">Sujeta a directrices y políticas vigentes de la Secretaría de Salud</td>
    </tr>
    <tr>
    <td style="padding:10px; border: 1px solid #ddd; font-weight:bold; text-align:center;">Anti hepatitis B (HB)</td>
    <td style="padding:10px; border: 1px solid #ddd;">Infección por Hepatitis B</td>
    <td style="padding:10px; border: 1px solid #ddd;">2 aplicaciones de 20 µg (intervalo 0, 1 mes).<br>O bien:<br>3 aplicaciones** de 10 µg (intervalo 0, 1, 6 meses).</td>
    <td style="padding:10px; border: 1px solid #ddd;">Personal de laboratorio clínico: requiere refuerzo si la titulación de anticuerpos (anti-HBs) es inferior a 10 mUI/mL.</td>
    </tr>
    <tr>
    <td style="padding:10px; border: 1px solid #ddd; font-weight:bold; text-align:center;">SR***</td>
    <td style="padding:10px; border: 1px solid #ddd;">Sarampión y Rubéola</td>
    <td style="padding:10px; border: 1px solid #ddd; text-align:center;">Una aplicación de 0.5 mL.</td>
    <td style="padding:10px; border: 1px solid #ddd; text-align:center;">Dosis única</td>
    </tr>
    <tr>
    <td style="padding:10px; border: 1px solid #ddd; font-weight:bold; text-align:center;">Td</td>
    <td style="padding:10px; border: 1px solid #ddd;">Tétanos y Difteria</td>
    <td style="padding:10px; border: 1px solid #ddd;">
    <strong>Con antecedente completo****:</strong> A partir de los 15 años, refuerzo decenal.<br><br>
    <strong>Con antecedente incompleto/desconocido:</strong> 3 aplicaciones (0, 1, 12 meses) y luego refuerzos decenales.
    </td>
    <td style="padding:10px; border: 1px solid #ddd; text-align:center;">Cada 10 años</td>
    </tr>
    <tr>
    <td style="padding:10px; border: 1px solid #ddd; font-weight:bold; text-align:center;">Tdpa</td>
    <td style="padding:10px; border: 1px solid #ddd;">Tétanos, Difteria y Tos ferina</td>
    <td style="padding:10px; border: 1px solid #ddd; background-color:#FFF9C4;">
    Trabajadores de la salud con exposición a pacientes pediátricos: administrar 1 aplicación si carecen de historial vacunal previo.
    </td>
    <td style="padding:10px; border: 1px solid #ddd; text-align:center;">Dosis única</td>
    </tr>
    </tbody>
    </table>
    """
    st.markdown(tabla_ps_html, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size: 0.85rem; color: #555; margin-top: 15px;">
    <strong>Notas aclaratorias:</strong><br>
    * Sujeto a disponibilidad de biológicos a nivel nacional.<br>
    ** Utilizar esta pauta si la unidad médica carece de la formulación de 20 µg.<br>
    *** Si el trabajador tiene menos de 40 años y carece de documentación sobre al menos dos aplicaciones de SR o SRP, debe recibir 2 dosis (0.5 mL) separadas por 4 semanas.<br>
    **** Se considera historial completo poseer 5 dosis del esquema infantil (4 de hexavalente + 1 de DPT) o 3 aplicaciones de Td (intervalos 0, 1 y 12 meses).
    </div>
    """, unsafe_allow_html=True)

elif es_adulto_mayor:
    # --- PANEL EXCLUSIVO PARA ADULTO MAYOR (>= 60 AÑOS) ---
    st.subheader(f"🎯 Biológicos Prioritarios para {tipo_paciente}")
    st.caption(f"Lineamientos de vacunación del adulto mayor en México (Edad actual: {edad_texto_grande}):")

    # 1. Neumococo 20V
    with st.container(border=True):
        st.markdown("<h4 style='color:#00838F;margin:0;'>Anti Neumocócica Conjugada 20 Valente (VCN20)</h4>", unsafe_allow_html=True)
        st.markdown("""
        * **Criterio Oficial:** Toda la población de **60 años y más** (Dosis única).
        * **Dosis y Vía:** 0.5 mL intramuscular en región deltoidea.
        * **Revacunación:** No se requiere (esquema de dosis única).
        """)

    # 2. Influenza Estacional
    with st.container(border=True):
        st.markdown("<h4 style='color:#AD1457;margin:0;'>Anti Influenza Estacional</h4>", unsafe_allow_html=True)
        st.markdown("""
        * **Criterio Oficial:** Toda la población de **60 años y más**.
        * **Frecuencia:** **Dosis anual de refuerzo** al inicio de la temporada invernal (octubre a marzo).
        * **Dosis y Vía:** 0.5 mL intramuscular en región deltoidea.
        """)

    # 3. Td Refuerzo decenal
    with st.container(border=True):
        st.markdown("<h4 style='color:#3949AB;margin:0;'>Td (Tétanos y Difteria)</h4>", unsafe_allow_html=True)
        st.markdown("""
        * **Criterio Oficial:** Refuerzo cada **10 años** en personas con esquema previo completo.
        * **Sin antecedente verificable:** Esquema primario de 3 dosis (0, 1 y 12 meses).
        * **Dosis y Vía:** 0.5 mL intramuscular en región deltoidea.
        """)

else:
    # --- PANEL PARA POBLACIÓN GENERAL 10 A 59 AÑOS ---
    st.subheader("🎯 Biológicos indicados y Criterios Clínicos")
    st.caption(f"Recomendaciones normativas, grupos blanco, dosificación y compatibilidades ({edad_texto_grande}):")

    # 1. Anti Hepatitis B (>10 años)
    if act_hepb:
        with st.container(border=True):
            st.markdown("<h4 style='color:#E65100;margin:0;'>Vacuna Anti Hepatitis B (Población de 11 años y más / Adultos)</h4>", unsafe_allow_html=True)
            st.caption("Población de 11 años y más sin esquema previo (HB y/o Hexavalente antes de los 5 años)")
            
            col_hb1, col_hb2 = st.columns(2)
            with col_hb1:
                st.markdown("""
                **🔹 Presentación de 20 µg (1.0 mL):**
                * **Número de dosis:** **2 dosis**.
                * **Vía:** Intramuscular (región deltoidea).
                * **Intervalo:** Intervalo mínimo de **4 semanas** entre la primera y segunda dosis.
                """)
            with col_hb2:
                st.markdown("""
                **🔹 Presentación de 10 µg (0.5 mL):**
                * **Número de dosis:** **3 dosis**.
                * **Vía:** Intramuscular (región deltoidea).
                * **Esquema:** **0, 1 y 6 meses** (después de la dosis inicial).
                """)

    # 2. VPH
    if act_vph:
        with st.container(border=True):
            st.markdown("<h4 style='color:#F57F17;margin:0;'>VPH (Virus del Papiloma Humano)</h4>", unsafe_allow_html=True)
            col_vph1, col_vph2 = st.columns(2)
            with col_vph1:
                st.markdown("""
                **🎯 Población Objetivo:**
                * Niñas y niños en **5º de primaria** o de **11 años no escolarizados**.
                * **Dosis:** Única (0.5 mL IM en deltoides).
                """)
            with col_vph2:
                st.markdown("""
                **⚠️ Población en Riesgo (11 a 49 años):**
                * Personas viviendo con VIH y protocolo de violación sexual (9 a 19 años).
                * **Esquema:** 3 dosis (0 - 2 - 6 meses).
                """)
            st.info("💡 **Nota clínica:** No se requiere prueba de VPH previa. La vacunación no sustituye el tamizaje citológico.")

    # 3. Td
    if act_td:
        with st.container(border=True):
            st.markdown("<h4 style='color:#3949AB;margin:0;'>Td (Tétanos, Difteria)</h4>", unsafe_allow_html=True)
            st.markdown("""
            * **Población:** A partir de los 15 años de edad. Refuerzo cada 10 años (o esquema 0, 1, 12 meses sin antecedente).
            * **Dosis:** 0.5 mL intramuscular en región deltoidea.
            """)

    # 4. SR
    if act_sr:
        with st.container(border=True):
            st.markdown("<h4 style='color:#D81B60;margin:0;'>SR (Sarampión y Rubéola)</h4>", unsafe_allow_html=True)
            st.markdown("""
            * Población de 10 a 39 años sin esquema verificable de dos dosis de SRP o SR.
            * **Dosis:** 2 dosis con intervalo de 4 semanas.
            * **Contraindicación:** Embarazo e inmunocompromiso severo.
            """)

    # 5. Influenza por factores de riesgo
    with st.container(border=True):
        st.markdown("<h4 style='color:#AD1457;margin:0;'>Anti Influenza Estacional</h4>", unsafe_allow_html=True)
        st.markdown("""
        * **Población de 10 a 59 años:** Indicada en presencia de factores de riesgo (asma, diabetes, cardiopatías, obesidad mórbida, VIH).
        """)
