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
        help="Selecciona o escribe la fecha de nacimiento en formato dd/mm/aaaa"
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

# Condición de embarazo: Solo seleccionable si es Mujer >= 10 años
esta_embarazada = False
if es_mujer and anios >= 10:
    esta_embarazada = st.checkbox("🤰 ¿Se encuentra actualmente embarazada?", value=False)

# --- 4. CLASIFICACIÓN CLÍNICA ---
if dias_vida <= 28:
    tipo_paciente = "Recién nacida (Neonata)" if es_mujer else "Recién nacido (Neonato)"
    subcategoria = f"{dias_vida} días de vida"
    icono = "👶"
elif anios < 1:
    tipo_paciente = "Lactante menor"
    subcategoria = f"{meses} meses, {dias} días"
    icono = "🍼"
elif anios < 2:
    tipo_paciente = "Lactante mayor"
    subcategoria = f"1 año, {meses} meses"
    icono = "🍼"
elif 2 <= anios <= 5:
    tipo_paciente = "Preescolar"
    subcategoria = f"{anios} años, {meses} meses"
    icono = "🧸"
elif 6 <= anios <= 11:
    tipo_paciente = "Escolar (Niña)" if es_mujer else "Escolar (Niño)"
    subcategoria = f"{anios} años, {meses} meses"
    icono = "👧" if es_mujer else "👦"
elif 12 <= anios < 18:
    tipo_paciente = "Adolescente"
    subcategoria = f"{anios} años, {meses} meses"
    icono = "👧" if es_mujer else "👦"
elif 18 <= anios < 60:
    tipo_paciente = "Mujer adulta" if es_mujer else "Hombre adulto"
    subcategoria = f"{anios} años cumplidos"
    icono = "👩" if es_mujer else "👨"
else:  # anios >= 60
    tipo_paciente = "Adulta mayor" if es_mujer else "Adulto mayor"
    subcategoria = f"{anios} años cumplidos"
    icono = "👵" if es_mujer else "👴"

if es_mujer:
    color_fondo, color_borde, color_texto, badge_bg = "#FCE4EC", "#D81B60", "#880E4F", "#E91E63"
else:
    color_fondo, color_borde, color_texto, badge_bg = "#E3F2FD", "#1976D2", "#0D47A1", "#1565C0"

# --- 5. DISPLAY DE PERFIL ---
st.markdown("### 🏷️ Perfil Detectado")

embarazo_tag = " &nbsp;|&nbsp; <strong style='color:#C2185B;'>Estado: Embarazada 🤰</strong>" if esta_embarazada else ""

tarjeta_html = (
    f'<div style="background-color:{color_fondo};border-left:8px solid {color_borde};border-radius:8px;padding:16px 20px;margin-top:10px;margin-bottom:25px;">'
    f'<div style="display:flex;justify-content:space-between;align-items:center;">'
    f'<div>'
    f'<span style="font-size:1.45rem;font-weight:700;color:{color_texto};">{icono} {tipo_paciente}</span>'
    f'<div style="font-size:0.95rem;color:#37474F;margin-top:4px;">'
    f'<strong>Sexo:</strong> {sexo} &nbsp;|&nbsp; <strong>Fecha de Nacimiento:</strong> {fecha_nacimiento.strftime("%d/%m/%Y")} &nbsp;|&nbsp; <strong>Edad calculada:</strong> {subcategoria}{embarazo_tag}'
    f'</div>'
    f'</div>'
    f'<div style="background-color:{badge_bg};color:#FFFFFF;padding:6px 14px;border-radius:20px;font-size:0.85rem;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">'
    f'{dias_vida} días de vida'
    f'</div>'
    f'</div>'
    f'</div>'
)
st.markdown(tarjeta_html, unsafe_allow_html=True)

