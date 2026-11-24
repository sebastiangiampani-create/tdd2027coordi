# TDD 2027 — Formato del correo CCO (referencia inactiva)

**Conservado el 24/11/2026.** Esta carpeta reúne exclusivamente las definiciones del formato del informe anterior. **No ejecuta ni envía correos, no contiene cron ni workflows.**

## Encabezados y destinatarios

- **Asunto:** `Talleres de diseño 2027 - Informe de asistencia DD/MM/AAAA`.
- **Para:** cuenta emisora institucional, sin publicar aquí su credencial.
- **CCO:** listado institucional vigente almacenado en `config/destinatarios.json` (conservar como dato; no implica envío).
- **Texto alternativo:** aviso de que se comparte el informe de asistencia de la fecha con PDF visual y Excel nominal cifrado.
- **Fecha visible:** día y hora de la zona `America/Argentina/Buenos_Aires`, en formato `DD/MM/AAAA`.

## Estructura del HTML original

- Encabezado institucional: Escuela de Maestros y Ministerio de Educación.
- Identificador: `C0890 · TALLERES DE DISEÑO · TDD 2027`.
- Título: «Informe de asistencia».
- Asistencia del día y tarjetas de acumulado, universo, coberturas.
- Asistencia del día por turno; histórico de asistencia; asistencia por dependencia.
- Aviso de detalle nominal cifrado y enlace al tablero de informes.
- Nota metodológica: personas únicas por DNI; firma de diseño y logos institucionales.
- Colores: `#153e70`, `#092b56`, `#12395c`, `#215b98`, `#2677bd`, `#d8e9ff`, `#edf4ff`.
- Tipografía: Arial / Helvetica. Diseño de tabla HTML compatible con clientes de correo, ancho máximo 700 px.
- Logos originales: `assets/em-logo-header.svg`, `assets/em-logo-footer.svg`, `assets/ministerio-footer.svg` (para email se convertían a PNG embebidos).

## Adjuntos previstos

- `TDD2027_informe_visual_AAAA-MM-DD.pdf`: tablero visual A4 del día, acumulado e indicadores; diseño institucional.
- `TDD2027_asistencias_AAAA-MM-DD_PROTEGIDO.xlsx`: archivo cifrado con hojas «Detalle nominal», «Por escuela» y «Por área». Contraseña por canal separado.

## Plantilla HTML original, sin motor de envío

El siguiente bloque es una **referencia textual exacta** de la plantilla HTML dinámica; las expresiones entre llaves eran variables del sistema anterior. No es un ejecutor.

```python
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
      <tr>{metric("Asistencia acumulada",count(records),"Personas distintas en todo el período")}{metric("Universo de docentes","2.591","Base de referencia")}</tr>
      <tr>{metric("Cobertura del día",percent(count(today),total_expected).replace(".",","),f"{count(today)} asistentes de {total_expected} previstos")}{metric("Cobertura del universo",percent(count(records),2591).replace(".",","),f"{count(records)} de 2.591 docentes")}</tr></table>
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
    </td></tr><tr><td style="background:#153e70;padding:17px 20px;text-align:center"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td width="42%" align="left" valign="middle"><img src="cid:em_footer_logo" alt="Escuela de Maestros" width="145" style="display:block;width:145px;max-width:100%;height:auto;border:0"></td><td width="58%" align="right" valign="middle"><img src="cid:ministerio_logo" alt="Ministerio de Educación · Buenos Aires Ciudad" width="225" style="display:block;width:225px;max-width:100%;height:auto;border:0;margin-left:auto"></td></tr></table></td></tr></table></body></html>
```

## Funciones visuales anteriores: tarjetas, tablas e histórico

Referencias de maquetación para reconstruir el informe sin conservar el sistema de SMTP.

```python
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
        rs=[r for r in today if norm(at(r,15))==norm(name)]
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
```

## Referencia de generación visual de PDF y Excel

Código visual anterior, almacenado solo como texto en este documento. No incluye envío de correo.

