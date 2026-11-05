"""Optional plain-text email delivery for TDD WhatsApp report; no attachments."""
import os
import json
import re
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path

def main():
    config=json.loads(Path("config/destinatarios.json").read_text(encoding="utf-8"))
    addresses=list(dict.fromkeys(x["email"].strip().lower() for x in config["destinatarios"] if x.get("activo") is True))
    pattern=r"[A-Za-z0-9._%+\\-]+@[A-Za-z0-9.\\-]+\\.[A-Za-z]{2,}"
    if not addresses or any(not re.fullmatch(pattern,x) for x in addresses):
        raise RuntimeError("Destinatarios de email invalidos")
    password=os.environ.get("TDD_GMAIL_APP_PASSWORD","").replace(" ","")
    if not password: raise RuntimeError("Falta TDD_GMAIL_APP_PASSWORD")
    body=Path("report-output/mensaje.txt").read_text(encoding="utf-8").replace("*","")
    msg=EmailMessage()
    msg["From"]="sebastian.giampani@bue.edu.ar"
    msg["To"]="sebastian.giampani@bue.edu.ar"
    msg["Bcc"]=", ".join(x for x in addresses if x!=msg["To"])
    msg["Subject"]="TDD 2027 - Informe de asistencia"
    msg.set_content(body)
    with smtplib.SMTP_SSL("smtp.gmail.com",465,context=ssl.create_default_context(),timeout=30) as smtp:
        smtp.login(msg["From"],password)
        smtp.send_message(msg,to_addrs=addresses)
    print(f"Correo aceptado por SMTP para {len(addresses)} destinatarios.")

if __name__=="__main__":
    main()
