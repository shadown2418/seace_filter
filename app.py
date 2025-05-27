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
    "Moneda": "moneda"
}

archivo = st.file_uploader("Sube tu archivo Excel (.xls o .xlsx)", type=["xls", "xlsx"])

if archivo:
    try:
        extension = archivo.name.split(".")[-1].lower()
        if extension == "xls":
            df = pd.read_excel(archivo, engine="xlrd")
        else:
            df = pd.read_excel(archivo, engine="openpyxl")

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

                entidades = sorted(df["nombre entidad"].dropna().unique().tolist())
                entidad_sel = col1.multiselect("Entidad", entidades, default=entidades)

                objetos = sorted(df["objeto de contratacion"].dropna().unique().tolist())
                objeto_sel = col2.multiselect("Objeto de Contratación", objetos, default=objetos)

                fecha_min = df["fecha de publicacion"].min()
                fecha_max = df["fecha de publicacion"].max()
                fecha_rango = col3.date_input("Rango de Fechas", [fecha_min, fecha_max])

                # Aplicar filtros
                if entidad_sel:
                    df = df[df["nombre entidad"].isin(entidad_sel)]
                if objeto_sel:
                    df = df[df["objeto de contratacion"].isin(objeto_sel)]
                df_filtrado = df[
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
            def enviar_email_con_excel(df, destinatario, asunto, mensaje):
                output = BytesIO()
                df.to_excel(output, index=False, engine='openpyxl')
                output.seek(0)

                msg = EmailMessage()
                msg['Subject'] = asunto
                msg['From'] = os.getenv("EMAIL_USER")
                msg['To'] = destinatario
                msg.set_content(mensaje)

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

                return True

            with st.expander("📧 Enviar por correo"):
                if 'email_enviado' not in st.session_state:
                    st.session_state.email_enviado = False

                destinatario = st.text_input("Correo destinatario", value="" if st.session_state.email_enviado else "")
                asunto = st.text_input("Asunto del correo", value="" if st.session_state.email_enviado else "Procesos SEACE validados")
                mensaje = st.text_area("Mensaje del correo", value="" if st.session_state.email_enviado else "Se adjunta el archivo validado de procesos SEACE.")

                if st.button("Enviar archivo por correo"):
                    if destinatario and "@" in destinatario:
                        try:
                            if enviar_email_con_excel(df_filtrado, destinatario, asunto, mensaje):
                                st.session_state.email_enviado = True
                                st.success("📤 Archivo enviado exitosamente por correo.")
                        except Exception as e:
                            st.error(f"Error al enviar el correo: {e}")
                    else:
                        st.warning("⚠️ Ingresa un correo válido antes de enviar.")

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
