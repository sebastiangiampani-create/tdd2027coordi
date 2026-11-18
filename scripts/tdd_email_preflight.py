"""Preflight del envio TDD 2027: comprueba requisitos sin enviar mensajes.

No muestra nombres, DNI, passwords ni direcciones de destinatarios.
"""
import os
import smtplib
import ssl
from datetime import datetime, date
from zoneinfo import ZoneInfo

from tdd_report_email import (
    EMAIL, at, day, read, recipients, validate_attendance_sheet,
    encrypted_workbook, visual_pdf
)


def main():
    for value, expected in [
        ("16/11/2026", date(2026, 11, 16)),
        ("16/11", date(2026, 11, 16)),
        ("Date(2026,10,16)", date(2026, 11, 16)),
        ("16/11/2026 10:30", date(2026, 11, 16)),
    ]:
        if day(value) != expected:
            raise RuntimeError("PRECHECK_FAIL: reconocimiento de fechas")
    if day("Enc. 1") is not None:
        raise RuntimeError("PRECHECK_FAIL: lectura erronea de fecha")

    excel_password = os.environ.get("TDD_EXCEL_PASSWORD", "")
    gmail_password = os.environ.get("TDD_GMAIL_APP_PASSWORD", "").replace(" ", "")
    if len(excel_password) < 12:
        raise RuntimeError("PRECHECK_FAIL: falta TDD_EXCEL_PASSWORD")
    if not gmail_password:
        raise RuntimeError("PRECHECK_FAIL: falta TDD_GMAIL_APP_PASSWORD")

    addresses = recipients()
    print(f"PRECHECK_OK: {len(addresses)} destinatarios activos validados")

    rows = read(87091997)
    valid = validate_attendance_sheet(rows)
    proposals = read(0)
    if len(proposals) < 2:
        raise RuntimeError("PRECHECK_FAIL: hoja de propuestas inaccesible")
    now = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires"))
    current = sum(1 for row in rows[1:] if at(row, 1) and day(at(row, 14)) == now.date())
    print(f"PRECHECK_OK: Google Sheets accesible, {valid} filas fechadas, {current} filas de hoy")
    if not current:
        print("PRECHECK_ADVERTENCIA: aun no hay asistencias para la fecha actual; a las 19:45 el envio se cancelaria si sigue igual")

    example = next(row for row in rows[1:] if at(row, 1) and day(at(row, 14)))
    pdf = visual_pdf([example], now.date(), proposals)
    if not pdf.startswith(b"%PDF-"):
        raise RuntimeError("PRECHECK_FAIL: PDF invalido")
    excel = encrypted_workbook([example], excel_password)
    if not excel.startswith(bytes.fromhex("d0cf11e0a1b11ae1")):
        raise RuntimeError("PRECHECK_FAIL: Excel sin cifrar")
    print("PRECHECK_OK: PDF institucional y Excel cifrado generados en memoria")

    # Autentica ante el mismo SMTP usado por el envio real, SIN enviar mensajes.
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context(), timeout=30) as smtp:
        smtp.login(EMAIL, gmail_password)
        code, _ = smtp.noop()
        if code != 250:
            raise RuntimeError(f"PRECHECK_FAIL: SMTP respondio {code}")
    print("PRECHECK_OK: autenticacion SMTP de Gmail y conexion listas; NO se envio ningun correo")


if __name__ == "__main__":
    main()
