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
        value=date(2025, 12, 1),
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

# --- 2. CÁLCULO DE EDAD EXACTA ---
hoy = date.today()
dias_vida = (hoy - fecha_nacimiento).days
edad_delta = relativedelta(hoy, fecha_nacimiento)

anios = edad_delta.years
meses = edad_delta.months
dias = edad_delta.days

total_meses = (anios * 12) + meses
es_mujer = (sexo == "Mujer")

# --- 3. CLASIFICACIÓN CLÍNICA ---
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
else:
    tipo_paciente = "Adulta mayor" if es_mujer else "Adulto mayor"
    subcategoria = f"{anios} años cumplidos"
    icono = "👵" if es_mujer else "👴"

if es_mujer:
    color_fondo, color_borde, color_texto, badge_bg = "#FCE4EC", "#D81B60", "#880E4F", "#E91E63"
else:
    color_fondo, color_borde, color_texto, badge_bg = "#E3F2FD", "#1976D2", "#0D47A1", "#1565C0"

# --- 4. DISPLAY DE PERFIL ---
st.markdown("### 🏷️ Perfil Detectado")

tarjeta_html = f"""
<div style="background-color: {color_fondo}; border-left: 8px solid {color_borde}; border-radius: 8px; padding: 16px 20px; margin-top: 10px; margin-bottom: 25px;">
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
        <div style="background-color: {badge_bg}; color: #FFFFFF; padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
            {dias_vida} días de vida
        </div>
    </div>
</div>
"""
st.markdown(tarjeta_html, unsafe_allow_html=True)

