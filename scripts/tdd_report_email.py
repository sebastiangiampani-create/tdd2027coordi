import csv, io, os, smtplib, ssl, urllib.request, unicodedata, re
from datetime import datetime
from zoneinfo import ZoneInfo
from email.message import EmailMessage
from html import escape
from collections import defaultdict

SID="1hznlu4j_Ip4KqYNpMrdhvbJvnHrPl0hOIJ6qBOsTRb4"
EMAIL="sebastian.giampani@bue.edu.ar"
BASE={"DEM":2045,"DET":1393,"DENS":113,"DEA":302}
PLANNED={"Lunes":[356,225,251],"Martes":[283,274,175],"Miércoles":[437,362,305],"Jueves":[268,230,77],"Viernes":[227,205,178]}
SHIFTS=["Mañana","Tarde","Vespertino"]

def read(gid):
    url=f"https://docs.google.com/spreadsheets/d/{SID}/export?format=csv&gid={gid}"
    with urllib.request.urlopen(url,timeout=30) as f:
        data=f.read().decode("utf-8-sig")
    if data.lstrip().startswith("<"): raise ValueError("Google no devolvio CSV. Verificar acceso a la planilla.")
    return list(csv.reader(io.StringIO(data)))

def at(r,i): return str(r[i]).strip() if len(r)>i else ""
def norm(v): return unicodedata.normalize("NFKD",str(v)).encode("ascii","ignore").decode().lower().strip()
def day(v):
    v=str(v).strip()
    for fmt in ("%d/%m/%Y","%Y-%m-%d","%d/%m/%y"):
        try: return datetime.strptime(v,fmt).date()
        except ValueError: pass
    m=re.search(r"Date\\((\\d+),(\\d+),(\\d+)",v)
    if m:
        from datetime import date
        return date(int(m[1]),int(m[2])+1,int(m[3]))
    return None

def dep(v):
    n=norm(v)
    for key,aliases in {"DEM":["dem","media"],"DET":["det","tecnica"],"DENS":["dens","normal"],"DEA":["dea","artistica"]}.items():
        if any(a in n for a in aliases): return key
    return "Sin identificar"

def count(rs): return len({at(r,1) for r in rs if at(r,1)})
def percent(n,d): return f"{100*n/d:.1f}%" if d else "Sin referencia"
def table(headers,records):
    out='<table width="100%" cellpadding="9" cellspacing="0" style="border-collapse:collapse;font-size:13px"><tr style="background:#173f70;color:white">'
    out+=''.join(f'<th align="left">{escape(str(h))}</th>' for h in headers)+'</tr>'
    for row in records:
        out+='<tr style="background:#edf3fa">'+''.join(f'<td style="border-bottom:3px solid white">{escape(str(v))}</td>' for v in row)+'</tr>'
    return out+'</table>'

def attachment(rows):
    buf=io.StringIO();w=csv.writer(buf)
    w.writerow(["Fecha","Dependencia","Escuela","Area convocada","Turno","Comision","DNI","Apellido","Nombre","Codigo"])
    for r in rows: w.writerow([at(r,13),dep(at(r,5)),at(r,7),at(r,9),at(r,14),at(r,11),at(r,1),at(r,3),at(r,2),at(r,10)])
    return ("\ufeff"+buf.getvalue()).encode("utf-8")

