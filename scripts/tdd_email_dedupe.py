"""Evita enviar el mismo correo TDD dos veces en una fecha argentina.

Nunca envia mensajes. Si no puede verificar la API de GitHub, aborta.
"""
import json
import os
import urllib.request
from datetime import datetime, date as Date
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Argentina/Buenos_Aires")
HISTORICOS = {
    ".github/workflows/tdd-email-19.yml",
    ".github/workflows/tdd-email-brief.yml",
    ".github/workflows/tdd-email-backup.yml",
    ".github/workflows/tdd-report-preview.yml",
}
PASO_SMTP = "Enviar informe por correo en CCO"


def es_envio_exitoso(runs, fecha, run_id, jobs_for_run):
    for run in runs:
        if run.get("path") not in HISTORICOS:
            continue
        # En un reintento del mismo run puede haber un intento anterior
        # aceptado por SMTP. Revisar tambien sus jobs previos.
        if run.get("id") != run_id and run.get("status") != "completed":
            continue
        creado = run.get("created_at", "")
        if not creado:
            continue
        dia = datetime.fromisoformat(creado.replace("Z", "+00:00")).astimezone(TZ).date()
        if dia != fecha:
            continue
        for job in jobs_for_run(run["id"]):
            for step in job.get("steps", []):
                if step.get("name") == PASO_SMTP and step.get("conclusion") == "success":
                    return True
    return False


def main():
    fecha = Date.fromisoformat(os.environ["REPORT_DATE"])
    run_id = int(os.environ["GITHUB_RUN_ID"])
    repo = os.environ["GITHUB_REPOSITORY"]
    token = os.environ["GITHUB_TOKEN"]
    base = "https://api.github.com/repos/" + repo

    def api(path):
        request = urllib.request.Request(
            base + path,
            headers={
                "Authorization": "Bearer " + token,
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "TDD-2027-Unico-Envio",
            },
        )
        with urllib.request.urlopen(request, timeout=25) as response:
            return json.load(response)

    # Paginar para no omitir un envio anterior cuando hay muchos
    # deployments de GitHub Pages en el mismo dia.
    runs = []
    for page in range(1, 11):
        lote = api(f"/actions/runs?per_page=100&page={page}").get("workflow_runs")
        if not isinstance(lote, list):
            raise RuntimeError("No fue posible consultar los envios previos; envio bloqueado")
        runs.extend(lote)
        if len(lote) < 100:
            break
        ultimo = lote[-1].get("created_at")
        if not ultimo:
            raise RuntimeError("Historial de ejecuciones incompleto; envio bloqueado")
        ultimo_dia = datetime.fromisoformat(ultimo.replace("Z", "+00:00")).astimezone(TZ).date()
        if ultimo_dia < fecha:
            break
    else:
        raise RuntimeError("Demasiadas ejecuciones para auditar duplicados; envio bloqueado")

    def jobs_for_run(previous_id):
        jobs = api(f"/actions/runs/{previous_id}/jobs?filter=all&per_page=100").get("jobs")
        if not isinstance(jobs, list):
            raise RuntimeError("Sin historial de pasos SMTP; envio bloqueado")
        return jobs

    duplicado = es_envio_exitoso(runs, fecha, run_id, jobs_for_run)
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write("enviar=" + ("false" if duplicado else "true") + "\n")
    if duplicado:
        print(f"NO_ENVIO_DUPLICADO: existe confirmacion anterior de paso SMTP para {fecha}")
    else:
        print(f"ENVIO_HABILITADO: no existe envio anterior confirmado para {fecha}")


if __name__ == "__main__":
    main()