# --- 5. ESQUEMAS VISUALES CONDICIONALES ---
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

    act_bcg = dias_vida >= 0
    act_hepb = dias_vida >= 0
    act_m2 = total_meses >= 2
    act_m4 = total_meses >= 4
    act_m6 = total_meses >= 6
    act_m7 = total_meses >= 7
    act_m12 = total_meses >= 12
    act_m18 = total_meses >= 18
    act_m24 = total_meses >= 24
    act_m36 = total_meses >= 36
    act_m48 = total_meses >= 48
    act_m59 = total_meses >= 59
    act_m72 = total_meses >= 72

    tabla_pediatrica_html = f"""
    <style>
        .tabla-esquema {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 4px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin-top: 10px;
        }}
        .th-titulo {{
            color: #A07248;
            font-size: 1.55rem;
            font-weight: 800;
            text-align: center;
            padding-bottom: 12px;
        }}
        .th-col-edad {{
            background-color: #555555;
            color: #FFFFFF;
            font-weight: 700;
            font-size: 0.95rem;
            text-align: center;
            padding: 10px;
            width: 18%;
            border-radius: 3px;
        }}
        .th-col-vacunas {{
            background-color: #555555;
            color: #FFFFFF;
            font-weight: 700;
            font-size: 0.95rem;
            text-align: center;
            padding: 10px;
            border-radius: 3px;
        }}
        .celda-edad {{
            background-color: #555555;
            color: #FFFFFF;
            font-weight: 700;
            font-size: 0.88rem;
            text-align: center;
            padding: 10px 6px;
            border-radius: 3px;
        }}
        .celda-vacuna {{
            font-size: 0.85rem;
            font-weight: 600;
            text-align: center;
            padding: 10px 8px;
            border-radius: 3px;
            color: #263238;
        }}
    </style>

    <table class="tabla-esquema">
        <thead>
            <tr>
                <th colspan="7" class="th-titulo">Esquema de vacunación para menores de 10 años</th>
            </tr>
            <tr>
                <th class="th-col-edad">Edad</th>
                <th colspan="6" class="th-col-vacunas">Vacunas a aplicar</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td class="celda-edad">Nacimiento</td>
                <td colspan="2" class="celda-vacuna" style="background-color: {C_BCG if act_bcg else C_INACTIVO};">BCG</td>
                <td colspan="4" class="celda-vacuna" style="background-color: {C_HEPB if act_hepb else C_INACTIVO};">Hepatitis B</td>
            </tr>
            <tr>
                <td class="celda-edad">2 meses</td>
                <td colspan="2" class="celda-vacuna" style="background-color: {C_HEXA if act_m2 else C_INACTIVO};">Hexavalente acelular*</td>
                <td colspan="2" class="celda-vacuna" style="background-color: {C_ROTA if act_m2 else C_INACTIVO};">Rotavirus</td>
                <td colspan="2" class="celda-vacuna" style="background-color: {C_NEUMO if act_m2 else C_INACTIVO};">Neumococo conjugada 13 valente</td>
            </tr>
            <tr>
                <td class="celda-edad">4 meses</td>
                <td colspan="2" class="celda-vacuna" style="background-color: {C_HEXA if act_m4 else C_INACTIVO};">Hexavalente acelular*</td>
                <td colspan="2" class="celda-vacuna" style="background-color: {C_ROTA if act_m4 else C_INACTIVO};">Rotavirus</td>
                <td colspan="2" class="celda-vacuna" style="background-color: {C_NEUMO if act_m4 else C_INACTIVO};">Neumococo conjugada 13 valente</td>
            </tr>
            <tr>
                <td class="celda-edad">6 meses</td>
                <td colspan="2" class="celda-vacuna" style="background-color: {C_HEXA if act_m6 else C_INACTIVO};">Hexavalente acelular*</td>
                <td colspan="4" class="celda-vacuna" style="background-color: {C_INFL if act_m6 else C_INACTIVO};">Influenza 1a dosis</td>
            </tr>
            <tr>
                <td class="celda-edad">7 meses</td>
                <td colspan="6" class="celda-vacuna" style="background-color: {C_INFL if act_m7 else C_INACTIVO};">Influenza 2a dosis</td>
            </tr>
            <tr>
                <td class="celda-edad">12 meses (1 año)</td>
                <td colspan="3" class="celda-vacuna" style="background-color: {C_SRP if act_m12 else C_INACTIVO};">Triple viral (SRP)**</td>
                <td colspan="3" class="celda-vacuna" style="background-color: {C_NEUMO if act_m12 else C_INACTIVO};">Neumococo conjugada 13 valente</td>
            </tr>
            <tr>
                <td class="celda-edad">18 meses</td>
                <td colspan="3" class="celda-vacuna" style="background-color: {C_HEXA if act_m18 else C_INACTIVO};">Hexavalente acelular*</td>
                <td colspan="3" class="celda-vacuna" style="background-color: {C_SRP if act_m18 else C_INACTIVO};">Triple viral (SRP)** 2a dosis (Nacidos después de 2020)</td>
            </tr>
            <tr>
                <td class="celda-edad">24 meses (2 años)</td>
                <td colspan="6" class="celda-vacuna" style="background-color: {C_INFL if act_m24 else C_INACTIVO};">Influenza refuerzo anual</td>
            </tr>
            <tr>
                <td class="celda-edad">36 meses (3 años)</td>
                <td colspan="6" class="celda-vacuna" style="background-color: {C_INFL if act_m36 else C_INACTIVO};">Influenza refuerzo anual</td>
            </tr>
            <tr>
                <td class="celda-edad">48 meses (4 años)</td>
                <td colspan="3" class="celda-vacuna" style="background-color: {C_INFL if act_m48 else C_INACTIVO};">Influenza refuerzo anual</td>
                <td colspan="3" class="celda-vacuna" style="background-color: {C_DPT if act_m48 else C_INACTIVO};">DPT</td>
            </tr>
            <tr>
                <td class="celda-edad">59 meses (5 años)</td>
                <td colspan="6" class="celda-vacuna" style="background-color: {C_INFL if act_m59 else C_INACTIVO};">Influenza refuerzo anual</td>
            </tr>
            <tr>
                <td class="celda-edad">72 meses (6 años)</td>
                <td colspan="6" class="celda-vacuna" style="background-color: {C_SRP if act_m72 else C_INACTIVO};">Triple viral (SRP)** 2a dosis (Nacidos antes de 2020)</td>
            </tr>
        </tbody>
    </table>
    """
    st.markdown(tabla_pediatrica_html, unsafe_allow_html=True)

