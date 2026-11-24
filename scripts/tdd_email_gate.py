"""Decide si corresponde enviar el informe del dia, sin tocar el correo."""
import os
from datetime import datetime, time
from zoneinfo import ZoneInfo

from tdd_report_email import at, day, read, validate_attendance_sheet

TZ = ZoneInfo("America/Argentina/Buenos_Aires")
INICIO = time(19, 0)
CIERRE = time(22, 0)


def en_ventana(ahora):
    local = ahora.astimezone(TZ)
    hora = local.time().replace(tzinfo=None)
    return INICIO <= hora < CIERRE


def asistentes_unicos(filas, fecha):
    """Requiere DNI y fecha de asistencia exacta en la columna O."""
    validate_attendance_sheet(filas)
    return len({
        at(fila, 1) for fila in filas[1:]
        if at(fila, 1) and day(at(fila, 14)) == fecha
    })


def salida(fecha, habilitado):
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as archivo:
        archivo.write(f"fecha={fecha.isoformat()}\n")
        archivo.write("hay_asistencia=" + ("true" if habilitado else "false") + "\n")


def main():
    ahora = datetime.now(TZ)
    fecha = ahora.date()
    if not en_ventana(ahora):
        salida(fecha, False)
        print(f"NO_ENVIO_FUERA_DE_HORARIO: {ahora:%Y-%m-%d %H:%M} Argentina; permitido 19:00-22:00")
        return

    filas = read(87091997)
    total = asistentes_unicos(filas, fecha)
    salida(fecha, total > 0)
    if total:
        print(f"ASISTENCIA_CONFIRMADA: {fecha.isoformat()} total_DNI_unicos={total}")
    else:
        print(f"NO_ENVIO_SIN_ASISTENCIA: {fecha.isoformat()} no hay DNIs con fecha de hoy")


if __name__ == "__main__":
    main()
