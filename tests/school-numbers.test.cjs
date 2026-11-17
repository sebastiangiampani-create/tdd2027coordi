const {test}=require('node:test'),assert=require('node:assert/strict'),N=require('../assets/school-numbers.js'),X=require('../consultor-tdd/assets/cross.js').TDDCross,fs=require('fs'),path=require('path');
function source(){const head=['Dependencia','Escuela','Área','Esperados (POF)','Enc. 1','% Enc. 1','Enc. 2','% Enc. 2','Enc. 3','% Enc. 3','Enc. 4','% Enc. 4','Asistieron (≥1 enc.)'];const row=(dep,school,area,n,a,b,any)=>[dep,school,area,n,a,'',b,'',0,'',0,'',any];const rows=[['Título'],[],head,row('TOTAL GENERAL','','',10,5,3,6),row('DET','TOTAL DET','',6,3,2,4),row('DET','ET. RAGGIO','TOTAL ESCUELA',6,3,2,4),row('DET','ET. RAGGIO','Ciencias Sociales',4,2,1,3),row('DET','ET. RAGGIO','Artes',2,1,1,1),row('DEM','COLEGIO 7 - J.M. PUEYRREDÓN DE 3º','Artes',4,2,1,2)];rows[3][15]='Esc. Técnicas Raggio';rows[3][16]='Artes';rows[3][17]=1;rows[3][18]=1;rows[3][19]=0;const shifts=[['Título'],[],['Turno','Área','Esperados (POF)'],['TOTAL GENERAL','',10,5,'',3,'',0,'',0,'',6],['TARDE','TOTAL TURNO',10,5,'',3,'',0,'',0,'',6],['TARDE','Ciencias Sociales',4,2,'',1,'',0,'',0,'',3],['TARDE','Artes',6,3,'',2,'',0,'',0,'',3]];const metadata=[[],[],[],Object.assign([],{14:'Dirección de Educación Técnica',15:'Esc. Técnicas Raggio'})];return {rows,shifts,metadata}}
function fixture(){const f=source();return N.parse(f.rows,f.shifts,f.metadata,X)}
test('lee solo hojas de resumen y excluye totales para no duplicar cantidades',()=>{const d=fixture();assert.equal(d.details.length,3);assert.deepEqual(N.sum(d.details),{expected:10,e1:5,e2:3,e3:0,e4:0,any:6});assert.equal(N.sum(d.outside).any,1);assert.equal(N.group(d.details,['school']).length,2)});
test('los filtros de escuela, área y dependencia afectan tablas, totales y fuera de padrón',()=>{const d=fixture();const r=N.select(d,{school:X.school('Esc. Técnicas Raggio'),area:X.areaKey('Artes'),dependency:'DET'});assert.equal(r.total.expected,2);assert.equal(r.total.any,1);assert.equal(r.outsideTotal.any,1);assert.equal(N.select(d,{dependency:'DEM'}).outside.length,0)});
test('el resumen por turno tiene su propio alcance y no inventa cruces por escuela',()=>{const r=N.select(fixture(),{view:'shift',shift:'TARDE',dependency:'DEM',school:'irrelevant',area:X.areaKey('Artes')});assert.equal(r.total.expected,6);assert.equal(r.outsideAvailable,false);assert.equal(r.outside.length,0)});
test('se detectan resúmenes filtrados o incompletos y cambios de encabezados',()=>{const f=source();f.rows.pop();assert.throws(()=>N.parse(f.rows,f.shifts,f.metadata,X),/incompleto/);const g=source();g.shifts.pop();assert.throws(()=>N.parse(g.rows,g.shifts,g.metadata,X),/no coincide/)});
test('CSV admite comas, saltos y comillas; cantidades no válidas no se convierten en ceros',()=>{assert.deepEqual(N.csv('A,B\n"Una, escuela","Dos ""áreas"""\n'),[['A','B'],['Una, escuela','Dos "áreas"']]);assert.equal(N.count('2.591'),2591);assert.throws(()=>N.count('sin dato'));assert.throws(()=>N.csv('A,"incompleto'))});
test('el tablero solo solicita las tres hojas agregadas del archivo nuevo',()=>{const s=fs.readFileSync(path.join(__dirname,'../assets/school-dashboard.js'),'utf8');assert.match(s,/1djc57JJz-pdqmLHV8x45QO_jhM8XWI76k0OdhZ5Lg3E/);assert.match(s,/\[\['schools','201'\],\['shifts','204'\],\['metadata','202'\]\]/);assert(!/1hznlu4j|1x-cRhs|Base convocados|Base no convocados/.test(s));assert(!/DNI|Apellido|Nombre/.test(s))});
test('conserva fuera de padrón al seleccionar las dos etiquetas de Escuela de la Ribera de esta fuente',()=>{const f=source();for(const r of f.rows){if(r[1]==='ET. RAGGIO'){r[0]='DEM';r[1]='EEM 7 - ESCUELA DE LA RIBERA'}}f.rows[3][15]='Esc. de Educacion Media N° 07/04° Escuela de la Ribera';f.metadata[3][14]='Dirección de Educación Media';f.metadata[3][15]=f.rows[3][15];const d=N.parse(f.rows,f.shifts,f.metadata,X),id=d.details.find(r=>r.school.includes('RIBERA')).schoolId;assert.equal(N.select(d,{school:id}).outsideTotal.any,1)});

test('participación unificada utiliza el mismo numerador en total y porcentaje',()=>{
 const registered={expected:2,any:1,e1:1,e2:1,e3:0,e4:0};
 const outside={any:1,e1:1,e2:1,e3:0,e4:0};
 const merged=N.combine(registered,outside);
 assert.equal(merged.expected,2);assert.equal(merged.any,2);assert.equal(N.ratio(merged.any,merged.expected),100);
 assert.equal(merged.e1,2);assert.equal(merged.e2,2);
 assert.equal(N.ratio(registered.any,registered.expected),50);
});
test('participación sobre POF puede superar 100 % y sin POF no hay porcentaje',()=>{
 const merged=N.combine({expected:1,any:1,e1:1},{any:2,e1:2});
 assert.equal(merged.any,3);assert.equal(N.ratio(merged.any,merged.expected),300);
 assert.equal(N.ratio(3,0),null);
});
