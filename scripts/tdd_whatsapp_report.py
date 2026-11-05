"""Informe TDD por WhatsApp en texto. Requiere ventana de atencion de 24h abierta."""
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo
from tdd_report_email import read, at, day, count, norm, PLANNED, SHIFTS, percent

GRAPH="https://graph.facebook.com/v25.0"

def call(url, token, data, content_type):
    request=urllib.request.Request(url,data=data,headers={"Authorization":"Bearer "+token,"Content-Type":content_type},method="POST")
    try:
        with urllib.request.urlopen(request,timeout=45) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        # Surface only Meta's structured error code and message, never request credentials,
        # phone numbers, tokens, or complete response bodies.
        error_code=None
        error_subcode=None
        error_type=None
        try:
            payload=json.loads(exc.read().decode("utf-8"))
            meta_error=payload.get("error",{}) if isinstance(payload,dict) else {}
            if isinstance(meta_error,dict):
                if isinstance(meta_error.get("code"),int):
                    error_code=meta_error["code"]
                if isinstance(meta_error.get("error_subcode"),int):
                    error_subcode=meta_error["error_subcode"]
                if isinstance(meta_error.get("type"),str) and re.fullmatch(r"[A-Za-z_]{1,80}",meta_error["type"]):
                    error_type=meta_error["type"]
        except (ValueError,UnicodeError,OSError):
            pass
        details=[]
        if error_code is not None: details.append(f"codigo Meta {error_code}")
        if error_subcode is not None: details.append(f"subcodigo {error_subcode}")
        if error_type: details.append(f"tipo {error_type}")
        suffix=f" ({', '.join(details)})" if details else ""
        hint=("Revisa que el numero este habilitado como destinatario de prueba, "
              "los permisos de WhatsApp del token y la ventana de atencion de 24 horas "
              "para enviar mensajes sin plantilla.")
        raise RuntimeError(f"Meta devolvio HTTP {exc.code}{suffix}. {hint}") from None

def send(token,phone_id,recipient,payload):
    body={"messaging_product":"whatsapp","recipient_type":"individual","to":recipient,**payload}
    response=call(f"{GRAPH}/{phone_id}/messages",token,json.dumps(body).encode("utf-8"),"application/json")
    if not response.get("messages"): raise RuntimeError("Meta no confirmo la aceptacion del mensaje")
    return response

