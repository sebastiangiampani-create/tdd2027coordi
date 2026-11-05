"""Prueba manual de informe TDD por WhatsApp. Requiere ventana de atencion de 24h abierta."""
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo
from tdd_report_email import read, at, day, count, visual_pdf, norm, PLANNED, SHIFTS, percent

GRAPH="https://graph.facebook.com/v25.0"

def call(url, token, data, content_type):
    request=urllib.request.Request(url,data=data,headers={"Authorization":"Bearer "+token,"Content-Type":content_type},method="POST")
    try:
        with urllib.request.urlopen(request,timeout=45) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        # Do not log tokens, request bodies, phone numbers, or response payloads.
        raise RuntimeError(f"Meta devolvio HTTP {exc.code}. Comproba que respondiste al numero de prueba en las ultimas 24 horas y que el token sigue vigente.") from None

def send(token,phone_id,recipient,payload):
    body={"messaging_product":"whatsapp","recipient_type":"individual","to":recipient,**payload}
    response=call(f"{GRAPH}/{phone_id}/messages",token,json.dumps(body).encode("utf-8"),"application/json")
    if not response.get("messages"): raise RuntimeError("Meta no confirmo la aceptacion del mensaje")
    return response

def main():
    token=os.environ.get("TDD_WA_ACCESS_TOKEN","").strip()
    phone_id=os.environ.get("TDD_WA_PHONE_NUMBER_ID","").strip()
    recipient=re.sub(r"\D","",os.environ.get("TDD_WA_TEST_RECIPIENT",""))
    if not token or not phone_id.isdigit() or not 8<=len(recipient)<=15:
        raise RuntimeError("Faltan secrets TDD_WA_ACCESS_TOKEN, TDD_WA_PHONE_NUMBER_ID o TDD_WA_TEST_RECIPIENT")
    raw=os.environ.get("REPORT_DATE","").strip()
    target=datetime.strptime(raw,"%Y-%m-%d").date() if raw else datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
    rows=read(87091997)
    proposals=read(0)
    if len(rows)<2 or len(proposals)<2: raise RuntimeError("No se pudieron consultar las planillas")
    records=[r for r in rows[1:] if at(r,1)]
    scope=os.environ.get("REPORT_SCOPE","general").strip().lower()
    scopes={"tm":("Mañana",),"tm_tt":("Mañana","Tarde"),"general":tuple(SHIFTS)}
    if scope not in scopes: raise RuntimeError("REPORT_SCOPE invalido: tm, tm_tt o general")
    included=scopes[scope]
    labels={"tm":"TM","tm_tt":"TM + TT","general":"GENERAL"}
    today=[r for r in records if day(at(r,13))==target and norm(at(r,14)) in {norm(name) for name in included}]
    if not today: raise RuntimeError("Sin asistencia para esa fecha; no se envio nada")
    pdf=visual_pdf(records,target,proposals,included_shifts=included,whatsapp_cutoff=True)
    if not pdf.startswith(b"%PDF-"): raise RuntimeError("PDF invalido")
    boundary="TDD2027UploadBoundary"
    filename=f"TDD_2027_Asistencia_{scope.upper()}_{target.isoformat()}.pdf"
    fields=[
        ("messaging_product",b"whatsapp",None),
        ("type",b"application/pdf",None),
        ("file",pdf,filename),
    ]
    parts=[]
    for name,value,file_name in fields:
        header=f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"'
        if file_name: header+=f'; filename="{file_name}"\r\nContent-Type: application/pdf'
        parts.append(header.encode()+b"\r\n\r\n"+value+b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    uploaded=call(f"{GRAPH}/{phone_id}/media",token,b"".join(parts),f"multipart/form-data; boundary={boundary}")
    media_id=uploaded.get("id")
    if not media_id: raise RuntimeError("Meta no devolvio ID del PDF cargado")
    # An outbound freeform document requires a customer service window opened by an inbound user message.
    plan=PLANNED.get(["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"][target.weekday()],[])
    current_shift={"tm":"Mañana","tm_tt":"Tarde","general":"Vespertino"}[scope]
    current_index=SHIFTS.index(current_shift)
    current_actual=count([r for r in today if norm(at(r,14))==norm(current_shift)])
    current_expected=plan[current_index] if current_index<len(plan) else 0
    day_actual=count(today)
    day_expected=sum(plan[i] for i,name in enumerate(SHIFTS) if name in included and i<len(plan))
    prior=[r for r in records if (d:=day(at(r,13))) and (d<target or (d==target and norm(at(r,14)) in {norm(name) for name in included}))]
    unique_period=count(prior)
    def fmt(value): return f"{value:,}".replace(",", ".")
    def pct(actual,planned): return percent(actual,planned).replace(".", ",")
    icons={"Mañana":"☀️","Tarde":"🌤️","Vespertino":"🌙"}
    breakdown=[]
    for i,name in enumerate(SHIFTS):
        if name not in included: continue
        n=count([r for r in today if norm(at(r,14))==norm(name)])
        p=plan[i] if i<len(plan) else 0
        breakdown.append(f"{icons[name]} *Turno {name.lower()}:* {fmt(n)} asistentes / {fmt(p)} previstos ({pct(n,p)})")
    shift_breakdown="\n".join(breakdown)
    cutoff={"tm":"12:00","tm_tt":"17:00","general":"20:15"}[scope]
    daily_section=""
    if scope!="tm":
        earlier=[name for name in included if name!=current_shift]
        earlier_lines="\n".join(f"{icons[name]} *Turno {name.lower()}:* {fmt(count([r for r in today if norm(at(r,14))==norm(name)]))} asistentes" for name in earlier)
        daily_section=(f"📊 *TOTAL DEL DÍA · HASTA LAS {cutoff}*\n{earlier_lines}\n"
                       f"👥 *Total asistentes:* {fmt(day_actual)} (DNI únicos)\n"
                       f"📋 *Total previstos:* {fmt(day_expected)}\n"
                       f"📈 *Porcentaje del día:* {pct(day_actual,day_expected)}\n\n")
    caption=(
        "📚 *TALLERES DE DISEÑO 2027*\n"
        f"📍 *INFORME DE ASISTENCIA · TURNO {current_shift.upper()}*\n\n"
        f"📅 *Fecha:* {target.strftime('%d/%m/%Y')}\n\n"
        f"{icons[current_shift]} *ASISTENCIA DEL TURNO {current_shift.upper()}*\n"
        f"👥 *Docentes asistentes:* {fmt(current_actual)}\n"
        f"📋 *Docentes previstos:* {fmt(current_expected)}\n"
        f"📈 *Porcentaje:* {pct(current_actual,current_expected)}\n\n"
        + daily_section
        + "🌎 *PARTICIPACIÓN ACUMULADA DEL PERÍODO*\n"
        f"👥 *Docentes distintos:* {fmt(unique_period)}\n"
        f"🎯 *Cobertura del universo:* {pct(unique_period,3853)} de 3.853 docentes\n\n"
        "📎 *Informe visual en PDF adjunto*\n"
        "_Datos registrados al momento del envío. Totales por DNI unico._\n\n"
        "🏛️ *Escuela de Maestros* · Ministerio de Educación"
    )
    send(token,phone_id,recipient,{"type":"document","document":{"id":media_id,"filename":filename,"caption":caption}})
    print("Meta acepto el PDF visual con resumen de asistencia para el destinatario de prueba.")

if __name__=="__main__":
    main()
