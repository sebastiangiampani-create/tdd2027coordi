"""Evita reenviar el mismo informe si GitHub ejecuta tarde el cron.

Busca ejecuciones anteriores de ambos flujos CCO con el paso SMTP completado con
exito para la misma fecha de informe. Solo consulta metadatos de GitHub.
No lee ni registra ninguna informacion personal de asistentes.
"""
import json
import os
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Argentina/Buenos_Aires")


def main():
    token = os.environ["GITHUB_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]
    current_id = int(os.environ["GITHUB_RUN_ID"])
    requested = os.environ.get("REPORT_DATE", "").strip()
    date = datetime.strptime(requested, "%Y-%m-%d").date() if requested else datetime.now(TZ).date()
    base = "https://api.github.com/repos/" + repo

    def api(endpoint):
        req = urllib.request.Request(
            base + endpoint,
            headers={
                "Authorization": "Bearer " + token,
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "TDD-2027-email-dedupe",
            },
        )
        with urllib.request.urlopen(req, timeout=25) as response:
            return json.load(response)

    runs = api("/actions/runs?per_page=100").get("workflow_runs", [])
    for run in runs:
        if run.get("id") == current_id or run.get("path") not in {
            ".github/workflows/tdd-email-brief.yml",
            ".github/workflows/tdd-email-backup.yml",
            ".github/workflows/tdd-report-preview.yml",  # historico manual
        }:
            continue
        started = run.get("created_at", "")
        if not started:
            continue
        run_day = datetime.fromisoformat(started.replace("Z", "+00:00")).astimezone(TZ).date()
        if run_day != date or run.get("status") != "completed":
            continue
        jobs = api("/actions/runs/" + str(run["id"]) + "/jobs?per_page=100").get("jobs", [])
        for job in jobs:
            for step in job.get("steps", []):
                if step.get("name") == "Enviar informe por correo en CCO" and step.get("conclusion") == "success":
                    print("ENVIO_YA_REALIZADO: informe aceptado anteriormente en un intento de hoy. Se omite duplicado.")
                    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
                        output.write("send=false\n")
                    return
    print("ENVIO_PENDIENTE: no se encontro otro envio SMTP exitoso para " + date.isoformat())
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write("send=true\n")


if __name__ == "__main__":
    main()
