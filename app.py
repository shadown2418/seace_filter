# Requiere instalación de dependencias:
# pip install streamlit pandas openpyxl xlsxwriter xlrd

import streamlit as st
import pandas as pd
from io import BytesIO
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime

st.set_page_config(page_title="Validador SEACE", layout="wide")
st.title("📊 Validador de Procesos SEACE")

# Columnas requeridas
columnas_requeridas = {
    "Nombre o Sigla de la Entidad": "nombre entidad",
    "Fecha y Hora de Publicacion": "fecha de publicacion",
    "Nomenclatura": "nomenclatura",
    "Objeto de Contratación": "objeto de contratacion",
    "Descripción de Objeto": "descripcion",
    "VR / VE / Cuantía de la contratación": "vr/ve",
    "Moneda": "moneda",
    "CUI": "cui",
    "Código SNIP": "codigo snip",
    "Ficha de Selección": "ficha de seleccion"  # opcional si se incluye
}

archivo = st.file_uploader("Sube tu archivo Excel (.xlsx o .xls)", type=["xlsx", "xls"])

if archivo:
    try:
        # Intentar leer con openpyxl o fallback a xlrd
        try:
            df = pd.read_excel(archivo, engine="openpyxl")
        except:
            df = pd.read_excel(archivo, engine="xlrd")

        columnas_archivo = df.columns.tolist()

        # Validación de columnas
        faltantes = [col for col in columnas_requeridas if col not in columnas_archivo]

        if faltantes:
            st.error("\n❌ Faltan las siguientes columnas necesarias:\n\n" + "\n".join([f"- {col}" for col in faltantes]))
        else:
            st.success("✅ Archivo válido. Todas las columnas requeridas están presentes.")

            # Renombrar columnas para trabajar con nombres simples
            df = df.rename(columns=columnas_requeridas)

            # Convertir fecha
            df["fecha de publicacion"] = pd.to_datetime(df["fecha de publicacion"], errors="coerce")

            # Filtros
            with st.expander("🔍 Filtros"):
                col1, col2, col3 = st.columns(3)

                entidades = df["nombre entidad"].dropna().unique().tolist()
                entidad_sel = col1.multiselect("Entidad", entidades, default=entidades)

                objetos = df["objeto de contratacion"].dropna().unique().tolist()
                objeto_sel = col2.multiselect("Objeto de Contratación", objetos, default=objetos)

                fecha_min = df["fecha de publicacion"].min()
                fecha_max = df["fecha de publicacion"].max()
                fecha_rango = col3.date_input("Rango de Fechas", [fecha_min, fecha_max])

                # Filtrar
                df_filtrado = df[
                    (df["nombre entidad"].isin(entidad_sel)) &
                    (df["objeto de contratacion"].isin(objeto_sel)) &
                    (df["fecha de publicacion"] >= pd.to_datetime(fecha_rango[0])) &
                    (df["fecha de publicacion"] <= pd.to_datetime(fecha_rango[1]))
                ]

            st.subheader("📋 Procesos Filtrados")
            st.dataframe(df_filtrado, use_container_width=True)

            # Botón de descarga
            def convertir_excel(df):
                buffer = BytesIO()
                df.to_excel(buffer, index=False, engine='xlsxwriter')
                buffer.seek(0)
                return buffer

            buffer_excel = convertir_excel(df_filtrado)

            st.download_button(
                label="⬇️ Descargar archivo validado",
                data=buffer_excel,
                file_name="procesos_validado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # Botón para enviar por correo
            def enviar_email_con_excel(df):
                output = BytesIO()
                df.to_excel(output, index=False, engine='openpyxl')
                output.seek(0)

                msg = EmailMessage()
                msg['Subject'] = 'Procesos SEACE validados'
                msg['From'] = os.getenv("EMAIL_USER")
                msg['To'] = os.getenv("EMAIL_TO")
                msg.set_content("Se adjunta el archivo validado de procesos SEACE.")

                msg.add_attachment(
                    output.read(),
                    maintype='application',
                    subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    filename='procesos_validado.xlsx'
                )

                with smtplib.SMTP(os.getenv("EMAIL_HOST"), int(os.getenv("EMAIL_PORT"))) as server:
                    server.starttls()
                    server.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASSWORD"))
                    server.send_message(msg)

                st.success("📤 Archivo enviado exitosamente por correo.")

            with st.expander("📧 Enviar por correo"):
                if st.button("Enviar archivo por correo"):
                    enviar_email_con_excel(df_filtrado)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
