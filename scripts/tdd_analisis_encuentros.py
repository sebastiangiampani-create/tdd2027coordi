"""Informe agregado de participación por DNI distinto y encuentro.

Lee Asistencias (gid=87091997) de la fuente oficial. NUNCA imprime DNI ni
nombres, solo estadísticas agregadas. Los códigos se normalizan como el tablero.
"""
import csv
import io
import re
import urllib.request
from collections import Counter, defaultdict
from datetime import date, datetime
from zoneinfo import ZoneInfo

SID = "1hznlu4j_Ip4KqYNpMrdhvbJvnHrPl0hOIJ6qBOsTRb4"
GID = "87091997"


def parse_date(raw):
    val = str(raw or "").strip()
    m = re.search(r"Date\((\d{4}),(\d+),(\d+)", val)
    if m:
        try:
            return date(int(m[1]), int(m[2]) + 1, int(m[3])).isoformat()
        except ValueError:
            return None
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d",
                "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M",
                "%Y-%m-%d %H:%M:%S", "%d/%m"):
        try:
            dt = datetime.strptime(val, fmt)
            year = 2026 if fmt == "%d/%m" else dt.year
            return date(year, dt.month, dt.day).isoformat()
        except ValueError:
            pass
    return None


def normalize_encounter(label):
    s = str(label or "").strip().lower()
    s = re.sub(r"[\s._-]+", " ", s)
    if not s:
        return None
    # Encuentro 1 / Enc. 1 / 1 / 1°: todos representan el mismo encuentro.
    m = re.fullmatch(r"(?:encuentro|enc|e)?\s*(\d{1,2})(?:\s*(?:er|do|ro|to|°|º))?", s)
    if m:
        return "N" + str(int(m.group(1)))
    m = re.search(r"\benc(?:uentro)?\s*(\d{1,2})\b", s)
    if m:
        return "N" + str(int(m.group(1)))
    return "OTRO"


def main():
    url = "https://docs.google.com/spreadsheets/d/" + SID + "/export?format=csv&gid=" + GID
    request = urllib.request.Request(url, headers={"User-Agent": "TDD-2027-Aggregates"})
    with urllib.request.urlopen(request, timeout=50) as response:
        content = response.read().decode("utf-8-sig")
    if content.lstrip().startswith("<"):
        raise RuntimeError("La planilla no entregó un CSV. No se inventan cantidades.")
    table = list(csv.reader(io.StringIO(content)))
    if len(table) < 2:
        raise RuntimeError("Fuente sin filas suficientes.")
    header = table[0]
    if len(header) < 16:
        raise RuntimeError("Cambio de esquema: faltan columnas A:P.")
    print("ESQUEMA_CSV:", [(i + 1, header[i]) for i in [1, 12, 13, 14, 15]])
    # B = DNI; N = Encuentro; O = Fecha de capacitación.
    by_dni_date = defaultdict(set)
    by_dni_label = defaultdict(set)
    rows_by_person = Counter()
    label_distribution = Counter()
    date_distribution = Counter()
    unrecognized_labels = 0
    rows_without_date = 0
    total_valid_ids_rows = 0
    cutoff = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
    for row in table[1:]:
        if len(row) < 2:
            continue
        dni = re.sub(r"\D", "", row[1].strip())
        if not dni:
            continue
        total_valid_ids_rows += 1
        rows_by_person[dni] += 1
        raw_label = row[13].strip() if len(row) > 13 else ""
        raw_date = row[14].strip() if len(row) > 14 else ""
        label = normalize_encounter(raw_label)
        day = parse_date(raw_date)
        if day and day <= cutoff.isoformat():
            by_dni_date[dni].add(day)
            date_distribution[day] += 1
        else:
            rows_without_date += 1
        if label and label != "OTRO":
            by_dni_label[dni].add(label)
            label_distribution[label] += 1
        else:
            if label == "OTRO":
                unrecognized_labels += 1
            label_distribution[label or "BLANCO"] += 1

    ids = set(rows_by_person)
    by_date_counts = Counter(len(by_dni_date[dni]) for dni in ids)
    by_label_counts = Counter(len(by_dni_label[dni]) for dni in ids)
    disagreements = Counter(
        (len(by_dni_date[dni]), len(by_dni_label[dni])) for dni in ids
        if len(by_dni_date[dni]) != len(by_dni_label[dni])
    )
    print("CORTE:", cutoff.isoformat())
    print("FILAS_CON_DNI:", total_valid_ids_rows)
    print("TOTAL_DNI_UNICOS:", len(ids))
    print("FRECUENCIA_POR_FECHAS_DISTINTAS:", sorted(by_date_counts.items()))
    print("FRECUENCIA_POR_NUMERO_DE_ENCUENTRO:", sorted(by_label_counts.items()))
    print("FRECUENCIA_ETIQUETAS_SIN_DNI:", sorted(label_distribution.items()))
    print("FECHAS_AGREGADAS:", sorted(date_distribution.items()))
    print("REGISTROS_SIN_FECHA_VALIDA:", rows_without_date)
    print("REGISTROS_ENCUENTRO_NO_RECONOCIDO:", unrecognized_labels)
    print("DISCREPANCIAS_FECHA_VS_ETIQUETA_TOTAL_DNI:", sum(disagreements.values()))
    print("DISCREPANCIAS_TIPOS:", sorted(disagreements.items()))
    print("COMPROBACION_SUMATORIA_FECHAS:", sum(k * v for k, v in by_date_counts.items()))
    print("COMPROBACION_SUMATORIA_ETIQUETAS:", sum(k * v for k, v in by_label_counts.items()))
    if not ids:
        raise RuntimeError("No se pudieron contar DNI en la planilla.")
    if sum(by_date_counts.values()) != len(ids) or sum(by_label_counts.values()) != len(ids):
        raise RuntimeError("Inconsistencia en grupos de DNI.")


if __name__ == "__main__":
    main()