```python
def encrypted_workbook(rows, password):
    wb=Workbook()
    details=wb.active
    details.title="Detalle nominal"
    columns=["Fecha","Dependencia","Escuela de pertenencia","Area convocada","Turno","Comision","DNI","Apellido","Nombre","Codigo"]
    details.append(columns)
    for r in rows:
        details.append([at(r,14),dep(at(r,5)),at(r,7),at(r,9),at(r,15),at(r,11),at(r,1),at(r,3),at(r,2),at(r,10)])
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


def visual_pdf(records, target, proposals, included_shifts=None, whatsapp_cutoff=False):
    """One-page visual attendance dashboard; all counts are distinct DNI."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor, white
    from reportlab.lib.utils import ImageReader
    from reportlab.lib.units import mm
    from reportlab.lib.pagesizes import A4
    from collections import defaultdict
    output=BytesIO()
    cv=canvas.Canvas(output,pagesize=A4)
    W,H=A4
    navy=HexColor("#12395c")
    blue=HexColor("#174e8a")
    pale=HexColor("#eaf3ff")
    light=HexColor("#f3f7fb")
    muted=HexColor("#526b80")
    def rect(x,y,w,h,fill,r=8,stroke=None):
        cv.setFillColor(fill)
        cv.setStrokeColor(stroke or fill)
        cv.roundRect(x,y,w,h,r,stroke=1 if stroke else 0,fill=1)
    def txt(x,y,s,size=10,bold=False,color=navy):
        cv.setFillColor(color)
        cv.setFont("Helvetica-Bold" if bold else "Helvetica",size)
        cv.drawString(x,y,str(s))
    def bar(x,y,w,value,maximum):
        rect(x,y,w,7,HexColor("#c9dff3"),3)
        if maximum and value:
            rect(x,y,max(3,w*min(value/maximum,1)),7,HexColor("#2677bd"),3)
    def num(items):return count(items)
    shift_names = tuple(included_shifts) if included_shifts is not None else tuple(SHIFTS)
    if not shift_names or any(name not in SHIFTS for name in shift_names):
        raise ValueError("Turnos de informe invalidos")
    relevant=[r for r in records if day(at(r,14)) and day(at(r,14))<=target and norm(at(r,15)) in {norm(name) for name in shift_names}]
    today=[r for r in relevant if day(at(r,14))==target]
    dates=sorted({day(at(r,14)) for r in relevant})
    weekday=["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
    plan=PLANNED.get(weekday[target.weekday()],[])
    expected=sum(plan[i] for i,name in enumerate(SHIFTS) if name in shift_names and i<len(plan))
    daily=num(today)
    accumulated=num(relevant)
    if whatsapp_cutoff:
        current=shift_names[-1]
        current_idx=SHIFTS.index(current)
        current_count=num([r for r in today if norm(at(r,15))==norm(current)])
        current_expected=plan[current_idx] if current_idx<len(plan) else 0
        relevant=[r for r in records if (d:=day(at(r,14))) and (d<target or (d==target and norm(at(r,15)) in {norm(name) for name in shift_names}))]
        accumulated=num(relevant)
    cv.setFillColor(white);cv.rect(0,0,W,H,fill=1,stroke=0)
    rect(0,H-93,W,93,navy,0)
    logo=ImageReader(BytesIO(cairosvg.svg2png(url="assets/em-logo-footer.svg",output_width=500)))
    cv.drawImage(logo,40,H-64,width=132,height=45,mask="auto",preserveAspectRatio=True,anchor="c")
    ministry=ImageReader(BytesIO(cairosvg.svg2png(url="assets/ministerio-footer.svg",output_width=650)))
    cv.drawImage(ministry,W-245,H-59,width=204,height=34,mask="auto",preserveAspectRatio=True,anchor="c")
    txt(40,H-122,"C0890  /  TDD 2027",11,True,blue)
    scope_label = "GENERAL" if len(shift_names)==len(SHIFTS) else " + ".join({"Mañana":"TM","Tarde":"TT","Vespertino":"TV"}[name] for name in shift_names)
    txt(40,H-147,"INFORME DE ASISTENCIA - "+scope_label,19,True,navy)
    txt(40,H-167,"Talleres de Diseño  |  "+target.strftime("%d/%m/%Y"),10,False,muted)
    # Hero
    rect(40,H-298,W-80,113,pale,12,HexColor("#b8d1f2"))
    txt(60,H-208,("ASISTENCIA DEL TURNO "+current.upper()) if whatsapp_cutoff else "ASISTENCIA DEL DIA",11,True,blue)
    txt(59,H-268,str(current_count if whatsapp_cutoff else daily),51,True,navy)
    txt(245,H-249,"asistentes",15,True,navy)
    txt(245,H-268,"de "+str(current_expected if whatsapp_cutoff else expected)+" previstos",10,False,muted)
    # KPI cards
    y=H-393
    cards=[("ASISTENCIA ACUMULADA",str(accumulated),"personas distintas"),
           ("COBERTURA DEL DIA",percent(daily,expected),"sobre previstos"),
           (("COBERTURA DEL UNIVERSO",percent(accumulated,2591),"de 2.591 docentes") if len(shift_names)==len(SHIFTS) else ("TURNOS INCLUIDOS",scope_label,"corte parcial"))]
    if whatsapp_cutoff:
        cards=[("TOTAL DEL DIA",str(daily),"DNI unicos"),("COBERTURA DEL DIA",percent(daily,expected),"de "+str(expected)+" previstos"),("COBERTURA UNIVERSO",percent(accumulated,2591),str(accumulated)+" de 2.591 docentes")]
    gap=9
    cardw=(W-80-gap*2)/3
    for i,(label,value,detail) in enumerate(cards):
        x=40+i*(cardw+gap)
        rect(x,y,cardw,80,light,8,HexColor("#d8e5f0"))
        txt(x+12,y+60,label,8,True,muted)
        txt(x+12,y+30,value,24,True,navy)
        txt(x+12,y+14,detail,8,False,muted)
    # History
    hy=H-422
    txt(40,hy,"HISTORICO DE ASISTENCIA",12,True,navy)
    history=dates[-5:]
    max_history=max([num([r for r in relevant if day(at(r,14))==d]) for d in history] or [1])
    for i,d in enumerate(history):
        ry=hy-31-i*30
        group=[r for r in relevant if day(at(r,14))==d]
        n=num(group)
        exp=sum(PLANNED.get(weekday[d.weekday()],[])[i] for i,name in enumerate(SHIFTS) if name in shift_names and i<len(PLANNED.get(weekday[d.weekday()],[])))
        txt(42,ry,d.strftime("%d/%m"),9,True,navy)
        bar(99,ry-1,310,n,max_history)
        txt(424,ry,str(n),10,True,navy)
        txt(466,ry,percent(n,exp),9,False,muted)
    # Turnos and dependencies side by side
    lower=hy-31-len(history)*30-25
    txt(40,lower,"ASISTENCIA POR TURNO",11,True,navy)
    txt(318,lower,"POR DEPENDENCIA",11,True,navy)
    for i,name in enumerate(SHIFTS):
        n=num([r for r in today if norm(at(r,15))==norm(name)]) if name in shift_names else 0
        exp=plan[i] if i<len(plan) and name in shift_names else 0
        yy=lower-28-i*36
        txt(41,yy,name,9,True,navy)
        bar(113,yy-2,92,n,exp)
        txt(212,yy,str(n),10,True,navy)
        txt(245,yy,percent(n,exp),8,False,muted)
    for i,(name,universe) in enumerate(BASE.items()):
        n=num([r for r in today if dep(at(r,5))==name])
        yy=lower-28-i*29
        txt(319,yy,name,9,True,navy)
        bar(364,yy-2,104,n,max(1,daily))
        txt(478,yy,str(n),10,True,navy)
    rect(40,73,W-80,42,light,6)
    txt(52,97,"La asistencia se calcula en base a DNI unicos.",9,True,navy)
    txt(52,82,"Cada persona se cuenta una sola vez por jornada.",8,False,muted)
    txt(40,54,"Reporte de asistencia creado y diseñado por Sebastian Giampani",8,False,muted)
    rect(0,0,W,35,navy,0)
    txt(40,14,"ESCUELA DE MAESTROS  /  MINISTERIO DE EDUCACION  /  TDD 2027",8,True,white)
    cv.showPage()
    cv.save()
    return output.getvalue()
```

## Estado

**Inactivo.** Para volver a empezar, diseñar un nuevo disparador, generador y mecanismo de envío por separado. Los secretos de GitHub y los archivos de datos no se han modificado en esta limpieza.
