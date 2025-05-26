import streamlit as st
import pandas as pd

st.title("📥 Validación de archivo de procesos SEACE")

uploaded_file = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, engine="openpyxl")
        df.columns = df.columns.str.strip().str.lower()

        columnas_requeridas = {
            'nombre entidad',
            'fecha de publicación',
            'nomenclatura',
            'objeto de contratación',
            'descripción',
            'código snip',
            'cui',
            'vr/ve',
            'moneda',
            'ficha de selección'
        }

        columnas_presentes = set(df.columns)
        faltantes = columnas_requeridas - columnas_presentes

        st.subheader("🧾 Columnas detectadas:")
        st.write(list(df.columns))

        if faltantes:
            st.error("❌ Faltan las siguientes columnas necesarias:")
            for col in faltantes:
                st.write(f"• {col}")
        else:
            st.success("✅ Todas las columnas requeridas están presentes.")
            st.dataframe(df[list(columnas_requeridas)].head(20))

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
