import streamlit as st
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

st.set_page_config(page_title="Esquemas de Vacunación 2026", page_icon="💉", layout="wide")

st.title("💉 Esquemas de Vacunación 2026")
st.caption("Evaluación etaria y perfil de vacunación epidemiológica.")

st.divider()

# --- 1. ENTRADA DE DATOS DEL PACIENTE ---
col_form1, col_form2 = st.columns([1, 1])

with col_form1:
    # Selector de fecha con formato visual DD/MM/AAAA
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
        help="Selecciona el sexo biológico del paciente"
    )

# --- 2. CÁLCULO DE EDAD Y CLASIFICACIÓN EPIDEMIOLÓGICA ---
hoy = date.today()

# Diferencia exacta en días y en desglose año/mes/día
dias_vida = (hoy - fecha_nacimiento).days
edad_delta = relativedelta(hoy, fecha_nacimiento)

anios = edad_delta.years
meses = edad_delta.months
dias = edad_delta.days

# Clasificación según los rangos definidos
if dias_vida <= 28:
    tipo_paciente = "Recién nacido (Neonato)"
    subcategoria = f"{dias_vida} días de vida"
    color_fondo = "#E3F2FD"      # Azul claro
    color_borde = "#1976D2"      # Azul marino
    color_texto = "#0D47A1"
    icono = "👶"

elif anios < 1:
    tipo_paciente = "Lactante (Lactante Menor)"
    subcategoria = f"{meses} meses, {dias} días"
    color_fondo = "#E0F7FA"      # Cyan suave
    color_borde = "#0097A7"      # Cyan oscuro
    color_texto = "#006064"
    icono = "🍼"

elif anios < 2:
    tipo_paciente = "Lactante (Lactante Mayor)"
    subcategoria = f"1 año, {meses} meses"
    color_fondo = "#E0F2F1"      # Teal suave
    color_borde = "#00796B"      # Teal oscuro
    color_texto = "#004D40"
    icono = "🍼"

elif 2 <= anios <= 5:
    tipo_paciente = "Preescolar"
    subcategoria = f"{anios} años, {meses} meses"
    color_fondo = "#FFF9C4"      # Amarillo suave
    color_borde = "#FBC02D"      # Amarillo oscuro
    color_texto = "#F57F17"
    icono = "🧸"

elif 6 <= anios <= 11:
    tipo_paciente = "Escolar (Niño)"
    subcategoria = f"{anios} años, {meses} meses"
    color_fondo = "#F1F8E9"      # Verde claro suave
    color_borde = "#689F38"      # Verde olivo
    color_texto = "#33691E"
    icono = "🎒"

elif 12 <= anios < 18:
    tipo_paciente = "Adolescente"
    subcategoria = f"{anios} años, {meses} meses"
    color_fondo = "#EDE7F6"      # Púrpura suave
    color_borde = "#512DA8"      # Púrpura intenso
    color_texto = "#311B92"
    icono = "🎧"

elif 18 <= anios < 60:
    tipo_paciente = "Adulto"
    subcategoria = f"{anios} años cumplidos"
    color_fondo = "#ECEFF1"      # Gris azulado neutro
    color_borde = "#455A64"      # Gris azulado oscuro
    color_texto = "#263238"
    icono = "🧑"

else: # anios >= 60
    tipo_paciente = "Adulto Mayor"
    subcategoria = f"{anios} años cumplidos"
    color_fondo = "#FFF3E0"      # Naranja/Ámbar suave
    color_borde = "#E64A19"      # Naranja quemado
    color_texto = "#BF360C"
    icono = "🧓"

# --- 3. DISPLAY VISUAL DEL TIPO DE PACIENTE ---
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
            <span style="font-size: 1.5rem; font-weight: 700; color: {color_texto};">
                {icono} {tipo_paciente}
            </span>
            <div style="font-size: 0.95rem; color: #424242; margin-top: 4px;">
                <strong>Sexo:</strong> {sexo} &nbsp;|&nbsp; 
                <strong>Fecha Nacimiento:</strong> {fecha_nacimiento.strftime('%d/%m/%Y')} &nbsp;|&nbsp; 
                <strong>Edad calculada:</strong> {subcategoria}
            </div>
        </div>
        <div style="
            background-color: {color_borde};
            color: #FFFFFF;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        ">
            {dias_vida} días totales
        </div>
    </div>
</div>
"""

st.markdown(tarjeta_html, unsafe_allow_html=True)
