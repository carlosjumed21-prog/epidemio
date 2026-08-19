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
        value=date(2010, 5, 20),
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
    color_fondo = "#FCE4EC"
    color_borde = "#D81B60"
    color_texto = "#880E4F"
    badge_bg = "#E91E63"
else:
    color_fondo = "#E3F2FD"
    color_borde = "#1976D2"
    color_texto = "#0D47A1"
    badge_bg = "#1565C0"

# --- 5. DISPLAY VISUAL DEL PERFIL ---
st.markdown("### 🏷️ Perfil Detectado")

tarjeta_html = f"""
<div style="
    background-color: {color_fondo};
    border-left: 8px solid {color_borde};
    border-radius: 8px;
    padding: 16px 20px;
    margin-top: 10px;
    margin-bottom: 25px;
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

# --- 6. ESQUEMAS DE VACUNACIÓN CONDICIONALES ---

if anios < 10:
    # --- ESQUEMA MENORES DE 10 AÑOS ---
    tabla_pediatrica_html = """
    <style>
        .tabla-esquema {
            width: 100%;
            border-collapse: separate;
            border-spacing: 4px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin-top: 10px;
        }
        .th-titulo {
            color: #A07248;
            font-size: 1.55rem;
            font-weight: 800;
            text-align: center;
            padding-bottom: 12px;
            letter-spacing: -0.5px;
        }
        .th-col-edad {
            background-color: #555555;
            color: #FFFFFF;
            font-weight: 700;
            font-size: 0.95rem;
            text-align: center;
            padding: 10px;
            width: 16%;
            border-radius: 3px;
        }
        .th-col-vacunas {
            background-color: #555555;
            color: #FFFFFF;
            font-weight: 700;
            font-size: 0.95rem;
            text-align: center;
            padding: 10px;
            border-radius: 3px;
        }
        .celda-edad {
            background-color: #555555;
            color: #FFFFFF;
            font-weight: 700;
            font-size: 0.88rem;
            text-align: center;
            padding: 10px 6px;
            border-radius: 3px;
        }
        .celda-vacuna {
            font-size: 0.85rem;
            font-weight: 600;
            text-align: center;
            padding: 10px 8px;
            border-radius: 3px;
            color: #263238;
        }
        /* Paleta Esquema <10 */
        .color-bcg { background-color: #D9D2E9; }
        .color-hepb { background-color: #F9CB9C; }
        .color-hexavalente { background-color: #CFE2F3; }
        .color-rotavirus { background-color: #D9EAD3; }
        .color-neumococo { background-color: #E7F3FE; }
        .color-influenza-rosa { background-color: #FADCE9; }
        .color-srp { background-color: #FFF2CC; }
        .color-dpt { background-color: #E2E3E5; }
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
                <td colspan="2" class="celda-vacuna color-bcg">BCG</td>
                <td colspan="4" class="celda-vacuna color-hepb">Hepatitis B</td>
            </tr>
            <tr>
                <td class="celda-edad">2 meses</td>
                <td colspan="2" class="celda-vacuna color-hexavalente">Hexavalente acelular*</td>
                <td colspan="2" class="celda-vacuna color-rotavirus">Rotavirus</td>
                <td colspan="2" class="celda-vacuna color-neumococo">Neumococo conjugada 13 valente</td>
            </tr>
            <tr>
                <td class="celda-edad">4 meses</td>
                <td colspan="2" class="celda-vacuna color-hexavalente">Hexavalente acelular*</td>
                <td colspan="2" class="celda-vacuna color-rotavirus">Rotavirus</td>
                <td colspan="2" class="celda-vacuna color-neumococo">Neumococo conjugada 13 valente</td>
            </tr>
            <tr>
                <td class="celda-edad">6 meses</td>
                <td colspan="2" class="celda-vacuna color-hexavalente">Hexavalente acelular*</td>
                <td colspan="4" class="celda-vacuna color-influenza-rosa">Influenza 1a dosis</td>
            </tr>
            <tr>
                <td class="celda-edad">7 meses</td>
                <td colspan="6" class="celda-vacuna color-influenza-rosa">Influenza 2a dosis</td>
            </tr>
            <tr>
                <td class="celda-edad">12 meses (1 año)</td>
                <td colspan="3" class="celda-vacuna color-srp">Triple viral (SRP)**</td>
                <td colspan="3" class="celda-vacuna color-neumococo">Neumococo conjugada 13 valente</td>
            </tr>
            <tr>
                <td class="celda-edad">18 meses</td>
                <td colspan="3" class="celda-vacuna color-hexavalente">Hexavalente acelular*</td>
                <td colspan="3" class="celda-vacuna color-srp">Triple viral (SRP)** 2a dosis (Nacidos después de 2020)</td>
            </tr>
            <tr>
                <td class="celda-edad">24 meses (2 años)</td>
                <td colspan="6" class="celda-vacuna color-influenza-rosa">Influenza refuerzo anual</td>
            </tr>
            <tr>
                <td class="celda-edad">36 meses (3 años)</td>
                <td colspan="6" class="celda-vacuna color-influenza-rosa">Influenza refuerzo anual</td>
            </tr>
            <tr>
                <td class="celda-edad">48 meses (4 años)</td>
                <td colspan="3" class="celda-vacuna color-influenza-rosa">Influenza refuerzo anual</td>
                <td colspan="3" class="celda-vacuna color-dpt">DPT</td>
            </tr>
            <tr>
                <td class="celda-edad">59 meses (5 años)</td>
                <td colspan="6" class="celda-vacuna color-influenza-rosa">Influenza refuerzo anual</td>
            </tr>
            <tr>
                <td class="celda-edad">72 meses (6 años)</td>
                <td colspan="6" class="celda-vacuna color-srp">Triple viral (SRP)** 2a dosis (Nacidos antes de 2020)</td>
            </tr>
        </tbody>
    </table>
    """
    st.markdown(tabla_pediatrica_html, unsafe_allow_html=True)

else:
    # --- ESQUEMA 10 A 19 AÑOS Y ADULTOS (>= 10 AÑOS) ---
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
            letter-spacing: -0.5px;
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
        /* Paleta Adultos réplica exacta */
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