# --- 6. TABLAS DE ESQUEMAS VISUALES ---
if anios < 10:
    st.markdown("### 📋 Esquema Oficial de Vacunación (< 10 años)")
    
    C_BCG = "#D9D2E9"
    C_HEPB = "#F9CB9C"
    C_HEXA = "#CFE2F3"
    C_ROTA = "#D9EAD3"
    C_NEUMO = "#E7F3FE"
    C_INFL = "#FADCE9"
    C_SRP = "#FFF2CC"
    C_DPT = "#E2E3E5"
    C_INACTIVO = "#EEEEEE"

    # Evaluaciones clínicas por edad cumplida
    act_bcg = dias_vida >= 0
    act_hepb = dias_vida >= 0
    act_m2 = (total_meses >= 2) or (dias_vida >= 60)
    act_m4 = (total_meses >= 4) or (dias_vida >= 120)
    act_m6 = (total_meses >= 6) or (dias_vida >= 180)
    act_m7 = (total_meses >= 7) or (dias_vida >= 210)
    act_m12 = (total_meses >= 12) or (anios >= 1)
    act_m18 = (total_meses >= 18) or (anios >= 2) or (anios == 1 and meses >= 6)
    act_m24 = (total_meses >= 24) or (anios >= 2)
    act_m36 = (total_meses >= 36) or (anios >= 3)
    
    # DPT: Activa a partir de los 4 años y hasta los 6 años 11 meses 29 días (< 7 años)
    act_m48 = (total_meses >= 48) or (anios >= 4)
    act_dpt = (4 <= anios <= 6) or (48 <= total_meses < 84)

    act_m59 = (total_meses >= 59) or (anios >= 5)
    act_m72 = (total_meses >= 72) or (anios >= 6)

    # Color dinámico de DPT (48 meses)
    bg_dpt_48 = C_DPT if (act_m48 or act_dpt) else C_INACTIVO

    tabla_pediatrica_html = f"""
<table style="width:100%;border-collapse:separate;border-spacing:4px;font-family:'Segoe UI',sans-serif;margin-top:10px;">
<thead>
<tr><th colspan="7" style="color:#A07248;font-size:1.55rem;font-weight:800;text-align:center;padding-bottom:12px;">Esquema de vacunación para menores de 10 años</th></tr>
<tr>
<th style="background-color:#555;color:#FFF;font-weight:700;font-size:0.95rem;text-align:center;padding:10px;width:18%;border-radius:3px;">Edad</th>
<th colspan="6" style="background-color:#555;color:#FFF;font-weight:700;font-size:0.95rem;text-align:center;padding:10px;border-radius:3px;">Vacunas a aplicar</th>
</tr>
</thead>
<tbody>
<tr>
<td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:10px 6px;border-radius:3px;">Nacimiento</td>
<td colspan="2" style="background-color:{C_BCG if act_bcg else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:#263238;">BCG</td>
<td colspan="4" style="background-color:{C_HEPB if act_hepb else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:#263238;">Hepatitis B</td>
</tr>
<tr>
<td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:10px 6px;border-radius:3px;">2 meses</td>
<td colspan="2" style="background-color:{C_HEXA if act_m2 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:#263238;">Hexavalente acelular*</td>
<td colspan="2" style="background-color:{C_ROTA if act_m2 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:#263238;">Rotavirus</td>
<td colspan="2" style="background-color:{C_NEUMO if act_m2 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:#263238;">Neumococo conjugada 13 valente</td>
</tr>
<tr>
<td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:10px 6px;border-radius:3px;">4 meses</td>
<td colspan="2" style="background-color:{C_HEXA if act_m4 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:#263238;">Hexavalente acelular*</td>
<td colspan="2" style="background-color:{C_ROTA if act_m4 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:#263238;">Rotavirus</td>
<td colspan="2" style="background-color:{C_NEUMO if act_m4 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:#263238;">Neumococo conjugada 13 valente</td>
</tr>
<tr>
<td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:10px 6px;border-radius:3px;">6 meses</td>
<td colspan="2" style="background-color:{C_HEXA if act_m6 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:#263238;">Hexavalente acelular*</td>
<td colspan="4" style="background-color:{C_INFL if act_m6 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:#263238;">Influenza 1a dosis</td>
</tr>
<tr>
<td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:10px 6px;border-radius:3px;">7 meses</td>
<td colspan="6" style="background-color:{C_INFL if act_m7 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:#263238;">Influenza 2a dosis</td>
</tr>
<tr>
<td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:10px 6px;border-radius:3px;">12 meses (1 año)</td>
<td colspan="3" style="background-color:{C_SRP if act_m12 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:#263238;">Triple viral (SRP)**</td>
<td colspan="3" style="background-color:{C_NEUMO if act_m12 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:#263238;">Neumococo conjugada 13 valente</td>
</tr>
<tr>
<td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:10px 6px;border-radius:3px;">18 meses</td>
<td colspan="3" style="background-color:{C_HEXA if act_m18 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:#263238;">Hexavalente acelular*</td>
<td colspan="3" style="background-color:{C_SRP if act_m18 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:#263238;">Triple viral (SRP)** 2a dosis (Nacidos después de 2020)</td>
</tr>
<tr>
<td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:10px 6px;border-radius:3px;">24 meses (2 años)</td>
<td colspan="6" style="background-color:{C_INFL if act_m24 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:#263238;">Influenza refuerzo anual</td>
</tr>
<tr>
<td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:10px 6px;border-radius:3px;">36 meses (3 años)</td>
<td colspan="6" style="background-color:{C_INFL if act_m36 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:#263238;">Influenza refuerzo anual</td>
</tr>
<tr>
<td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:10px 6px;border-radius:3px;">48 meses (4 años)</td>
<td colspan="3" style="background-color:{C_INFL if act_m48 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:#263238;">Influenza refuerzo anual</td>
<td colspan="3" style="background-color:{bg_dpt_48};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:#263238;">DPT</td>
</tr>
<tr>
<td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:10px 6px;border-radius:3px;">59 meses (5 años)</td>
<td colspan="6" style="background-color:{C_INFL if act_m59 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:#263238;">Influenza refuerzo anual</td>
</tr>
<tr>
<td style="background-color:#555;color:#FFF;font-weight:700;font-size:0.88rem;text-align:center;padding:10px 6px;border-radius:3px;">72 meses (6 años)</td>
<td colspan="6" style="background-color:{C_SRP if act_m72 else C_INACTIVO};font-size:0.85rem;font-weight:600;text-align:center;padding:10px 8px;border-radius:3px;color:#263238;">Triple viral (SRP)** 2a dosis (Nacidos antes de 2020)</td>
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
    C_NEUMO_AD = "#DCECF9"
    C_INFL_AD = "#FAD6E6"
    C_INACTIVO = "#EEEEEE"

    es_adulto_mayor = (anios >= 60)

    act_td = (anios >= 15)
    act_sr = (10 <= anios <= 39)
    act_hepb = (anios >= 11)
    act_vph = (10 <= anios <= 49)
    act_tdpa = esta_embarazada or ((15 <= anios <= 49) and es_mujer)
    act_neumo = es_adulto_mayor
    act_infl = True

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
<td style="background-color:{C_TD if act_td else C_INACTIVO};font-size:0.95rem;font-weight:600;text-align:center;padding:12px;border-radius:3px;color:#212121;">Td</td>
<td style="background-color:{C_TD if act_td else C_INACTIVO};font-size:0.95rem;font-weight:500;text-align:center;padding:12px;border-radius:3px;color:#212121;">Tétanos, difteria</td>
</tr>
<tr>
<td style="background-color:{C_SR if act_sr else C_INACTIVO};font-size:0.95rem;font-weight:600;text-align:center;padding:12px;border-radius:3px;color:#212121;">SR</td>
<td style="background-color:{C_SR if act_sr else C_INACTIVO};font-size:0.95rem;font-weight:500;text-align:center;padding:12px;border-radius:3px;color:#212121;">Sarampión, rubéola</td>
</tr>
<tr>
<td style="background-color:{C_HEPB_AD if act_hepb else C_INACTIVO};font-size:0.95rem;font-weight:600;text-align:center;padding:12px;border-radius:3px;color:#212121;">Anti hepatitis B</td>
<td style="background-color:{C_HEPB_AD if act_hepb else C_INACTIVO};font-size:0.95rem;font-weight:500;text-align:center;padding:12px;border-radius:3px;color:#212121;">Hepatitis B</td>
</tr>
<tr>
<td style="background-color:{C_VPH if act_vph else C_INACTIVO};font-size:0.95rem;font-weight:600;text-align:center;padding:12px;border-radius:3px;color:#212121;">VPH</td>
<td style="background-color:{C_VPH if act_vph else C_INACTIVO};font-size:0.95rem;font-weight:500;text-align:center;padding:12px;border-radius:3px;color:#212121;">Infección por Virus del Papiloma Humano</td>
</tr>
<tr>
<td style="background-color:{C_TDPA if act_tdpa else C_INACTIVO};font-size:0.95rem;font-weight:600;text-align:center;padding:12px;border-radius:3px;color:#212121;">Tdpa</td>
<td style="background-color:{C_TDPA if act_tdpa else C_INACTIVO};font-size:0.95rem;font-weight:500;text-align:center;padding:12px;border-radius:3px;color:#212121;">Tétanos, difteria, tos ferina</td>
</tr>
<tr>
<td style="background-color:{C_NEUMO_AD if act_neumo else C_INACTIVO};font-size:0.95rem;font-weight:600;text-align:center;padding:12px;border-radius:3px;color:#212121;">Anti neumocócica polisacárida 23 valente</td>
<td style="background-color:{C_NEUMO_AD if act_neumo else C_INACTIVO};font-size:0.95rem;font-weight:500;text-align:center;padding:12px;border-radius:3px;color:#212121;">Infección por neumococo</td>
</tr>
<tr>
<td style="background-color:{C_INFL_AD if act_infl else C_INACTIVO};font-size:0.95rem;font-weight:600;text-align:center;padding:12px;border-radius:3px;color:#212121;">Anti influenza</td>
<td style="background-color:{C_INFL_AD if act_infl else C_INACTIVO};font-size:0.95rem;font-weight:500;text-align:center;padding:12px;border-radius:3px;color:#212121;">Influenza</td>
</tr>
</tbody>
</table>
"""
    st.markdown(tabla_adultos_html, unsafe_allow_html=True)

