"""Utilidades de lectura de asistencia TDD 2027, sin correo ni SMTP."""
import csv, io, unicodedata, re, urllib.request
from datetime import datetime

SID="1hznlu4j_Ip4KqYNpMrdhvbJvnHrPl0hOIJ6qBOsTRb4"
PLANNED={"Lunes":[264,137,164],"Martes":[202,176,121],"Miércoles":[313,231,216],"Jueves":[168,133,54],"Viernes":[160,150,102]}
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
    """Parse the date from column O, never infer a date from an encounter label."""
    from datetime import date
    v=str(v).strip()
    if not v: return None
    for fmt in ("%d/%m/%Y","%Y-%m-%d","%d/%m/%y","%d/%m/%Y %H:%M:%S","%d/%m/%Y %H:%M","%Y-%m-%d %H:%M:%S"):
        try: return datetime.strptime(v,fmt).date()
        except ValueError: pass
    m=re.fullmatch(r"(\d{1,2})[/.-](\d{1,2})",v)
    if m:
        try: return date(2026,int(m[2]),int(m[1]))
        except ValueError: return None
    m=re.search(r"Date\((\d+),(\d+),(\d+)",v)
    if m:
        try: return date(int(m[1]),int(m[2])+1,int(m[3]))
        except ValueError: return None
    m=re.match(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})(?:\s|$)",v)
    if m:
        y=int(m[3]); y=y+2000 if y<100 else y
        try: return date(y,int(m[2]),int(m[1]))
        except ValueError: return None
    return None

def count(rs): return len({at(r,1) for r in rs if at(r,1)})
def percent(n,d): return f"{100*n/d:.1f}%" if d else "Sin referencia"