else:
    # --- ESQUEMA >= 10 AÑOS ---
    tabla_adultos_html = """
    <style>
        .tabla-adultos {
            width: 100%;
            border-collapse: separate;
            border-spacing: 4px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin-top: 10px;
        }
        .th-titulo-adulto {
            color: #A07248;
            font-size: 1.55rem;
            font-weight: 800;
            text-align: center;
            padding-bottom: 12px;
        }
        .th-encabezado-adulto {
            background-color: #555555;
            color: #FFFFFF;
            font-weight: 700;
            font-size: 1.05rem;
            text-align: center;
            padding: 12px;
            border-radius: 3px;
        }
        .celda-vacuna-adulto {
            font-size: 0.95rem;
            font-weight: 600;
            text-align: center;
            padding: 12px 14px;
            border-radius: 3px;
            color: #212121;
            width: 45%;
        }
        .celda-prevencion {
            font-size: 0.95rem;
            font-weight: 500;
            text-align: center;
            padding: 12px 14px;
            border-radius: 3px;
            color: #212121;
            width: 55%;
        }
        .color-fila-td { background-color: #D2D4EA; }
        .color-fila-sr { background-color: #F8E5DB; }
        .color-fila-hepb { background-color: #F9CCA7; }
        .color-fila-vph { background-color: #FEF9BE; }
        .color-fila-tdpa { background-color: #DCEBD6; }
        .color-fila-neumo { background-color: #DCECF9; }
        .color-fila-influenza { background-color: #FAD6E6; }
    </style>

    <table class="tabla-adultos">
        <thead>
            <tr>
                <th colspan="2" class="th-titulo-adulto">
                    Esquema de vacunación para población de 10 a 19 años y adultos a partir de los 20 años
                </th>
            </tr>
            <tr>
                <th class="th-encabezado-adulto">Vacunas</th>
                <th class="th-encabezado-adulto">Enfermedad que previene</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td class="celda-vacuna-adulto color-fila-td">Td</td>
                <td class="celda-prevencion color-fila-td">Tétanos, difteria</td>
            </tr>
            <tr>
                <td class="celda-vacuna-adulto color-fila-sr">SR</td>
                <td class="celda-prevencion color-fila-sr">Sarampión, rubéola</td>
            </tr>
            <tr>
                <td class="celda-vacuna-adulto color-fila-hepb">Anti hepatitis B</td>
                <td class="celda-prevencion color-fila-hepb">Hepatitis B</td>
            </tr>
            <tr>
                <td class="celda-vacuna-adulto color-fila-vph">VPH</td>
                <td class="celda-prevencion color-fila-vph">Infección por Virus del Papiloma Humano</td>
            </tr>
            <tr>
                <td class="celda-vacuna-adulto color-fila-tdpa">Tdpa</td>
                <td class="celda-prevencion color-fila-tdpa">Tétanos, difteria, tos ferina</td>
            </tr>
            <tr>
                <td class="celda-vacuna-adulto color-fila-neumo">Anti neumocócica polisacárida 23 valente</td>
                <td class="celda-prevencion color-fila-neumo">Infección por neumococo</td>
            </tr>
            <tr>
                <td class="celda-vacuna-adulto color-fila-influenza">Anti influenza</td>
                <td class="celda-prevencion color-fila-influenza">Influenza</td>
            </tr>
        </tbody>
    </table>
    """
    st.markdown(tabla_adultos_html, unsafe_allow_html=True)

# --- 6. MOTOR DE DECISIÓN CLÍNICA Y COADMINISTRACIÓN VISUAL ---
st.divider()
st.subheader("🎯 Evaluación Epidemiológica: Biológicos Correspondientes")