# --- 7. CATÁLOGO TÉCNICO PEDIÁTRICO (< 10 AÑOS) ---
CATALOGO_PEDIATRICO = [
    {
        "nombre": "BCG (Bacilo de Calmette-Guérin)",
        "dosis": "Dosis única contra formas graves de Tuberculosis",
        "hito_meses": 0,
        "edad_rec_str": "Al nacer",
        "edad_min_str": "Al nacer",
        "edad_max_str": "< 5 años (Excepcionalmente < 14 años)",
        "intervalo_rec": "No Aplica",
        "intervalo_min": "No Aplica",
        "tecnica_aplicacion": "0.1 mL intradérmica estricta en la región deltoidea del brazo derecho.",
        "simultaneas": ["Hexavalente", "Influenza", "Rotavirus", "Neumococo", "Hepatitis A", "Hepatitis B"],
        "cualquier_intervalo": ["SRP", "SR", "Varicela"],
        "intervalo_especial": [],
        "color": "#6A1B9A"
    },
    {
        "nombre": "Hepatitis B",
        "dosis": "Dosis al nacimiento",
        "hito_meses": 0,
        "edad_rec_str": "Al nacer o a los 7 días de vida",
        "edad_min_str": "Al nacer",
        "edad_max_str": "Preferentemente no después de los 7 días de vida",
        "intervalo_rec": "No Aplica",
        "intervalo_min": "No Aplica",
        "tecnica_aplicacion": "0.5 mL (10 µg) intramuscular en el tercio medio de la cara anterolateral externa del muslo izquierdo.",
        "simultaneas": ["Rotavirus", "Neumococo", "BCG", "Hexavalente (en ausencia de monovalente)"],
        "cualquier_intervalo": [],
        "intervalo_especial": [],
        "color": "#E65100"
    },
    {
        "nombre": "Hexavalente acelular *(DPaT+IPV+HB+Hib)",
        "dosis": "1ª Dosis",
        "hito_meses": 2,
        "edad_rec_str": "2 meses",
        "edad_min_str": "6 semanas",
        "edad_max_str": "< 5 años",
        "intervalo_rec": "8 semanas",
        "intervalo_min": "4 semanas",
        "tecnica_aplicacion": "0.5 mL intramuscular en tercio medio de la cara anterolateral externa del muslo derecho.",
        "simultaneas": ["Influenza", "Rotavirus", "Neumococo", "Hepatitis A"],
        "cualquier_intervalo": ["BCG", "SRP", "SR"],
        "intervalo_especial": [("Varicela", "4 semanas de separación")],
        "color": "#0277BD"
    },
    {
        "nombre": "Antirrotavirus (Rv1)",
        "dosis": "1ª Dosis",
        "hito_meses": 2,
        "edad_rec_str": "2 meses",
        "edad_min_str": "6 semanas",
        "edad_max_str": "7 meses 29 días",
        "intervalo_rec": "8 semanas",
        "intervalo_min": "4 semanas",
        "tecnica_aplicacion": "1.5 mL vía oral.",
        "simultaneas": ["Hexavalente", "Influenza", "Neumococo"],
        "cualquier_intervalo": ["BCG"],
        "intervalo_especial": [],
        "color": "#2E7D32"
    },
    {
        "nombre": "Neumocócica conjugada (VCN)",
        "dosis": "1ª Dosis",
        "hito_meses": 2,
        "edad_rec_str": "2 meses",
        "edad_min_str": "6 semanas",
        "edad_max_str": "59 meses de edad",
        "intervalo_rec": "8 semanas",
        "intervalo_min": "4 a 8 semanas",
        "tecnica_aplicacion": "0.5 mL intramuscular en tercio medio de la cara anterolateral externa del muslo derecho.",
        "simultaneas": ["Hexavalente", "Influenza", "Rotavirus", "Hepatitis A"],
        "cualquier_intervalo": ["BCG", "SRP", "SR", "Varicela"],
        "intervalo_especial": [],
        "color": "#00838F"
    },
    {
        "nombre": "Hexavalente acelular *(DPaT+IPV+HB+Hib)",
        "dosis": "2ª Dosis",
        "hito_meses": 4,
        "edad_rec_str": "4 meses",
        "edad_min_str": "10 semanas",
        "edad_max_str": "< 5 años",
        "intervalo_rec": "8 semanas",
        "intervalo_min": "4 semanas",
        "tecnica_aplicacion": "0.5 mL intramuscular en tercio medio de la cara anterolateral externa del muslo derecho.",
        "simultaneas": ["Influenza", "Rotavirus", "Neumococo", "Hepatitis A"],
        "cualquier_intervalo": ["BCG", "SRP", "SR"],
        "intervalo_especial": [("Varicela", "4 semanas de separación")],
        "color": "#0277BD"
    },
    {
        "nombre": "Antirrotavirus (Rv1)",
        "dosis": "2ª Dosis",
        "hito_meses": 4,
        "edad_rec_str": "4 meses",
        "edad_min_str": "10 semanas",
        "edad_max_str": "7 meses 29 días",
        "intervalo_rec": "No Aplica",
        "intervalo_min": "No Aplica",
        "tecnica_aplicacion": "1.5 mL vía oral.",
        "simultaneas": ["Hexavalente", "Influenza", "Neumococo"],
        "cualquier_intervalo": ["BCG"],
        "intervalo_especial": [],
        "color": "#2E7D32"
    },
    {
        "nombre": "Neumocócica conjugada (VCN)",
        "dosis": "2ª Dosis",
        "hito_meses": 4,
        "edad_rec_str": "4 meses",
        "edad_min_str": "10 semanas",
        "edad_max_str": "59 meses de edad",
        "intervalo_rec": "8 meses",
        "intervalo_min": "8 semanas",
        "tecnica_aplicacion": "0.5 mL intramuscular en tercio medio de la cara anterolateral externa del muslo derecho.",
        "simultaneas": ["Hexavalente", "Influenza", "Rotavirus", "Hepatitis A"],
        "cualquier_intervalo": ["BCG", "SRP", "SR", "Varicela"],
        "intervalo_especial": [],
        "color": "#00838F"
    },
    {
        "nombre": "Hexavalente acelular *(DPaT+IPV+HB+Hib)",
        "dosis": "3ª Dosis",
        "hito_meses": 6,
        "edad_rec_str": "6 meses",
        "edad_min_str": "14 semanas",
        "edad_max_str": "< 5 años",
        "intervalo_rec": "12 semanas",
        "intervalo_min": "6 semanas",
        "tecnica_aplicacion": "0.5 mL intramuscular en tercio medio de la cara anterolateral externa del muslo derecho.",
        "simultaneas": ["Influenza", "Rotavirus", "Neumococo", "Hepatitis A"],
        "cualquier_intervalo": ["BCG", "SRP", "SR"],
        "intervalo_especial": [("Varicela", "4 semanas de separación")],
        "color": "#0277BD"
    },
    {
        "nombre": "Influenza Estacional",
        "dosis": "1ª Dosis (Primovacunación)",
        "hito_meses": 6,
        "edad_rec_str": "6 meses",
        "edad_min_str": "6 meses",
        "edad_max_str": "59 meses",
        "intervalo_rec": "4 semanas",
        "intervalo_min": "4 semanas",
        "tecnica_aplicacion": "0.25 mL intramuscular en tercio medio de la cara anterolateral externa del muslo izquierdo.",
        "simultaneas": ["Hexavalente", "Rotavirus", "Neumococo", "Hepatitis A", "COVID-19"],
        "cualquier_intervalo": ["BCG", "SRP", "SR", "Varicela"],
        "intervalo_especial": [],
        "color": "#AD1457"
    },
    {
        "nombre": "Influenza Estacional",
        "dosis": "2ª Dosis (Primovacunación)",
        "hito_meses": 7,
        "edad_rec_str": "7 meses",
        "edad_min_str": "7 meses",
        "edad_max_str": "59 meses",
        "intervalo_rec": "Anual",
        "intervalo_min": "4 semanas",
        "tecnica_aplicacion": "0.25 mL intramuscular en muslo izquierdo.",
        "simultaneas": ["Hexavalente", "Rotavirus", "Neumococo", "Hepatitis A", "COVID-19"],
        "cualquier_intervalo": ["BCG", "SRP", "SR", "Varicela"],
        "intervalo_especial": [],
        "color": "#AD1457"
    },
    {
        "nombre": "Triple Viral (SRP)",
        "dosis": "1ª Dosis (Sarampión, rubéola, parotiditis)",
        "hito_meses": 12,
        "edad_rec_str": "12 meses (1 año)",
        "edad_min_str": "12 meses",
        "edad_max_str": "Menores de 10 años",
        "intervalo_rec": "5 años (o a los 18 meses si nació post-2020)",
        "intervalo_min": "4 semanas",
        "tecnica_aplicacion": "0.5 mL subcutánea en el área deltoidea del brazo izquierdo.",
        "simultaneas": ["Influenza", "Neumococo", "Hepatitis A", "BCG", "Hexavalente"],
        "cualquier_intervalo": [],
        "intervalo_especial": [("SR", "Intervalo de 4 semanas")],
        "color": "#E65100"
    },
    {
        "nombre": "Neumocócica conjugada (VCN)",
        "dosis": "3ª Dosis (Refuerzo)",
        "hito_meses": 12,
        "edad_rec_str": "12 meses (1 año)",
        "edad_min_str": "12 semanas",
        "edad_max_str": "59 meses de edad",
        "intervalo_rec": "No Aplica",
        "intervalo_min": "No Aplica",
        "tecnica_aplicacion": "0.5 mL intramuscular en tercio medio de la cara anterolateral externa del muslo derecho.",
        "simultaneas": ["Hexavalente", "Influenza", "Rotavirus", "Hepatitis A"],
        "cualquier_intervalo": ["BCG", "SRP", "SR", "Varicela"],
        "intervalo_especial": [],
        "color": "#00838F"
    },
    {
        "nombre": "Hexavalente acelular *(DPaT+IPV+HB+Hib)",
        "dosis": "4ª Dosis (Refuerzo)",
        "hito_meses": 18,
        "edad_rec_str": "18 meses",
        "edad_min_str": "12 meses",
        "edad_max_str": "< 5 años",
        "intervalo_rec": "No Aplica",
        "intervalo_min": "No Aplica",
        "tecnica_aplicacion": "0.5 mL intramuscular en tercio medio de la cara anterolateral externa del muslo izquierdo o deltoides izquierdo.",
        "simultaneas": ["Influenza", "Rotavirus", "Neumococo", "Hepatitis A"],
        "cualquier_intervalo": ["BCG", "SRP", "SR"],
        "intervalo_especial": [("Varicela", "4 semanas de separación")],
        "color": "#0277BD"
    },
    {
        "nombre": "Triple Viral (SRP)",
        "dosis": "2ª Dosis (Nacidos después de 2020)",
        "hito_meses": 18,
        "edad_rec_str": "18 meses",
        "edad_min_str": "18 meses",
        "edad_max_str": "Menores de 10 años",
        "intervalo_rec": "No Aplica",
        "intervalo_min": "No Aplica",
        "tecnica_aplicacion": "0.5 mL subcutánea en deltoides izquierdo.",
        "simultaneas": ["Influenza", "Neumococo", "Hepatitis A", "BCG", "Hexavalente"],
        "cualquier_intervalo": [],
        "intervalo_especial": [("SR", "Intervalo de 4 semanas")],
        "color": "#E65100"
    },
    {
        "nombre": "Influenza Estacional",
        "dosis": "Refuerzo Anual (2 años)",
        "hito_meses": 24,
        "edad_rec_str": "24 meses (2 años)",
        "edad_min_str": "24 meses",
        "edad_max_str": "59 meses",
        "intervalo_rec": "Anual",
        "intervalo_min": "4 semanas",
        "tecnica_aplicacion": "0.25 mL intramuscular en deltoides izquierdo.",
        "simultaneas": ["Neumococo", "Hepatitis A", "COVID-19"],
        "cualquier_intervalo": ["SRP", "SR", "Varicela"],
        "intervalo_especial": [],
        "color": "#AD1457"
    },
    {
        "nombre": "Influenza Estacional",
        "dosis": "Refuerzo Anual (3 años)",
        "hito_meses": 36,
        "edad_rec_str": "36 meses (3 años)",
        "edad_min_str": "36 meses",
        "edad_max_str": "59 meses",
        "intervalo_rec": "Anual",
        "intervalo_min": "4 semanas",
        "tecnica_aplicacion": "0.5 mL intramuscular en deltoides izquierdo.",
        "simultaneas": ["Neumococo", "Hepatitis A", "COVID-19"],
        "cualquier_intervalo": ["SRP", "SR", "Varicela"],
        "intervalo_especial": [],
        "color": "#AD1457"
    },
    {
        "nombre": "Influenza Estacional",
        "dosis": "Refuerzo Anual (4 años)",
        "hito_meses": 48,
        "edad_rec_str": "48 meses (4 años)",
        "edad_min_str": "48 meses",
        "edad_max_str": "59 meses",
        "intervalo_rec": "Anual",
        "intervalo_min": "4 semanas",
        "tecnica_aplicacion": "0.5 mL intramuscular en deltoides izquierdo.",
        "simultaneas": ["DPT", "Neumococo", "COVID-19"],
        "cualquier_intervalo": ["SRP", "SR"],
        "intervalo_especial": [],
        "color": "#AD1457"
    },
    {
        "nombre": "DPT (Difteria, Tos ferina, Tétanos)",
        "dosis": "Refuerzo a los 4 años",
        "hito_meses": 48,
        "edad_rec_str": "4 años (48 meses)",
        "edad_min_str": "4 años",
        "edad_max_str": "6 años, 11 meses y 29 días (< 7 años)",
        "intervalo_rec": "Posterior al esquema primario de Hexavalente",
        "intervalo_min": "6 semanas (posteriores a la 4ª dosis de Hexavalente)",
        "tecnica_aplicacion": "Posterior a la aplicación del esquema primario con la vacuna hexavalente acelular, se aplica una dosis de 0.5 mL de la vacuna DPT, vía intramuscular en la región deltoidea o tricipital del brazo izquierdo, a los 4 años de edad. En aquellos casos en los que no se reciba a los 4 años, la edad de aplicación no debe sobrepasar los 6 años, 11 meses y 29 días.",
        "simultaneas": ["Influenza", "Neumococo", "Hepatitis A"],
        "cualquier_intervalo": ["SRP", "SR"],
        "intervalo_especial": [],
        "color": "#546E7A"
    },
    {
        "nombre": "Influenza Estacional",
        "dosis": "Refuerzo Anual (5 años)",
        "hito_meses": 59,
        "edad_rec_str": "59 meses (5 años)",
        "edad_min_str": "59 meses",
        "edad_max_str": "59 meses",
        "intervalo_rec": "Anual",
        "intervalo_min": "4 semanas",
        "tecnica_aplicacion": "0.5 mL intramuscular en deltoides izquierdo.",
        "simultaneas": ["COVID-19"],
        "cualquier_intervalo": ["SRP", "SR"],
        "intervalo_especial": [],
        "color": "#AD1457"
    },
    {
        "nombre": "Triple Viral (SRP)",
        "dosis": "2ª Dosis (Nacidos antes de 2020)",
        "hito_meses": 72,
        "edad_rec_str": "72 meses (6 años)",
        "edad_min_str": "6 años",
        "edad_max_str": "Menores de 10 años",
        "intervalo_rec": "No Aplica",
        "intervalo_min": "No Aplica",
        "tecnica_aplicacion": "0.5 mL subcutánea en deltoides izquierdo.",
        "simultaneas": ["Influenza", "COVID-19"],
        "cualquier_intervalo": [],
        "intervalo_especial": [("SR", "Intervalo de 4 semanas")],
        "color": "#E65100"
    }
]

