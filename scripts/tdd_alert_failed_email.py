"""Aviso al responsable si falla un informe automatico TDD 2027.

El aviso es independiente del informe de destinatarios y solo se envia al
remitente institucional. No imprime credenciales ni datos de docentes.
"""
import os
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from zoneinfo import ZoneInfo

EMAIL = "sebastian.giampani@bue.edu.ar"

def main():
    password = os.environ.get("TDD_GMAIL_APP_PASSWORD", "").replace(" ", "")
    if not password:
        raise RuntimeError("No se pudo alertar: falta credencial de correo en GitHub Secrets.")
    today = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires"))
    repo = os.environ.get("GITHUB_REPOSITORY", "sebastiangiampani-create/tdd2027coordi")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    url = "https://github.com/" + repo + "/actions/runs/" + run_id if run_id else "https://github.com/" + repo + "/actions"
    message = EmailMessage()
    message["From"] = EMAIL
    message["To"] = EMAIL
    message["Subject"] = "TDD 2027 - Fallo el informe de asistencia automatico"
    message.set_content(
        "El informe de asistencia TDD 2027 no se envio correctamente.\n"
        "Fecha y hora de deteccion (Argentina): " + today.strftime("%d/%m/%Y %H:%M") + "\n"
        "Revisar el error en GitHub Actions:\n" + url + "\n"
        "Este aviso se envia solo a la cuenta responsable.\n"
    )
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context(), timeout=30) as smtp:
        smtp.login(EMAIL, password)
        smtp.send_message(message)
    print("Alerta de fallo aceptada por SMTP para la cuenta responsable.")

if __name__ == "__main__":
    main()