# Base de datos estructurada con desglose de compatibilidades
CATALOGO_CUADRO_71 = [
    {
        "nombre": "BCG (Bacilo de Calmette-Guérin)",
        "dosis": "Dosis única contra formas graves de Tuberculosis",
        "edad_rec_meses": 0,
        "edad_rec_str": "Al nacer",
        "edad_min_dias": 0,
        "edad_min_str": "Al nacer",
        "edad_max_meses": 59,
        "edad_max_str": "< 5 años (Excepcionalmente < 14 años)",
        "intervalo_rec": "No Aplica",
        "intervalo_min": "No Aplica",
        "simultaneas": ["Hexavalente", "Influenza", "Rotavirus", "Neumococo", "Hepatitis A", "Hepatitis B"],
        "cualquier_intervalo": ["SRP", "SR", "Varicela"],
        "intervalo_especial": [],
        "color": "#6A1B9A"
    },
    {
        "nombre": "Hepatitis B",
        "dosis": "Dosis al nacimiento",
        "edad_rec_meses": 0,
        "edad_rec_str": "Al nacer o a los 7 días de vida",
        "edad_min_dias": 0,
        "edad_min_str": "Al nacer",
        "edad_max_dias": 7,
        "edad_max_meses": 0.25,
        "edad_max_str": "Preferentemente no después de los 7 días de vida",
        "intervalo_rec": "No Aplica",
        "intervalo_min": "No Aplica",
        "simultaneas": ["Rotavirus", "Neumococo", "BCG", "Hexavalente (en ausencia de monovalente)"],
        "cualquier_intervalo": [],
        "intervalo_especial": [],
        "color": "#E65100"
    },
    {
        "nombre": "Hexavalente acelular *(DPaT+IPV+HB+Hib)",
        "dosis": "1ª Dosis",
        "edad_rec_meses": 2,
        "edad_rec_str": "2 meses",
        "edad_min_dias": 42,
        "edad_min_str": "6 semanas",
        "edad_max_meses": 59,
        "edad_max_str": "< 5 años",
        "intervalo_rec": "8 semanas",
        "intervalo_min": "4 semanas",
        "simultaneas": ["Influenza", "Rotavirus", "Neumococo", "Hepatitis A"],
        "cualquier_intervalo": ["BCG", "SRP", "SR"],
        "intervalo_especial": [("Varicela", "4 semanas de separación")],
        "color": "#0277BD"
    },
    {
        "nombre": "Hexavalente acelular *(DPaT+IPV+HB+Hib)",
        "dosis": "2ª Dosis",
        "edad_rec_meses": 4,
        "edad_rec_str": "4 meses",
        "edad_min_dias": 70,
        "edad_min_str": "10 semanas",
        "edad_max_meses": 59,
        "edad_max_str": "< 5 años",
        "intervalo_rec": "8 semanas",
        "intervalo_min": "4 semanas",
        "simultaneas": ["Influenza", "Rotavirus", "Neumococo", "Hepatitis A"],
        "cualquier_intervalo": ["BCG", "SRP", "SR"],
        "intervalo_especial": [("Varicela", "4 semanas de separación")],
        "color": "#0277BD"
    },
    {
        "nombre": "Hexavalente acelular *(DPaT+IPV+HB+Hib)",
        "dosis": "3ª Dosis",
        "edad_rec_meses": 6,
        "edad_rec_str": "6 meses",
        "edad_min_dias": 98,
        "edad_min_str": "14 semanas",
        "edad_max_meses": 59,
        "edad_max_str": "< 5 años",
        "intervalo_rec": "12 semanas",
        "intervalo_min": "6 semanas",
        "simultaneas": ["Influenza", "Rotavirus", "Neumococo", "Hepatitis A"],
        "cualquier_intervalo": ["BCG", "SRP", "SR"],
        "intervalo_especial": [("Varicela", "4 semanas de separación")],
        "color": "#0277BD"
    },
    {
        "nombre": "Hexavalente acelular *(DPaT+IPV+HB+Hib)",
        "dosis": "4ª Dosis (Refuerzo)",
        "edad_rec_meses": 18,
        "edad_rec_str": "18 meses",
        "edad_min_dias": 365,
        "edad_min_str": "12 meses",
        "edad_max_meses": 59,
        "edad_max_str": "< 5 años",
        "intervalo_rec": "No Aplica",
        "intervalo_min": "No Aplica",
        "simultaneas": ["Influenza", "Rotavirus", "Neumococo", "Hepatitis A"],
        "cualquier_intervalo": ["BCG", "SRP", "SR"],
        "intervalo_especial": [("Varicela", "4 semanas de separación")],
        "color": "#0277BD"
    },
    {
        "nombre": "Neumocócica conjugada (VCN)",
        "dosis": "1ª Dosis",
        "edad_rec_meses": 2,
        "edad_rec_str": "2 meses",
        "edad_min_dias": 42,
        "edad_min_str": "6 semanas",
        "edad_max_meses": 59,
        "edad_max_str": "59 meses de edad",
        "intervalo_rec": "8 semanas",
        "intervalo_min": "4 a 8 semanas",
        "simultaneas": ["Hexavalente", "Influenza", "Rotavirus", "Hepatitis A"],
        "cualquier_intervalo": ["BCG", "SRP", "SR", "Varicela"],
        "intervalo_especial": [],
        "color": "#00838F"
    },
    {
        "nombre": "Neumocócica conjugada (VCN)",
        "dosis": "2ª Dosis",
        "edad_rec_meses": 4,
        "edad_rec_str": "4 meses",
        "edad_min_dias": 70,
        "edad_min_str": "10 semanas",
        "edad_max_meses": 59,
        "edad_max_str": "59 meses de edad",
        "intervalo_rec": "8 meses",
        "intervalo_min": "8 semanas",
        "simultaneas": ["Hexavalente", "Influenza", "Rotavirus", "Hepatitis A"],
        "cualquier_intervalo": ["BCG", "SRP", "SR", "Varicela"],
        "intervalo_especial": [],
        "color": "#00838F"
    },
    {
        "nombre": "Neumocócica conjugada (VCN)",
        "dosis": "3ª Dosis (Refuerzo)",
        "edad_rec_meses": 12,
        "edad_rec_str": "12 meses",
        "edad_min_dias": 84,
        "edad_min_str": "12 semanas",
        "edad_max_meses": 59,
        "edad_max_str": "59 meses de edad",
        "intervalo_rec": "No Aplica",
        "intervalo_min": "No Aplica",
        "simultaneas": ["Hexavalente", "Influenza", "Rotavirus", "Hepatitis A"],
        "cualquier_intervalo": ["BCG", "SRP", "SR", "Varicela"],
        "intervalo_especial": [],
        "color": "#00838F"
    },
    {
        "nombre": "Antirrotavirus (Rv1)",
        "dosis": "1ª Dosis",
        "edad_rec_meses": 2,
        "edad_rec_str": "2 meses",
        "edad_min_dias": 42,
        "edad_min_str": "6 semanas",
        "edad_max_dias": 239,
        "edad_max_meses": 7.9,
        "edad_max_str": "7 meses 29 días",
        "intervalo_rec": "8 semanas",
        "intervalo_min": "4 semanas",
        "simultaneas": ["Hexavalente", "Influenza", "Neumococo"],
        "cualquier_intervalo": ["BCG"],
        "intervalo_especial": [],
        "color": "#2E7D32"
    },
    {
        "nombre": "Antirrotavirus (Rv1)",
        "dosis": "2ª Dosis",
        "edad_rec_meses": 4,
        "edad_rec_str": "4 meses",
        "edad_min_dias": 70,
        "edad_min_str": "10 semanas",
        "edad_max_dias": 239,
        "edad_max_meses": 7.9,
        "edad_max_str": "7 meses 29 días",
        "intervalo_rec": "No Aplica",
        "intervalo_min": "No Aplica",
        "simultaneas": ["Hexavalente", "Influenza", "Neumococo"],
        "cualquier_intervalo": ["BCG"],
        "intervalo_especial": [],
        "color": "#2E7D32"
    },
    {
        "nombre": "Influenza Estacional",
        "dosis": "1ª Dosis (Primovacunación)",
        "edad_rec_meses": 6,
        "edad_rec_str": "6 meses",
        "edad_min_dias": 180,
        "edad_min_str": "6 meses",
        "edad_max_meses": 59,
        "edad_max_str": "59 meses",
        "intervalo_rec": "4 semanas",
        "intervalo_min": "4 semanas",
        "simultaneas": ["Hexavalente", "Rotavirus", "Neumococo", "Hepatitis A", "COVID-19"],
        "cualquier_intervalo": ["BCG", "SRP", "SR", "Varicela"],
        "intervalo_especial": [],
        "color": "#AD1457"
    },
    {
        "nombre": "Influenza Estacional",
        "dosis": "2ª Dosis (Primovacunación)",
        "edad_rec_meses": 7,
        "edad_rec_str": "7 meses",
        "edad_min_dias": 210,
        "edad_min_str": "7 meses",
        "edad_max_meses": 59,
        "edad_max_str": "59 meses",
        "intervalo_rec": "Anual",
        "intervalo_min": "4 semanas",
        "simultaneas": ["Hexavalente", "Rotavirus", "Neumococo", "Hepatitis A", "COVID-19"],
        "cualquier_intervalo": ["BCG", "SRP", "SR", "Varicela"],
        "intervalo_especial": [],
        "color": "#AD1457"
    },
    {
        "nombre": "Triple Viral (SRP)",
        "dosis": "1ª Dosis (Sarampión, rubéola y parotiditis)",
        "edad_rec_meses": 12,
        "edad_rec_str": "12 meses",
        "edad_min_dias": 365,
        "edad_min_str": "12 meses",
        "edad_max_meses": 119,
        "edad_max_str": "Menores de 10 años",
        "intervalo_rec": "5 años (o a los 18 meses si nació post-2020)",
        "intervalo_min": "4 semanas",
        "simultaneas": ["Influenza", "Neumococo", "Hepatitis A", "BCG", "Hexavalente"],
        "cualquier_intervalo": [],
        "intervalo_especial": [("SR", "Intervalo de 4 semanas")],
        "color": "#F57F17"
    },
    {
        "nombre": "Triple Viral (SRP)",
        "dosis": "2ª Dosis (Sarampión, rubéola y parotiditis)",
        "edad_rec_meses": 18,
        "edad_rec_str": "18 meses (nacidos a partir de 2022) o 6 años",
        "edad_min_dias": 540,
        "edad_min_str": "18 meses / 6 años",
        "edad_max_meses": 119,
        "edad_max_str": "Menores de 10 años",
        "intervalo_rec": "No Aplica",
        "intervalo_min": "No Aplica",
        "simultaneas": ["Influenza", "Neumococo", "Hepatitis A", "BCG", "Hexavalente"],
        "cualquier_intervalo": [],
        "intervalo_especial": [("SR", "Intervalo de 4 semanas")],
        "color": "#F57F17"
    }
]