def main():
    token=os.environ.get("TDD_WA_ACCESS_TOKEN","").strip()
    phone_id=os.environ.get("TDD_WA_PHONE_NUMBER_ID","").strip()
    dry_run=os.environ.get("REPORT_DRY_RUN","").strip().lower() in {"1","true","yes"}
    test_only=os.environ.get("REPORT_TEST_ONLY","").strip().lower() in {"1","true","yes"}
    raw_recipients=(os.environ.get("TDD_WA_TEST_RECIPIENT","").strip() if test_only else (os.environ.get("TDD_WA_RECIPIENTS","").strip() or os.environ.get("TDD_WA_TEST_RECIPIENT","").strip()))
    recipients=list(dict.fromkeys(re.sub(r"\\D","",item) for item in re.split(r"[,;\\s]+",raw_recipients) if item.strip()))
    if not dry_run and (not token or not phone_id.isdigit()):
        raise RuntimeError("Faltan secrets TDD_WA_ACCESS_TOKEN o TDD_WA_PHONE_NUMBER_ID")
    if not dry_run and (not recipients or any(not 8<=len(number)<=15 for number in recipients)):
        raise RuntimeError("Configura TDD_WA_RECIPIENTS con numeros internacionales separados por comas")
    raw=os.environ.get("REPORT_DATE","").strip()
    target=datetime.strptime(raw,"%Y-%m-%d").date() if raw else datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
    rows=read(87091997)
    if len(rows)<2: raise RuntimeError("No se pudo consultar la planilla de asistencia")
    records=[r for r in rows[1:] if at(r,1)]
    scope=os.environ.get("REPORT_SCOPE","general").strip().lower()
    scopes={"tm":("Mañana",),"tm_tt":("Mañana","Tarde"),"general":tuple(SHIFTS)}
    if scope not in scopes: raise RuntimeError("REPORT_SCOPE invalido: tm, tm_tt o general")
    included=scopes[scope]
    today=[r for r in records if day(at(r,13))==target and norm(at(r,14)) in {norm(name) for name in included}]
    if not today: raise RuntimeError("Sin asistencia para esa fecha; no se envio nada")
    plan=PLANNED.get(["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"][target.weekday()],[])
    current_shift={"tm":"Mañana","tm_tt":"Tarde","general":"Vespertino"}[scope]
    current_index=SHIFTS.index(current_shift)
    current_actual=count([r for r in today if norm(at(r,14))==norm(current_shift)])
    current_expected=plan[current_index] if current_index<len(plan) else 0
    prior=[r for r in records if (d:=day(at(r,13))) and (d<target or (d==target and norm(at(r,14)) in {norm(name) for name in included}))]
    unique_period=count(prior)
    def fmt(value): return f"{value:,}".replace(",", ".")
    def pct(actual,planned): return percent(actual,planned).replace(".", ",")
    icons={"Mañana":"☀️","Tarde":"🌤️","Vespertino":"🌙"}
    caption=(
        f"📍 *INFORME DE ASISTENCIA · TURNO {current_shift.upper()}*\n\n"
        f"📅 *Fecha:* {target.strftime('%d/%m/%Y')}\n\n"
    )
    if scope=="general":
        # El cierre vespertino muestra los tres turnos, sin duplicar el acumulado.
        for i,name in enumerate(SHIFTS):
            actual=count([r for r in today if norm(at(r,14))==norm(name)])
            expected=plan[i] if i<len(plan) else 0
            caption+=(
                f"{icons[name]} *ASISTENCIA DEL TURNO {name.upper()}*\n"
                f"👥 *Docentes asistentes:* {fmt(actual)}\n"
                f"📋 *Docentes previstos:* {fmt(expected)}\n"
                f"📈 *Porcentaje:* {pct(actual,expected)}\n\n"
            )
    else:
        caption+=(
            f"{icons[current_shift]} *ASISTENCIA DEL TURNO {current_shift.upper()}*\n"
            f"👥 *Docentes asistentes:* {fmt(current_actual)}\n"
            f"📋 *Docentes previstos:* {fmt(current_expected)}\n"
            f"📈 *Porcentaje:* {pct(current_actual,current_expected)}\n\n"
        )
    caption += (
        "🌎 *PARTICIPACIÓN ACUMULADA DEL PERÍODO*\n"
        f"👥 *Docentes distintos:* {fmt(unique_period)}\n"
        f"🎯 *Cobertura del universo:* {pct(unique_period,3853)} de 3.853 docentes\n\n"
        "_Datos registrados al momento del envío. Totales por DNI únicos._\n\n"
        "🏛️ *Escuela de Maestros* · Ministerio de Educación"
    )
    from pathlib import Path
    out=Path("report-output")
    out.mkdir(exist_ok=True)
    (out/"mensaje.txt").write_text(caption,encoding="utf-8")
    if dry_run:
        print(f"VALIDACION SIN ENVIO: texto generado. Corte {scope}, fecha {target}, asistentes del turno {current_actual}, DNI unicos del periodo {unique_period}.")
        return
    send(token,phone_id,recipient,{"type":"text","text":{"preview_url":False,"body":caption}})
            accepted+=1
        except RuntimeError as exc:
            failures.append((index,str(exc)))
    print(f"Meta acepto {accepted}/{len(recipients)} mensajes. Aceptacion no garantiza entrega.")
    if failures:
        for index,error in failures:
            print(f"Destinatario #{index}: {error}")
        raise RuntimeError(f"Fallaron {len(failures)} de {len(recipients)} envios.")

if __name__=="__main__":
    main()
