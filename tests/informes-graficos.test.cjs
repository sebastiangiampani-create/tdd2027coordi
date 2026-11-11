const {test}=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
const source=fs.readFileSync(require('node:path').join(__dirname,'../informes-asistencia.html'),'utf8');
class Element{constructor(tag){this.tagName=tag;this.children=[];this.style={};this.attributes={};this.textContent='';this.value='';}append(...nodes){this.children.push(...nodes)}replaceChildren(...nodes){this.children=nodes;this.textContent=''}setAttribute(k,v){this.attributes[k]=v}addEventListener(){}}
function app(rows,type='horizontal',report='sede'){
 const els=new Map();const $=id=>{if(!els.has(id))els.set(id,new Element('div'));return els.get(id)};$('chartType').value=type;$('reportType').value=report;
 const document={createElement:t=>new Element(t),createElementNS:(_,t)=>new Element(t),createDocumentFragment:()=>new Element('fragment')};
 const context=vm.createContext({document,$,filtered:rows,clean:v=>String(v??'').trim(),dni:r=>String(r[1]??'').replace(/\D/g,''),dateOnly:v=>v,shift:v=>v,countUnique:r=>new Set(r.map(x=>String(x[1])).filter(Boolean)).size,reportSort:{column:-1,ascending:false}});
 vm.runInContext(source.slice(source.indexOf('const REPORT_DEFS='),source.indexOf("$('chartType').addEventListener")),context);vm.runInContext('renderReports()',context);return {els,$,context};
}
function row(id,venue,date='02/11'){const r=Array(16).fill('');r[1]=id;r[15]=venue;r[13]=date;r[14]='Tarde';return r}
function text(el){return String(el.textContent)+el.children.map(text).join('')}
function all(el){return [el,...el.children.flatMap(all)]}
test('registros y DNI únicos ocupan sus columnas; gráficos usan DNI únicos',()=>{
 for(const type of ['horizontal','vertical','pie','donut','line']){
  const {$,context}=app([row('1','Sede A'),row('1','Sede A'),row('2','Sede A'),row('1','Sede B')],type);
  const data=JSON.parse(vm.runInContext('JSON.stringify(reportTableData)',context));assert.deepEqual(data,[['Sede A',3,2],['Sede B',1,1]]);
  assert.equal(text($('reportFoot')),'TOTAL42');assert(!/NaN|undefined/.test(text($('reportChart'))));
  assert(!/NaN|undefined/.test(JSON.stringify(all($('reportChart')).map(n=>n.style))));assert($('reportChart').children.length>0);
 }
});
test('se incluyen más de doce grupos y las etiquetas no incorporan cantidades',()=>{
 const {$}=app(Array.from({length:15},(_,i)=>row(String(i+1),'Sede '+i)));
 assert.equal($('reportChart').children.length,15);assert.equal($('reportChart').children[0].children[0].textContent,'Sede 0');
});
test('las líneas por fecha siguen el calendario, no el ranking',()=>{
 const {$}=app([row('1','A','10/11'),row('2','A','02/11'),row('3','A','02/11'),row('4','A','01/12')],'line','fechaSede');
 assert.deepEqual($('reportChart').children.at(-1).children.map(n=>n.textContent),['1. 02/11 · A','2. 10/11 · A','3. 01/12 · A']);
});
test('selecciones vacías o sin DNI válido no producen porcentajes inválidos',()=>{
 for(const rows of [[],[row('','A')]]){const {$}=app(rows,'donut');assert(!/NaN|undefined/.test(text($('reportChart'))));assert.match(text($('reportChart')),/Sin/)}
});