if anios < 10:
    vacunas_actuales = []
    for v in CATALOGO_CUADRO_71:
        if dias_vida >= v["edad_min_dias"]:
            if dias_vida <= v.get("edad_max_dias", v["edad_max_meses"] * 30.5 + 30):
                vacunas_actuales.append(v)

    if vacunas_actuales:
        st.markdown(f"#### 📍 Biológicos indicados para la edad del paciente ({subcategoria}):")
        
        for v in vacunas_actuales:
            # Generador de Badges HTML para Coadministración
            badges_simultaneas = "".join([
                f'<span style="background-color: #E8F5E9; color: #1B5E20; border: 1px solid #A5D6A7; padding: 4px 8px; border-radius: 6px; font-size: 0.78rem; font-weight: 600; margin-right: 4px; margin-bottom: 4px; display: inline-block;">💉 {sim}</span>'
                for sim in v["simultaneas"]
            ])

            badges_cualquier_intervalo = "".join([
                f'<span style="background-color: #E0F2F1; color: #004D40; border: 1px solid #80CBC4; padding: 4px 8px; border-radius: 6px; font-size: 0.78rem; font-weight: 600; margin-right: 4px; margin-bottom: 4px; display: inline-block;">⏱️ {ci} (Cualquier intervalo)</span>'
                for ci in v["cualquier_intervalo"]
            ])

            badges_intervalo_especial = "".join([
                f'<span style="background-color: #FFF3E0; color: #BF360C; border: 1px solid #FFCC80; padding: 4px 8px; border-radius: 6px; font-size: 0.78rem; font-weight: 600; margin-right: 4px; margin-bottom: 4px; display: inline-block;">⚠️ {ie[0]}: {ie[1]}</span>'
                for ie in v["intervalo_especial"]
            ])

            st.markdown(f"""
            <div style="
                border: 1px solid #CFD8DC;
                border-left: 6px solid {v['color']};
                border-radius: 8px;
                padding: 14px 18px;
                margin-bottom: 15px;
                background-color: #FFFFFF;
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 1.15rem; font-weight: 700; color: {v['color']};">
                        {v['nombre']} — <span style="font-weight: 600; color: #37474F;">{v['dosis']}</span>
                    </span>
                    <span style="background-color: #ECEFF1; color: #37474F; padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600;">
                        Recomendada: {v['edad_rec_str']}
                    </span>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 8px; font-size: 0.85rem; color: #424242; margin-bottom: 12px; background-color: #F8F9FA; padding: 8px 12px; border-radius: 6px;">
                    <div><strong>🔹 Edad mínima:</strong> {v['edad_min_str']}</div>
                    <div><strong>🔸 Edad máxima permitida:</strong> {v['edad_max_str']}</div>
                    <div><strong>⏱️ Intervalo recomendado:</strong> {v['intervalo_rec']}</div>
                    <div><strong>⚠️ Intervalo mínimo:</strong> {v['intervalo_min']}</div>
                </div>

                <div style="font-size: 0.84rem; font-weight: 700; color: #455A64; margin-bottom: 6px;">
                    🔗 Aplicación y Compatibilidad entre Biológicos:
                </div>
                
                <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 4px;">
                    {badges_simultaneas}
                    {badges_cualquier_intervalo}
                    {badges_intervalo_especial}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ El paciente ha superado el rango de primovacunación de este cuadro pediátrico.")
else:
    st.markdown(f"#### 📍 Biológicos indicados para población de 10 a 19 años y adultos ({subcategoria}):")
    st.markdown("""
    <div style="border: 1px solid #CFD8DC; border-left: 6px solid #1976D2; border-radius: 6px; padding: 14px 18px; background-color: #FAFAFA; margin-bottom: 12px;">
        <span style="font-size: 1.1rem; font-weight: 700; color: #0D47A1;">Esquema Integral para el Adulto</span>
        <div style="font-size: 0.9rem; color: #37474F; margin-top: 6px;">
            - <strong>Td / Tdpa:</strong> Refuerzo cada 10 años (1 dosis de Tdpa en embarazadas a partir de la semana 20).<br>
            - <strong>SR:</strong> 2 dosis si no cuenta con antecedente vacunal previo en personas de 10 a 39 años.<br>
            - <strong>Anti Hepatitis B:</strong> Esquema de 3 dosis (0, 1, 6 meses) en grupos de riesgo o personal de salud.<br>
            - <strong>VPH:</strong> Mujeres y personas en edad blanco institucional según lineamiento sectorial.<br>
            - <strong>Anti neumocócica 23 valente:</strong> Indicada a partir de los 60 años o con comorbilidades.<br>
            - <strong>Anti Influenza:</strong> Dosis anual de refuerzo en temporada invernal.
        </div>
    </div>
    """, unsafe_allow_html=True)
