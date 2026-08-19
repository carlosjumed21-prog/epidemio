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
        value=date(2020, 1, 1),
        min_value=date(1900, 1, 1),
        max_value=date.today(),
        format="DD/MM/YYYY",
        help="Selecciona o escribe la fecha de nacimiento en formato dd/mm/aaaa"
    )

with col_form2:
    sexo = st.radio(
        "⚧ Sexo:",
        options=["Hombre", "Mujer"],
        horizontal=True,
        help="Selecciona el sexo del paciente"
    )

# --- 2. CÁLCULO DE EDAD ---
hoy = date.today()
dias_vida = (hoy - fecha_nacimiento).days
edad_delta = relativedelta(hoy, fecha_nacimiento)

anios = edad_delta.years
meses = edad_delta.months
dias = edad_delta.days

es_mujer = (sexo == "Mujer")

# --- 3. CONCORDANCIA DE GÉNERO Y CATEGORIZACIÓN ---
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

# --- 4. PALETA DE COLOR SEGÚN GÉNERO ---
if es_mujer:
    # Paleta Rosa
    color_fondo = "#FCE4EC"      # Rosa muy suave
    color_borde = "#D81B60"      # Rosa mexicano / magenta
    color_texto = "#880E4F"      # Rosa profundo
    badge_bg = "#E91E63"
else:
    # Paleta Azul
    color_fondo = "#E3F2FD"      # Azul claro suave
    color_borde = "#1976D2"      # Azul rey
    color_texto = "#0D47A1"      # Azul marino profundo
    badge_bg = "#1565C0"

# --- 5. DISPLAY VISUAL ---
st.markdown("### 🏷️ Perfil Detectado")

tarjeta_html = f"""
<div style="
    background-color: {color_fondo};
    border-left: 8px solid {color_borde};
    border-radius: 8px;
    padding: 16px 20px;
    margin-top: 10px;
    margin-bottom: 20px;
">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <span style="font-size: 1.45rem; font-weight: 700; color: {color_texto};">
                {icono} {tipo_paciente}
            </span>
            <div style="font-size: 0.95rem; color: #37474F; margin-top: 4px;">
                <strong>Sexo:</strong> {sexo} &nbsp;|&nbsp; 
                <strong>Fecha de Nacimiento:</strong> {fecha_nacimiento.strftime('%d/%m/%Y')} &nbsp;|&nbsp; 
                <strong>Edad calculada:</strong> {subcategoria}
            </div>
        </div>
        <div style="
            background-color: {badge_bg};
            color: #FFFFFF;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        ">
            {dias_vida} días de vida
        </div>
    </div>
</div>
"""

st.markdown(tarjeta_html, unsafe_allow_html=True)
