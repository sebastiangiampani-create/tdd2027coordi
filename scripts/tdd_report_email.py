import csv, io, os, smtplib, ssl, urllib.request, unicodedata, re
from datetime import datetime
from zoneinfo import ZoneInfo
from email.message import EmailMessage
from html import escape
from collections import defaultdict
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
import msoffcrypto

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
    for fmt in ("%d/%m/%Y","%Y-%m-%d","%d/%m/%y","%d/%m/%Y %H:%M:%S","%d/%m/%Y %H:%M","%d/%m","%Y-%m-%d %H:%M:%S"):
        try:
            d=datetime.strptime(v,fmt).date()
            return d.replace(year=2026) if fmt=="%d/%m" else d
        except ValueError: pass
    m=re.search(r"Date\((\d+),(\d+),(\d+)",v)
    if m:
        from datetime import date
        return date(int(m[1]),int(m[2])+1,int(m[3]))
    m=re.match(r"^(\\d{1,2})[/.-](\\d{1,2})(?:[/.-](\\d{2,4}))?",v)
    if m:
        from datetime import date
        y=int(m[3]) if m[3] else 2026
        if y<100:y+=2000
        try:return date(y,int(m[2]),int(m[1]))
        except ValueError:pass
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

def encrypted_workbook(rows, password):
    wb=Workbook()
    details=wb.active
    details.title="Detalle nominal"
    columns=["Fecha","Dependencia","Escuela de pertenencia","Area convocada","Turno","Comision","DNI","Apellido","Nombre","Codigo"]
    details.append(columns)
    for r in rows:
        details.append([at(r,13),dep(at(r,5)),at(r,7),at(r,9),at(r,14),at(r,11),at(r,1),at(r,3),at(r,2),at(r,10)])
    groups=[
        ("Por escuela",lambda r:(at(r,7),at(r,9)),["Escuela","Area","Docentes unicos"]),
        ("Por area",lambda r:(at(r,9),at(r,7)),["Area","Escuela","Docentes unicos"])
    ]
    for name,key,headers in groups:
        ws=wb.create_sheet(name)
        ws.append(headers)
        counts=defaultdict(set)
        for r in rows:
            if at(r,1): counts[key(r)].add(at(r,1))
        for pair,ids in sorted(counts.items()):
            ws.append([pair[0],pair[1],len(ids)])
    for ws in wb.worksheets:
        ws.freeze_panes="A2"
        ws.auto_filter.ref=ws.dimensions
        ws.row_dimensions[1].height=28
        for cell in ws[1]:
            cell.fill=PatternFill("solid",fgColor="153E70")
            cell.font=Font(bold=True,color="FFFFFF")
            cell.alignment=Alignment(vertical="center")
        for col in ws.columns:
            letter=get_column_letter(col[0].column)
            width=min(60,max(14,max(len(str(cell.value or "")) for cell in col[:150])+3))
            ws.column_dimensions[letter].width=width
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.alignment=Alignment(vertical="top",wrap_text=True)
    raw=BytesIO()
    wb.save(raw)
    raw.seek(0)
    protected=BytesIO()
    office=msoffcrypto.OfficeFile(raw)
    office.encrypt(password,protected)
    data=protected.getvalue()
    if not data.startswith(bytes.fromhex("d0cf11e0a1b11ae1")):
        raise RuntimeError("No se pudo verificar el cifrado del archivo Excel; envio cancelado.")
    return data