# --- 8. PANEL INFERIOR DINÁMICO ---
st.divider()

if anios < 10:
    hitos_disponibles = [0, 2, 4, 6, 7, 12, 18, 24, 36, 48, 59, 72]
    
    if dias_vida <= 28:
        hito_objetivo = 0
    elif anios in [4, 5]:
        # A los 4 y 5 años muestra las vacunas correspondientes (incluyendo DPT e Influenza)
        hito_objetivo = 48 if anios == 4 else 59
    elif anios >= 6:
        hito_objetivo = 72
    else:
        hitos_pendientes = [h for h in hitos_disponibles if h >= total_meses]
        hito_objetivo = hitos_pendientes[0] if hitos_pendientes else 72

    # Obtener vacunas de la etapa seleccionada
    vacunas_a_mostrar = [v for v in CATALOGO_PEDIATRICO if v["hito_meses"] == hito_objetivo]
    
    # Si el paciente tiene entre 4 y 6 años y DPT no está en la lista inmediata, se añade como biológico aplicable
    dpt_obj = next((v for v in CATALOGO_PEDIATRICO if "DPT" in v["nombre"]), None)
    if (4 <= anios <= 6) and dpt_obj and (dpt_obj not in vacunas_a_mostrar):
        vacunas_a_mostrar.append(dpt_obj)

    texto_hito = vacunas_a_mostrar[0]["edad_rec_str"] if vacunas_a_mostrar else "Etapa actual"
    
    st.subheader(f"🎯 Vacunas a aplicar en la etapa actual / siguiente ({texto_hito})")
    st.caption(f"Sugerencias técnicas y compatibilidades para el paciente con edad calculada de {subcategoria}:")

    for v in vacunas_a_mostrar:
        with st.container(border=True):
            col_t1, col_t2 = st.columns([3, 1])
            with col_t1:
                st.markdown(f"<h4 style='color:{v['color']};margin:0;'>{v['nombre']} — <span style='color:#37474F;font-weight:500;'>{v['dosis']}</span></h4>", unsafe_allow_html=True)
            with col_t2:
                st.markdown(f"<div style='text-align:right;'><span style='background-color:#ECEFF1;color:#37474F;padding:4px 10px;border-radius:12px;font-size:0.8rem;font-weight:600;'>Recomendada: {v['edad_rec_str']}</span></div>", unsafe_allow_html=True)

            st.write("")
            
            if "tecnica_aplicacion" in v:
                st.markdown(f"**📌 Indicación y Vía de Aplicación:** {v['tecnica_aplicacion']}")
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f"**🔹 Edad mínima:**<br><span style='color:#0D47A1;'>{v['edad_min_str']}</span>", unsafe_allow_html=True)
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
                badges_html.append(f"<span style='background-color:#E8F5E9;color:#1B5E20;border:1px solid #A5D6A7;padding:3px 8px;border-radius:6px;font-size:0.8rem;font-weight:600;margin-right:5px;display:inline-block;margin-bottom:4px;'>💉 {sim}</span>")
            for ci in v["cualquier_intervalo"]:
                badges_html.append(f"<span style='background-color:#E0F2F1;color:#004D40;border:1px solid #80CBC4;padding:3px 8px;border-radius:6px;font-size:0.8rem;font-weight:600;margin-right:5px;display:inline-block;margin-bottom:4px;'>⏱️ {ci} (Cualquier intervalo)</span>")
            for ie in v["intervalo_especial"]:
                badges_html.append(f"<span style='background-color:#FFF3E0;color:#BF360C;border:1px solid #FFCC80;padding:3px 8px;border-radius:6px;font-size:0.8rem;font-weight:600;margin-right:5px;display:inline-block;margin-bottom:4px;'>⚠️ {ie[0]}: {ie[1]}</span>")
            
            st.markdown("".join(badges_html), unsafe_allow_html=True)

