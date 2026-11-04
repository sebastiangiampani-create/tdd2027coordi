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


def visual_pdf(records, target):
    """Resumen imprimible sin datos nominales; todas las cifras son DNI unicos."""
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.units import mm
    from collections import defaultdict

    blue=colors.HexColor("#153e70")
    light=colors.HexColor("#eaf2fb")
    ink=colors.HexColor("#12395c")
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TDDTitle",parent=styles["Title"],fontName="Helvetica-Bold",fontSize=16,leading=20,textColor=blue,spaceAfter=9))
    styles.add(ParagraphStyle(name="TDDSection",parent=styles["Heading2"],fontSize=11,leading=14,textColor=blue,spaceBefore=13,spaceAfter=6))
    styles.add(ParagraphStyle(name="TDDSmall",parent=styles["Normal"],fontSize=8,leading=12,textColor=ink))
    styles.add(ParagraphStyle(name="TDDCenter",parent=styles["Normal"],fontSize=9,leading=13,alignment=TA_CENTER,textColor=ink))
    out=BytesIO()
    doc=SimpleDocTemplate(out,pagesize=(210*mm,297*mm),leftMargin=14*mm,rightMargin=14*mm,topMargin=13*mm,bottomMargin=15*mm)
    width=182*mm
    def grid(data,widths=None,header=True):
        t=Table(data,colWidths=widths or [width/len(data[0])]*len(data[0]),repeatRows=1 if header else 0,hAlign="LEFT")
        commands=[("VALIGN",(0,0),(-1,-1),"MIDDLE"),("BOTTOMPADDING",(0,0),(-1,-1),7),("TOPPADDING",(0,0),(-1,-1),7),("LINEBELOW",(0,0),(-1,-1),.35,colors.HexColor("#c8d9ed")),("TEXTCOLOR",(0,0),(-1,-1),ink),("FONTSIZE",(0,0),(-1,-1),8)]
        if header:commands += [("BACKGROUND",(0,0),(-1,0),blue),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold")]
        t.setStyle(TableStyle(commands))
        return t
    def ids(items):return count(items)
    def title(txt):return Paragraph(txt,styles["TDDSection"])
    def date_label(d):return d.strftime("%d/%m/%Y")
    story=[]
    logo_png=cairosvg.svg2png(url="assets/em-logo-header.svg",output_width=500)
    logo=Image(BytesIO(logo_png),width=62*mm,height=8.4*mm)
    story.extend([logo,Spacer(1,8*mm),Paragraph("C0890 · TDD 2027 · Informe general de asistencia",styles["TDDTitle"]),
                  Paragraph("Talleres de Diseño · Fecha del informe: "+date_label(target),styles["TDDSmall"]),Spacer(1,5*mm)])
    observed=sorted({day(at(r,13)) for r in records if day(at(r,13)) and day(at(r,13))<=target})
    relevant=[r for r in records if day(at(r,13)) and day(at(r,13))<=target]
    today=[r for r in relevant if day(at(r,13))==target]
    plan=PLANNED.get(["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"][target.weekday()],[])
    total_plan=sum(plan)
    stats=[["Asistencia del día","Asistencia acumulada","Cobertura del día","Cobertura del universo"],
           [str(ids(today)),str(ids(relevant)),percent(ids(today),total_plan),percent(ids(relevant),3853)]]
    story.append(grid(stats,header=True))
    story.append(Paragraph("Universo de referencia: 3.853 docentes. La asistencia se calcula en base a DNI únicos.",styles["TDDSmall"]))
    story.append(title("Asistencia por fecha"))
    date_rows=[["Fecha","Asistentes","Previstos","Cobertura"]]
    for d in observed:
        group=[r for r in relevant if day(at(r,13))==d]
        expected=sum(PLANNED.get(["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"][d.weekday()],[]))
        date_rows.append([date_label(d),str(ids(group)),str(expected) if expected else "—",percent(ids(group),expected)])
    story.append(grid(date_rows))
    story.append(title("Asistencia del día por turno"))
    turn_rows=[["Turno","Asistentes","Previstos","Cobertura"]]
    for i,name in enumerate(SHIFTS):
        n=ids([r for r in today if norm(at(r,14))==norm(name)])
        expected=plan[i] if i<len(plan) else 0
        turn_rows.append([name,str(n),str(expected) if expected else "—",percent(n,expected)])
    story.append(grid(turn_rows))
    story.append(title("Asistencia del día por dependencia"))
    dep_rows=[["Dependencia","Asistentes","Universo","Cobertura acumulada"]]
    for name,universe in BASE.items():
        n=ids([r for r in today if dep(at(r,5))==name])
        accumulated=ids([r for r in relevant if dep(at(r,5))==name])
        dep_rows.append([name,str(n),str(universe),percent(accumulated,universe)])
    story.append(grid(dep_rows))
    story.append(title("Asistencia por fecha y sede"))
    story.append(Paragraph("Los datos de sede se obtienen de la planilla Propuestas. El detalle nominal permanece en el Excel cifrado.",styles["TDDSmall"]))
    story.append(Spacer(1,5*mm))
    story.append(Paragraph("Reporte de asistencia creado y diseñado por Sebastian Giampani",styles["TDDCenter"]))
    def footer(canvas,document):
        canvas.setFillColor(blue);canvas.rect(0,0,210*mm,10*mm,fill=1,stroke=0)
        canvas.setFillColor(colors.white);canvas.setFont("Helvetica",7)
        canvas.drawCentredString(105*mm,4*mm,"ESCUELA DE MAESTROS  ·  MINISTERIO DE EDUCACION  ·  TDD 2027")
        canvas.setFillColor(ink);canvas.drawRightString(196*mm,12*mm,str(document.page))
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    return out.getvalue()

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
        history.append((d,count(group),sum(plan)))
    def history_card(d,people,planned,active):
        rate=100*people/planned if planned else 0
        bg="#d8e9ff" if active else "#edf4ff"
        border="#174e8a" if active else "#b8d1f2"
        return (
            f'<td width="33%" valign="top" style="padding:4px">'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{bg};border:1px solid {border};border-radius:9px">'
            f'<tr><td align="center" style="padding:12px 4px 3px;font-size:12px;color:#12395c">{d.strftime("%d/%m")}</td></tr>'
            f'<tr><td align="center" style="font-size:28px;font-weight:700;color:#092b56">{people}</td></tr>'
            '<tr><td align="center" style="font-size:11px;color:#526b80;padding:2px 4px 10px">asistentes</td></tr>'
            f'<tr><td style="padding:10px 8px;border-top:1px solid #c8d9ed"><strong style="font-size:16px;color:#092b56">{percent(people,planned).replace(".",",")}</strong>'
            f'<div style="background:#c6d8ee;height:7px;border-radius:4px;margin:6px 0"><div style="background:#2677bd;height:7px;width:{min(100,rate):.1f}%;border-radius:4px"></div></div>'
            f'<div style="font-size:10px;color:#526b80">{people} asistentes de {planned} previstos</div></td></tr></table></td>'
        )
    history_html='<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
    for i,(d,people,planned) in enumerate(history):
        if i and i%3==0: history_html+='</tr><tr>'
        history_html+=history_card(d,people,planned,d==target)
    history_html+='</tr></table>'
    shifts=[]
    for i,name in enumerate(SHIFTS):
        rs=[r for r in today if norm(at(r,14))==norm(name)]
        shifts.append([name,count(rs),percent(count(rs),expected[i] if expected else 0)])
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
    def metric(label,value,sub,featured=False):
        size=44 if featured else 30
        bg="#d8e9ff" if featured else "#edf3f8"
        border="#8bb4e0" if featured else "#dce5ed"
        return (f'<td width="50%" valign="top" style="padding:5px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{bg};border:1px solid {border};border-radius:11px">'
                f'<tr><td style="padding:17px 14px"><div style="font-size:{size}px;line-height:1.1;font-weight:700;color:#092b56">{value}</div><div style="font-size:14px;font-weight:700;color:#12395c;margin-top:8px">{label}</div><div style="font-size:11px;color:#526b80;margin-top:5px">{sub}</div></td></tr></table></td>')
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
      <span style="float:right;color:#153e70;font-size:12px;font-weight:700;padding-top:12px">MINISTERIO DE EDUCACIÓN</span>
    </td></tr>
    <tr><td style="padding:18px 20px 5px">
      <div style="font-size:12px;font-weight:700;color:#215b98">C0890 · TALLERES DE DISEÑO · TDD 2027</div>
      <h1 style="font-size:23px;line-height:1.2;margin:8px 0;color:#092b56">Informe de asistencia</h1>
      <div style="font-size:13px;color:#526b80">{weekday} {target.strftime('%d/%m/%Y')} · Actualizado {datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).strftime('%H:%M')} h</div>
    </td></tr>
    <tr><td style="padding:8px 15px 18px">
      <h2 style="font-size:16px;margin:6px 5px 8px;color:#12395c">Asistencia del día</h2>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
      <tr><td style="padding:5px">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#d8e9ff;border:2px solid #8bb4e0;border-radius:11px"><tr>
          <td style="padding:18px 20px">
            <div style="font-size:55px;line-height:1.05;font-weight:700;color:#092b56">{count(today)}</div>
            <div style="font-size:17px;font-weight:700;color:#12395c;margin-top:8px">Asistentes del día</div>
          </td></tr></table>
      </td></tr></table>
      <h2 style="font-size:16px;margin:16px 5px 8px;color:#12395c">Acumulado y cobertura</h2>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
      <tr>{metric("Asistencia acumulada",count(records),"Personas distintas en todo el período")}{metric("Universo de docentes","3.853","Base de referencia")}</tr>
      <tr>{metric("Cobertura del día",percent(count(today),total_expected).replace(".",","),f"{count(today)} asistentes de {total_expected} previstos")}{metric("Cobertura del universo",percent(count(records),3853).replace(".",","),f"{count(records)} de 3.853 docentes")}</tr></table>
      <div style="padding:9px 6px;font-size:12px;color:#526b80">Asistencia acumulada por jornada: <strong style="color:#092b56">{percent(cumulative,cumulative_expected).replace(".",",")}</strong> · Se contabiliza cada asistente una vez por jornada; puede asistir en días diferentes.</div>
      <h2 style="font-size:16px;margin:19px 5px 9px;color:#12395c">Asistencia del día por turno</h2>
      {bar_table(["Turno","Asistentes","Cobertura"],shifts,2)}
      <h2 style="font-size:16px;margin:19px 5px 9px;color:#12395c">Histórico de asistencia</h2>
      {history_html}
      <h2 style="font-size:16px;margin:19px 5px 9px;color:#12395c">Asistencia por dependencia</h2>
      {bar_table(["Dependencia","Hoy","Acumulado","Cobertura"],dependencies,3)}
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:19px;background:#edf4ff;border:1px solid #b8d1f2;border-radius:9px"><tr><td style="padding:12px 14px;font-size:12px">
      <strong>Detalle de asistentes · Excel protegido</strong><div style="margin-top:5px;color:#526b80">Adjunto cifrado con tres hojas: detalle nominal, por escuela y por área. La contraseña se entrega por separado.</div>
      </td></tr></table>
      <p style="font-size:12px;margin:15px 5px"><a href="https://sebastiangiampani-create.github.io/tdd2027coordi/informes-asistencia.html" style="color:#174e8a;font-weight:700">Abrir el tablero de asistencia</a></p>
      <p style="font-size:11px;color:#526b80;margin:12px 5px 0"><strong>Nota metodológica:</strong> La asistencia se calcula en base a DNI únicos. Cada persona se cuenta una sola vez por jornada.</p>
      <p style="font-size:10px;color:#667c8e;margin:12px 5px 0">Reporte de prueba · Consulta de planillas en modo lectura · Datos sujetos a actualización</p>
      <p style="font-size:10px;color:#667c8e;margin:8px 5px 0;text-align:center">Reporte de asistencia creado y diseñado por Sebastian Giampani</p>
    </td></tr><tr><td style="background:#153e70;padding:17px 20px;text-align:center"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td width="42%" align="left" valign="middle"><img src="cid:em_footer_logo" alt="Escuela de Maestros" width="145" style="display:block;width:145px;max-width:100%;height:auto;border:0"></td><td width="58%" align="right" valign="middle"><img src="cid:ministerio_logo" alt="Ministerio de Educación · Buenos Aires Ciudad" width="225" style="display:block;width:225px;max-width:100%;height:auto;border:0;margin-left:auto"></td></tr></table></td></tr></table></body></html>"""

    message=EmailMessage()
    message["From"]=EMAIL;message["To"]=EMAIL
    message["Subject"]=f"[PRUEBA] TDD 2027 - Informe de asistencia {target.strftime('%d/%m/%Y')}"
    message.set_content("Reporte de TDD 2027 en HTML, PDF visual y Excel cifrado adjuntos.")
    message.add_alternative(html,subtype="html")
    # Gmail no renderiza SVG de forma fiable: convertir los logos del portal a PNG
    # e incrustarlos como imagenes relacionadas (CID), sin depender de enlaces externos.
    html_part=message.get_payload()[-1]
    for logo_path,cid in [(logo_header,"em_logo"),("assets/em-logo-footer.svg","em_footer_logo"),(logo_ministry,"ministerio_logo")]:
        svg=Path(logo_path)
        if not svg.is_file(): raise RuntimeError(f"Logo institucional ausente: {logo_path}")
        png=cairosvg.svg2png(bytestring=svg.read_bytes(),output_width=420)
        html_part.add_related(png,maintype="image",subtype="png",cid=f"<{cid}>",filename=svg.stem+".png")

    pdf=visual_pdf(records,target)
    if not pdf.startswith(b"%PDF-"): raise RuntimeError("PDF visual invalido; envio cancelado.")
    message.add_attachment(pdf,maintype="application",subtype="pdf",filename=f"TDD2027_informe_visual_{target.isoformat()}.pdf")
    excel=encrypted_workbook(today,excel_password)
    message.add_attachment(excel,maintype="application",subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",filename=f"TDD2027_asistencias_{target.isoformat()}_PROTEGIDO.xlsx")
    with smtplib.SMTP_SSL("smtp.gmail.com",465,context=ssl.create_default_context(),timeout=30) as smtp:
        smtp.login(EMAIL,password)
        smtp.send_message(message)
    print(f"Correo de prueba enviado a {EMAIL}; {len(today)} registros para {target.isoformat()}")

if __name__=="__main__": main()