def main():
    password=os.environ.get("TDD_GMAIL_APP_PASSWORD","").replace(" ","")
    excel_password=os.environ.get("TDD_EXCEL_PASSWORD","")
    if len(excel_password)<12: raise RuntimeError("Falta TDD_EXCEL_PASSWORD o es demasiado corta (minimo 12 caracteres).")
    if not password: raise RuntimeError("Falta TDD_GMAIL_APP_PASSWORD en GitHub Secrets.")
    requested=os.environ.get("REPORT_DATE","").strip()
    target=datetime.strptime(requested,"%Y-%m-%d").date() if requested else datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
    all_rows=read(87091997)
    proposals=read(0)
    if len(proposals)<2 or len(all_rows)<2: raise RuntimeError("Planillas sin datos o inaccesibles; no se envia.")
    records=[r for r in all_rows[1:] if at(r,1)]
    today=[r for r in records if day(at(r,13))==target]
    if not today:
        from collections import Counter
        print("Diagnostic date values (no names):", Counter(at(r,13) for r in records).most_common(8))
        raise RuntimeError("No hay registros reconocidos de la fecha seleccionada; no se envia.")
    weekday=["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"][target.weekday()]
    expected=PLANNED.get(weekday)
    total_expected=sum(expected) if expected else 0
    dates={day(at(r,13)) for r in records if day(at(r,13))}
    cumulative=sum(count([r for r in records if day(at(r,13))==d]) for d in dates)
    cumulative_expected=sum(sum(PLANNED.get(["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"][d.weekday()],[])) for d in dates)
    history=[]
    for d in sorted(dates):
        label=["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"][d.weekday()]
        plan=PLANNED.get(label)
        if not plan: continue
        group=[r for r in records if day(at(r,13))==d]
        history.append((d,len(group),count(group),sum(plan)))
    history_html='<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
    for i,(d,registered,people,planned) in enumerate(history):
        rate=100*people/planned if planned else 0
        if i and i%3==0: history_html+='</tr><tr>'
        history_html+=(
            '<td valign="top" width="33%" style="padding:4px">'
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#edf4fc;border:1px solid #c6d8ee;border-radius:7px">'
            f'<tr><td align="center" style="padding:12px 5px;color:#153e70;font-size:12px">{d.strftime("%d/%m")}</td></tr>'
            f'<tr><td align="center" style="font-size:24px;font-weight:bold;color:#153e70">{registered}</td></tr>'
            '<tr><td align="center" style="font-size:11px;padding:4px">registros</td></tr>'
            f'<tr><td style="padding:8px 7px"><strong style="font-size:15px">{percent(people,planned)}</strong>'
            f'<div style="background:#c6d8ee;height:6px;border-radius:4px"><div style="background:#2677bd;height:6px;width:{min(100,rate):.1f}%;border-radius:4px"></div></div>'
            f'<div style="font-size:10px;padding-top:5px">{people} únicos de {planned} previstos</div></td></tr></table></td>'
        )
    history_html+='</tr></table>'
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
    html=f"""<html><body style="margin:0;padding:18px;background:#f1f5fa;font-family:Arial,Helvetica,sans-serif;color:#183c64">
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="max-width:680px;margin:auto;background:#ffffff">
    <tr><td style="background:#153e70;color:white;padding:24px">
    <div style="font-size:12px;letter-spacing:1px">ESCUELA DE MAESTROS · MINISTERIO DE EDUCACIÓN</div>
    <h1 style="font-size:25px;margin:12px 0 4px">TDD 2027 · Asistencia</h1>
    <div style="font-size:14px">{target.strftime('%d/%m/%Y')} · {weekday}</div></td></tr>
    <tr><td style="padding:20px">
    <table role="presentation" width="100%" cellpadding="10" cellspacing="4">
    <tr><td style="background:#edf4fc"><strong style="font-size:26px">{len(today)}</strong><br><small>Registros del día</small></td>
    <td style="background:#edf4fc"><strong style="font-size:26px">{count(today)}</strong><br><small>Docentes únicos del día</small></td></tr>
    <tr><td style="background:#edf4fc"><strong style="font-size:26px">{percent(count(today),total_expected)}</strong><br><small>Cobertura del día</small></td>
    <td style="background:#edf4fc"><strong style="font-size:26px">{count(records)}</strong><br><small>Docentes únicos acumulados</small></td></tr></table>
    <p style="font-size:13px;color:#566b83">Universo: 3.853 docentes · Cobertura del universo: {percent(count(records),3853)} · Asistencia acumulada: {percent(cumulative,cumulative_expected)}</p>
    <h2 style="font-size:17px">Histórico de asistencia</h2>{history_html}
    <h2 style="font-size:17px">Por turno</h2>{table(["Turno","Registros","Unicos","Cobertura"],shifts)}
    <h2 style="font-size:17px;margin-top:18px">Por dependencia</h2>{table(["Dependencia","Hoy","Unicos acumulados","Cobertura"],dependencies)}
    <p style="font-size:13px;margin-top:20px"><strong>Detalle nominal:</strong> archivo Excel cifrado adjunto, con tres hojas (detalle, escuela y área). La contraseña se comunica por separado.</p>
    <p style="font-size:13px"><a href="https://sebastiangiampani-create.github.io/tdd2027coordi/informes-asistencia.html" style="color:#1761a0">Consultar tablero de asistencia</a></p>
    <p style="font-size:11px;color:#63758a">Reporte generado {datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).strftime('%d/%m/%Y %H:%M')} (Buenos Aires). Datos consultados en modo lectura.</p>
    </td></tr></table></body></html>"""

    message=EmailMessage()
    message["From"]=EMAIL;message["To"]=EMAIL
    message["Subject"]=f"[PRUEBA] TDD 2027 - Informe de asistencia {target.strftime('%d/%m/%Y')}"
    message.set_content("Reporte de TDD 2027 en formato HTML con dos archivos adjuntos.")
    message.add_alternative(html,subtype="html")
    excel=encrypted_workbook(today,excel_password)
    message.add_attachment(excel,maintype="application",subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",filename=f"TDD2027_asistencias_{target.isoformat()}_PROTEGIDO.xlsx")
    with smtplib.SMTP_SSL("smtp.gmail.com",465,context=ssl.create_default_context(),timeout=30) as smtp:
        smtp.login(EMAIL,password)
        smtp.send_message(message)
    print(f"Correo de prueba enviado a {EMAIL}; {len(today)} registros para {target.isoformat()}")

if __name__=="__main__": main()