def main():
    password=os.environ.get("TDD_GMAIL_APP_PASSWORD","").replace(" ","")
    if not password: raise RuntimeError("Falta TDD_GMAIL_APP_PASSWORD en GitHub Secrets.")
    requested=os.environ.get("REPORT_DATE","").strip()
    target=datetime.strptime(requested,"%Y-%m-%d").date() if requested else datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
    all_rows=read(87091997)
    proposals=read(0)
    if len(proposals)<2 or len(all_rows)<2: raise RuntimeError("Planillas sin datos o inaccesibles; no se envia.")
    records=[r for r in all_rows[1:] if at(r,1)]
    today=[r for r in records if day(at(r,13))==target]
    if not today: raise RuntimeError("No hay registros de la fecha seleccionada; no se envia.")
    weekday=["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"][target.weekday()]
    expected=PLANNED.get(weekday)
    total_expected=sum(expected) if expected else 0
    dates={day(at(r,13)) for r in records if day(at(r,13))}
    cumulative=sum(count([r for r in records if day(at(r,13))==d]) for d in dates)
    cumulative_expected=sum(sum(PLANNED.get(["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"][d.weekday()],[])) for d in dates)
    shifts=[]
    for i,name in enumerate(SHIFTS):
        rs=[r for r in today if norm(at(r,14))==norm(name)]
        shifts.append([name,len(rs),count(rs),percent(count(rs),expected[i] if expected else 0)])
    dependencies=[]
    for name in BASE:
        rs=[r for r in today if dep(at(r,5))==name]
        history=[r for r in records if dep(at(r,5))==name]
        dependencies.append([name,count(rs),count(history),percent(count(history),BASE[name])])
    school=defaultdict(set);area=defaultdict(set)
    for r in today:
        school[(at(r,7),at(r,9))].add(at(r,1))
        area[(at(r,9),at(r,7))].add(at(r,1))
    school_summary=[[s,a,len(ids)] for (s,a),ids in sorted(school.items())]
    area_summary=[[a,s,len(ids)] for (a,s),ids in sorted(area.items())]
    html=f"""<html><body style="font-family:Arial,sans-serif;background:#f3f6fa;color:#153e70;margin:0;padding:20px"><div style="max-width:780px;margin:auto;background:white;padding:22px">
    <div style="background:#153e70;color:white;text-align:center;padding:26px;border-radius:10px"><small>ESCUELA DE MAESTROS · TDD 2027</small><h1>Reporte diario de asistencia</h1><p>{target.strftime('%d/%m/%Y')} · {weekday}</p></div>
    <h2>Indicadores generales</h2>
    {table(["Indicador","Valor"],[["Docentes únicos acumulados",count(records)],["Registros acumulados",len(records)],["Universo de docentes",3853],["Cobertura del universo",percent(count(records),3853)],["Asistencia acumulada",percent(cumulative,cumulative_expected)],["Asistencias de la fecha",len(today)],["Docentes únicos de la fecha",count(today)],["Cobertura de la fecha",percent(count(today),total_expected)]])}
    <h2>Asistencias por turno</h2>{table(["Turno","Registros","Docentes únicos","Cobertura"],shifts)}
    <h2>Dependencias</h2>{table(["Dependencia","Asistieron hoy","Únicos acumulados","Cobertura acumulada"],dependencies)}
    <h2>Docentes asistentes por escuela y área</h2>{table(["Escuela","Área","Docentes únicos"],school_summary)}
    <h2>Docentes asistentes por área y escuela</h2>{table(["Área","Escuela","Docentes únicos"],area_summary)}
    <h2>Archivos para descargar</h2><p>Se adjuntan dos CSV compatibles con Excel, ordenados por escuela y por área. Incluyen el detalle nominal de docentes asistentes de esta fecha. Los archivos no se publican en GitHub Pages.</p>
    <p><a href="https://sebastiangiampani-create.github.io/tdd2027coordi/informes-asistencia.html">Abrir tablero TDD 2027</a></p>
    <p style="font-size:12px;color:#667">Prueba manual, solo destinatario autorizado. Origen: Asistencias y Propuestas (solo lectura).</p></div></body></html>"""
    message=EmailMessage()
    message["From"]=EMAIL;message["To"]=EMAIL
    message["Subject"]=f"[PRUEBA] TDD 2027 - Informe de asistencia {target.strftime('%d/%m/%Y')}"
    message.set_content("Reporte de TDD 2027 en formato HTML con dos archivos adjuntos.")
    message.add_alternative(html,subtype="html")
    for name,key in [("por_escuela",lambda r:(norm(at(r,7)),norm(at(r,9)),norm(at(r,3)))),("por_area",lambda r:(norm(at(r,9)),norm(at(r,7)),norm(at(r,3))))]:
        message.add_attachment(attachment(sorted(today,key=key)),maintype="text",subtype="csv",filename=f"TDD2027_{name}_{target.isoformat()}.csv")
    with smtplib.SMTP_SSL("smtp.gmail.com",465,context=ssl.create_default_context(),timeout=30) as smtp:
        smtp.login(EMAIL,password)
        smtp.send_message(message)
    print(f"Correo de prueba enviado a {EMAIL}; {len(today)} registros para {target.isoformat()}")

if __name__=="__main__": main()
