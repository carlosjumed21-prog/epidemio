import streamlit as st

def render():
    st.title("Unidad Notificante")
    st.markdown("---")

    # CSS para convertir los botones de formularios en color rojo
    st.markdown("""
        <style>
        div.stButton > button:first-child {
            background-color: #FF4B4B;
            color: white;
            border: none;
        }
        div.stButton > button:first-child:hover {
            background-color: #FF2B2B;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)

    # Lógica de datos predeterminados
    tlahuac_data = {
        "Entidad": "CDMX", "Jurisdicción": "Tlahuac", 
        "CLUES": "DFIST00053", "Municipio": "Tlahuac", "Localidad": "Tlahuac"
    }

    opcion_unidad = st.selectbox("Seleccione la Unidad Notificante:", ["Seleccione...", "Tlahuac", "Otro"])
    
    disabled = (opcion_unidad == "Tlahuac")
    datos = tlahuac_data if opcion_unidad == "Tlahuac" else {"Entidad": "", "Jurisdicción": "", "CLUES": "", "Municipio": "", "Localidad": ""}

    with st.form("form_unidad"):
        col1, col2 = st.columns(2)
        with col1:
            entidad = st.text_input("Entidad", value=datos["Entidad"], disabled=disabled)
            jurisdiccion = st.text_input("Jurisdicción", value=datos["Jurisdicción"], disabled=disabled)
            clues = st.text_input("CLUES", value=datos["CLUES"], disabled=disabled)
        with col2:
            municipio = st.text_input("Municipio", value=datos["Municipio"], disabled=disabled)
            localidad = st.text_input("Localidad", value=datos["Localidad"], disabled=disabled)
        
        # Botón rojo
        submit = st.form_submit_button("Guardar Registro y Continuar")
        
        if submit:
            # Guardamos los datos en el session_state para persistirlos
            st.session_state.datos_unidad = {
                "Entidad": entidad, "Jurisdicción": jurisdiccion, 
                "CLUES": clues, "Municipio": municipio, "Localidad": localidad
            }
            
            st.success("Datos guardados. Ya puedes avanzar a la siguiente ventana.")
            
            # Opcional: Esto te permite saber qué datos se guardaron para tu lógica de gspread futura
            st.write("Datos en memoria:", st.session_state.datos_unidad)