elif es_adulto_mayor:
    # --- PANEL EXCLUSIVO PARA ADULTO MAYOR (>= 60 AÑOS) ---
    st.subheader(f"🎯 Biológicos Prioritarios para {tipo_paciente} ({subcategoria})")
    st.caption("Lineamientos de vacunación del adulto mayor en México:")

    # 1. Neumococo 23V
    with st.container(border=True):
        st.markdown("<h4 style='color:#00838F;margin:0;'>Anti Neumocócica Polisacárida 23 Valente</h4>", unsafe_allow_html=True)
        st.markdown("""
        * **Criterio Oficial:**
          * **Población de 65 años y más:** Aplicación universal (Dosis única).
          * **Población de 60 a 64 años con factores de riesgo:** Pacientes con diabetes mellitus, EPOC, cardiopatías, nefropatías, hepatopatías crónicas o tabaquismo.
        * **Dosis y Vía:** 0.5 mL intramuscular en región deltoidea.
        * **Revacunación:** Dosis única de revacunación a los 5 años únicamente en personas con asplenia anatómica/funcional o inmunocomprometidas.
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
    # --- PANEL PARA POBLACIÓN 10 A 59 AÑOS ---
    st.subheader(f"🎯 Biológicos indicados y Criterios Clínicos ({subcategoria})")
    st.caption("Recomendaciones normativas, grupos blanco, dosificación y compatibilidades:")

    # 0. VSR (EXCLUSIVO EMBARAZO)
    if esta_embarazada:
        with st.container(border=True):
            st.markdown("<h4 style='color:#00897B;margin:0;'>Vacuna contra el Virus Sincitial Respiratorio (VSR)</h4>", unsafe_allow_html=True)
            st.caption("Lineamiento Oficial de Vacunación Materna")
            st.markdown("""
            * **Población blanco:** Personas embarazadas entre las **semanas 32 a 36 de gestación**.
            * **Dosis y Vía:** Dosis única de **0.5 mL**, vía intramuscular en la región deltoidea del brazo de menor uso (no dominante).
            * **Revacunación:** **No se requiere revacunación**.
            * **Objetivo clínico:** Protección del lactante contra bronquiolitis y neumonía grave por VSR durante los primeros 6 meses de vida mediante anticuerpos maternos.
            """)

    # 1. Anti Hepatitis B (>10 años)
    if act_hepb:
        with st.container(border=True):
            st.markdown("<h4 style='color:#E65100;margin:0;'>Vacuna Anti Hepatitis B (Población $\ge$ 11 años y Adultos)</h4>", unsafe_allow_html=True)
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
    if act_vph and not esta_embarazada:
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

    # 3. Td / Tdpa
    if act_td or act_tdpa:
        with st.container(border=True):
            st.markdown("<h4 style='color:#3949AB;margin:0;'>Td / Tdpa (Tétanos, Difteria, Tos Ferina)</h4>", unsafe_allow_html=True)
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                st.markdown("""
                **🔹 Td:**
                * A partir de los 15 años de edad. Refuerzo cada 10 años (o esquema 0, 1, 12 meses sin antecedente).
                """)
            with col_t2:
                st.markdown("""
                **🔹 Tdpa:**
                * **Mujeres embarazadas:** En cada embarazo a partir de la **semana 20 de gestación**.
                """)

    # 4. SR
    if act_sr and not esta_embarazada:
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
        * **Población de 10 a 59 años:** Indicada en presencia de factores de riesgo (embarazo, asma, diabetes, cardiopatías, obesidad mórbida, VIH, personal de salud).
        """)
