import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Filtrador SEACE", layout="centered")

st.title("📄 Filtrador de Procesos SEACE")

st.markdown("Sube el archivo Excel descargado desde [SEACE](https://www.seace.gob.pe/buscador) y filtra los procesos por Objeto de Contratación y Tipo de Selección.")

uploaded_file = st.file_uploader("📤 Sube tu archivo Excel aquí", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # Mostrar columnas disponibles
        st.success(f"Archivo cargado con {len(df)} filas.")

        # Normalizar texto
        df['Objeto de contratación'] = df['Objeto de contratación'].str.upper()
        df['Tipo de procedimiento'] = df['Tipo de procedimiento'].str.upper()

        # Opciones de filtro
        objetos = ['BIEN', 'SERVICIO', 'OBRA', 'CONSULTORÍA DE OBRA']
        tipos = ['LP', 'LPE', 'LPP', 'LPN', 'CPS', 'CPC', 'CPP']

        objeto_sel = st.multiselect("🛠 Objeto de contratación", objetos, default=objetos)
        tipo_sel = st.multiselect("⚖ Tipo de selección", tipos, default=tipos)

        # Filtrar
        df_filtrado = df[
            df['Objeto de contratación'].str.contains('|'.join(objeto_sel), na=False) &
            df['Tipo de procedimiento'].str.contains('|'.join(tipo_sel), na=False)
        ]

        st.markdown(f"### 🔎 Resultados filtrados: {len(df_filtrado)} filas")
        st.dataframe(df_filtrado)

        # Botón para descargar
        def to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Filtrado')
            output.seek(0)
            return output

        st.download_button(
            "⬇️ Descargar Excel filtrado",
            data=to_excel(df_filtrado),
            file_name="procesos_filtrados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
