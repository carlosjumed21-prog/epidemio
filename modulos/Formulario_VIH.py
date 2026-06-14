if st.button("🚀 Generar 100 registros coherentes"):
        data = []
        for _ in range(100):
            cap = random.choice(["Si", "No"])
            grado = np.random.choice(["Técnico", "Licenciatura", "Especialidad", "Maestría"], p=[0.1, 0.5, 0.35, 0.05])
            
            # Definimos probabilidades seguras
            p1 = 0.85 if cap == "Si" else 0.45 # Siempre
            p2 = 0.10                          # Frecuentemente
            p3 = round(1.0 - (p1 + p2), 2)     # A veces (Complemento)
            
            data.append({
                "Fecha": "2026-03-01", 
                "Frecuencia_EPP": np.random.choice(["Siempre", "Frecuentemente", "A veces"], p=[p1, p2, p3]),
                "Capacitacion_VIH": cap, 
                "Grado_Academico": grado, 
                "Conocimiento_NOM": "Alto (9-10)" if cap == "Si" else "Bajo (0-5.9)"
            })
        st.session_state.db_vih = pd.DataFrame(data)
        st.success("✅ Base de datos simulada creada.")
