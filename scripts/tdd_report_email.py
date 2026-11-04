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
import cairosvg
from pathlib import Path

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
    def history_card(d,registered,people,planned,active):
        rate=100*people/planned if planned else 0
        bg="#d8e9ff" if active else "#edf4ff"
        border="#174e8a" if active else "#b8d1f2"
        return (
            f'<td width="33%" valign="top" style="padding:4px">'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{bg};border:1px solid {border};border-radius:9px">'
            f'<tr><td align="center" style="padding:12px 4px 3px;font-size:12px;color:#12395c">{d.strftime("%d/%m")}</td></tr>'
            f'<tr><td align="center" style="font-size:28px;font-weight:700;color:#092b56">{registered}</td></tr>'
            '<tr><td align="center" style="font-size:11px;color:#526b80;padding:2px 4px 10px">registros</td></tr>'
            f'<tr><td style="padding:10px 8px;border-top:1px solid #c8d9ed"><strong style="font-size:16px;color:#092b56">{percent(people,planned).replace(".",",")}</strong>'
            f'<div style="background:#c6d8ee;height:7px;border-radius:4px;margin:6px 0"><div style="background:#2677bd;height:7px;width:{min(100,rate):.1f}%;border-radius:4px"></div></div>'
            f'<div style="font-size:10px;color:#526b80">{people} únicos de {planned} previstos</div></td></tr></table></td>'
        )
    history_html='<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
    for i,(d,registered,people,planned) in enumerate(history):
        if i and i%3==0: history_html+='</tr><tr>'
        history_html+=history_card(d,registered,people,planned,d==target)
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
    def metric(label,value,sub):
        return (f'<td width="50%" valign="top" style="padding:5px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#edf3f8;border:1px solid #dce5ed;border-radius:11px">'
                f'<tr><td style="padding:13px 14px"><div style="font-size:27px;font-weight:700;color:#092b56">{value}</div><div style="font-size:12px;color:#12395c;margin-top:4px">{label}</div><div style="font-size:10px;color:#526b80;margin-top:5px">{sub}</div></td></tr></table></td>')
    def bar_table(headers,records,rate_index):
        out='<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-size:12px">'
        out+='<tr>'+''.join(f'<th align="left" style="padding:8px 7px;background:#eaf1f7;color:#12395c;border-bottom:1px solid #dce5ed">{escape(str(x))}</th>' for x in headers)+'</tr>'
        for row in records:
            out+='<tr>'
            for i,v in enumerate(row):
                if i==rate_index:
                    try: p=float(str(v).replace("%","").replace(",",".")) 
                    except ValueError:p=0
                    content=(f'<strong style="color:#092b56">{escape(str(v).replace(".",","))}</strong>'
                             f'<div style="height:6px;background:#c6d8ee;border-radius:4px;margin-top:5px"><div style="height:6px;width:{min(100,p):.1f}%;background:#2677bd;border-radius:4px"></div></div>')
                else:content=escape(str(v))
                out+=f'<td valign="middle" style="padding:10px 7px;border-bottom:1px solid #e0e8ed;color:#12395c">{content}</td>'
            out+='</tr>'
        return out+'</table>'
    logo_header='assets/em-logo-header.svg'
    logo_ministry='assets/ministerio-footer.svg'
    html=f"""<html><body style="margin:0;padding:14px;background:#f3f6fa;font-family:Arial,Helvetica,sans-serif;color:#12395c">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:700px;margin:auto;background:#ffffff;border:1px solid #dce5ed;border-radius:12px">
    <tr><td style="padding:18px 20px;border-bottom:1px solid #dce5ed">
      <img src="cid:em_logo" alt="Escuela de Maestros" width="170" style="max-width:45%;height:auto;vertical-align:middle;border:0">
      <img src="cid:ministerio_logo" alt="Ministerio de Educación" width="160" style="max-width:43%;height:auto;vertical-align:middle;float:right;border:0">
    </td></tr>
    <tr><td style="padding:18px 20px 5px">
      <div style="font-size:12px;font-weight:700;color:#215b98">C0890 · TALLERES DE DISEÑO · TDD 2027</div>
      <h1 style="font-size:23px;line-height:1.2;margin:8px 0;color:#092b56">Informe de asistencia</h1>
      <div style="font-size:13px;color:#526b80">{weekday} {target.strftime('%d/%m/%Y')} · Actualizado {datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).strftime('%H:%M')} h</div>
    </td></tr>
    <tr><td style="padding:8px 15px 18px">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
      <tr>{metric("Registros del día",len(today),"Asistencias registradas")}{metric("Docentes únicos del día",count(today),"DNI sin duplicados en la jornada")}</tr>
      <tr>{metric("Cobertura del día",percent(count(today),total_expected).replace(".",","),f"{count(today)} únicos de {total_expected} previstos")}{metric("Docentes únicos acumulados",count(records),f"{percent(count(records),3853).replace('.',',')} del universo de 3.853")}</tr></table>
      <div style="padding:7px 6px;font-size:12px;color:#526b80">Asistencia acumulada: <strong style="color:#092b56">{percent(cumulative,cumulative_expected).replace(".",",")}</strong> · Registros acumulados: <strong>{len(records)}</strong></div>
      <h2 style="font-size:16px;margin:17px 5px 8px;color:#12395c">Histórico de asistencia</h2>
      {history_html}
      <h2 style="font-size:16px;margin:19px 5px 9px;color:#12395c">Asistencia por turno</h2>
      {bar_table(["Turno","Registros","Únicos","Cobertura"],shifts,3)}
      <h2 style="font-size:16px;margin:19px 5px 9px;color:#12395c">Asistencia por dependencia</h2>
      {bar_table(["Dependencia","Hoy","Únicos acumulados","Cobertura"],dependencies,3)}
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:19px;background:#edf4ff;border:1px solid #b8d1f2;border-radius:9px"><tr><td style="padding:12px 14px;font-size:12px">
      <strong>Detalle de asistentes · Excel protegido</strong><div style="margin-top:5px;color:#526b80">Adjunto cifrado con tres hojas: detalle nominal, por escuela y por área. La contraseña se entrega por separado.</div>
      </td></tr></table>
      <p style="font-size:12px;margin:15px 5px"><a href="https://sebastiangiampani-create.github.io/tdd2027coordi/informes-asistencia.html" style="color:#174e8a;font-weight:700">Abrir el tablero de asistencia</a></p>
      <p style="font-size:10px;color:#667c8e;margin:12px 5px 0">Reporte de prueba · Consulta de planillas en modo lectura · Datos sujetos a actualización</p>
    </td></tr></table></body></html>"""

    message=EmailMessage()
    message["From"]=EMAIL;message["To"]=EMAIL
    message["Subject"]=f"[PRUEBA] TDD 2027 - Informe de asistencia {target.strftime('%d/%m/%Y')}"
    message.set_content("Reporte de TDD 2027 en formato HTML con dos archivos adjuntos.")
    message.add_alternative(html,subtype="html")
    # Gmail no renderiza SVG de forma fiable: convertir los logos del portal a PNG
    # e incrustarlos como imagenes relacionadas (CID), sin depender de enlaces externos.
    html_part=message.get_payload()[-1]
    for logo_path,cid in [(logo_header,"em_logo"),(logo_ministry,"ministerio_logo")]:
        svg=Path(logo_path)
        if not svg.is_file(): raise RuntimeError(f"Logo institucional ausente: {logo_path}")
        png=cairosvg.svg2png(bytestring=svg.read_bytes(),output_width=420)
        html_part.add_related(png,maintype="image",subtype="png",cid=f"<{cid}>",filename=svg.stem+".png")

    excel=encrypted_workbook(today,excel_password)
    message.add_attachment(excel,maintype="application",subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",filename=f"TDD2027_asistencias_{target.isoformat()}_PROTEGIDO.xlsx")
    with smtplib.SMTP_SSL("smtp.gmail.com",465,context=ssl.create_default_context(),timeout=30) as smtp:
        smtp.login(EMAIL,password)
        smtp.send_message(message)
    print(f"Correo de prueba enviado a {EMAIL}; {len(today)} registros para {target.isoformat()}")

if __name__=="__main__": main()
