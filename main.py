import os
import streamlit as st

# Esto te mostrará qué carpetas ve el sistema en la raíz
st.write("Archivos detectados en la raíz:", os.listdir("."))

# Esto te mostrará qué hay dentro de la carpeta modulos
if os.path.exists("modulos"):
    st.write("Contenido de 'modulos':", os.listdir("modulos"))
else:
    st.error("La carpeta 'modulos' no existe en la raíz.")
