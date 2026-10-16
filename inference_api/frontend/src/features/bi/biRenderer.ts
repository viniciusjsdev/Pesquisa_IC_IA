// Rendering and numeric formulas ported from the frozen SPEC-008 BI reference.
// The snapshot is fetched after authentication; no BI observations are bundled here.
/* eslint-disable @typescript-eslint/no-explicit-any */
const palette={teal:'#087f75',blue:'#3673ba',amber:'#b47825',red:'#bc584a'};
type Source={key:string;label:string;linhas:number;inicio?:string;fim?:string;sem_data?:number;definition:string;domain:string;table:string;date_field:string;[key:string]:any};
type Snapshot={series:Record<string,any[]>;sources:Source[];inventory:Record<string,Record<string,number>>};
type Column={key:string;label:string;format?:(value:any)=>string};
type ChartSeries={key:string;label:string;color:string};
let data:Snapshot,tab:'overview'|'financial'|'industrial'|'sources',start:number,end:number,grain:'year'|'month';
const esc=(s:unknown)=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'} as Record<string,string>)[c]);
const num=(n:any,d=0)=>n==null||!Number.isFinite(n)?'—':new Intl.NumberFormat('pt-BR',{maximumFractionDigits:d,minimumFractionDigits:d}).format(n);
const compact=(n:any)=>n==null?'—':new Intl.NumberFormat('pt-BR',{notation:'compact',maximumFractionDigits:1}).format(n);
const ratio=(a:any,b:any)=>a==null||b==null||b===0?null:a/b;
const percent=(n:any)=>n==null?'—':num(n,1)+'%';
function sum(rows:any[],key:string){const v=rows.map(r=>r[key]).filter(x=>x!=null);return v.length?v.reduce((a,b)=>a+b,0):null}
function filtered(key:string):any[]{return data.series[key].filter((r:any)=>+r.mes.slice(0,4)>=start&&+r.mes.slice(0,4)<=end)}
function aggregate(rows:any[],grain:string){const m=new Map<string,any>();for(const r of rows){const k=grain==='year'?r.mes.slice(0,4):r.mes;if(!m.has(k))m.set(k,{});const o=m.get(k);for(const [f,v]of Object.entries(r)){if(f!=='mes'&&v!=null)o[f]=(o[f]??0)+v}}return m}
function metrics(s:any){const e=s.equipamentos??{},q=s.qualidade??{},c=s.custos??{},f=s.resultados??{};return{
 receita:s.vendas?.receita??null,volume:s.operacoes?.volume??null,energia:s.operacoes?.energia??null,
 oee:ratio(e.oee_soma,e.oee_n),disponibilidade:ratio(e.disponibilidade_soma,e.disponibilidade_n),performance:ratio(e.performance_soma,e.performance_n),qualidade:ratio(e.qualidade_soma,e.qualidade_n),
 rejeicao:ratio(q.rejeitadas,q.aprovadas==null||q.rejeitadas==null?null:q.aprovadas+q.rejeitadas),
 horas:s.paradas?.horas??null,custo:c.custo_total??null,custo_unitario:ratio(c.custo_total,c.unidades),
 receita_reportada:f.receita_reportada??null,lucro:f.lucro_liquido??null,margem:ratio(f.lucro_liquido,f.receita_reportada),
 materia_prima:c.materia_prima??null,mao_obra:c.mao_obra??null,indiretos:c.indiretos??null,aprovadas:q.aprovadas??null,rejeitadas:q.rejeitadas??null}}
function build(){const grouped:Record<string,Map<string,any>>={},totals:Record<string,any>={};for(const k of Object.keys(data.series)){const rows=filtered(k);grouped[k]=aggregate(rows,grain);totals[k]={};const fields=new Set(rows.flatMap(r=>Object.keys(r)));for(const f of fields)if(f!=='mes')totals[k][f]=sum(rows,f)}
 const periods=[];for(let y=start;y<=end;y++){if(grain==='year')periods.push(String(y));else for(let m=1;m<=12;m++)periods.push(`${y}-${String(m).padStart(2,'0')}`)}
 const rows=periods.map(period=>({period,...metrics(Object.fromEntries(Object.entries(grouped).map(([k,m])=>[k,m.get(period)])))}));return{rows,total:metrics(totals)}}
const scope=()=>`${String(start)}–${String(end)}`;
const pct=(n:any)=>n==null?null:n*100;
function card(label:string,value:string,unit:string,note:string,symbol='↗'){return`<article class="card"><div class="kpi-top"><div class="kpi-label">${label}</div><span class="kpi-symbol">${symbol}</span></div><div class="kpi-value">${value} <small>${unit}</small></div><div class="kpi-note">${note}</div></article>`}
function head(title:string,note:string){return`<div class="sectionhead"><h2>${title}</h2><span>${note}</span></div>`}
function panel(title:string,note:string,body:string,full=false){return`<section class="panel ${full?'full':''}"><h3>${title}</h3><p>${note}</p>${body}</section>`}
function chart(rows:any[],series:ChartSeries[],unit='',fixed:number[]|null=null){const w=590,h=235,left=57,right=14,top=15,bottom=35,pw=w-left-right,ph=h-top-bottom;
 const vals=rows.flatMap(r=>series.map(s=>r[s.key])).filter(v=>v!=null&&Number.isFinite(v));if(!vals.length)return'<div class="empty">Sem observações neste período.</div>';
 const low=fixed?fixed[0]:Math.min(0,...vals);let high=fixed?fixed[1]:Math.max(0,...vals)*1.12;if(high===low)high=low+1;
 const x=(i:number)=>left+(rows.length===1?pw/2:i*pw/(rows.length-1)),y=(v:number)=>top+ph-(v-low)/(high-low)*ph;
 let svg=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Gráfico de ${esc(series.map(s=>s.label).join(', '))}. Valores detalhados na tabela e no CSV.">`;
 for(let t=0;t<5;t++){const v=low+(high-low)*t/4,yy=y(v);svg+=`<line x1="${left}" y1="${yy}" x2="${w-right}" y2="${yy}" stroke="#e9efec"/><text x="${left-9}" y="${yy+3}" text-anchor="end">${esc(compact(v))}</text>`}
 const step=Math.max(1,Math.ceil(rows.length/7));rows.forEach((r,i)=>{if(i%step===0||i===rows.length-1){const label=r.period.length===7?r.period.slice(5)+'/'+r.period.slice(2,4):r.period;svg+=`<text x="${x(i)}" y="${h-10}" text-anchor="middle">${esc(label)}</text>`}});
 for(const s of series){let path='';const segments:string[]=[];rows.forEach((r,i)=>{const v=r[s.key];if(v==null){if(path)segments.push(path);path=''}else path+=(path?' L':'M')+x(i)+','+y(v)});if(path)segments.push(path);
  for(const p of segments)svg+=`<path d="${p}" fill="none" stroke="${s.color}" stroke-width="2.4" stroke-linejoin="round"/>`;
  rows.forEach((r,i)=>{if(r[s.key]!=null)svg+=`<circle cx="${x(i)}" cy="${y(r[s.key])}" r="${rows.length>30?2:3.5}" fill="${s.color}"><title>${esc(r.period+' · '+s.label+': '+num(r[s.key],2)+' '+unit)}</title></circle>`})}
 svg+='</svg>';return`<div class="chart">${svg}</div><div class="legend">${series.map(s=>`<span><i style="background:${s.color}"></i>${s.label}</span>`).join('')}<span>${unit} · lacunas = sem dados</span></div>`}
function series(key:string,label:string,color=palette.teal):ChartSeries{return{key,label,color}}
function table(rows:any[],columns:Column[]){return`<div class="tablewrap"><table><thead><tr>${columns.map(c=>`<th scope="col">${esc(c.label)}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${columns.map(c=>`<td>${esc(c.format?c.format(r[c.key]):r[c.key]??'—')}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`}
function integratedTable(rows:any[]){return table(rows,[{key:'period',label:'Período'},{key:'receita',label:'Vendas · u.m.',format:v=>num(v,2)},{key:'volume',label:'Volume nas operações',format:num},{key:'oee',label:'OEE médio',format:v=>percent(pct(v))},{key:'custo_unitario',label:'Custo unit. · u.m.',format:v=>num(v,3)},{key:'rejeicao',label:'Rejeição',format:v=>percent(pct(v))},{key:'horas',label:'Paradas · h',format:v=>num(v,1)}])}
function coverageNote(){const keys=tab==='financial'?['vendas','custos','resultados']:tab==='industrial'?['operacoes','equipamentos','qualidade','paradas']:['vendas','custos','resultados','operacoes'];
 const missing=keys.filter(k=>filtered(k).length===0).map(k=>data.sources.find(s=>s.key===k)?.label || k);
 const notes=['Fontes com coberturas diferentes. Custos e resultados financeiros têm registros somente até 2023. Valores monetários em unidades monetárias (u.m.); moeda não informada na base.'];
 if(end>=2026)notes.push('2026 contém apenas registros industriais de fronteira temporal; não representa um ano completo.');
 if(missing.length)notes.push('Sem observações no filtro: '+missing.join(', ')+'.');
 return {warning:missing.length>0,text:notes.join(' ')};
}
function render(){const{rows,total:t}=build();const percentRows=rows.map(r=>({...r,oee:pct(r.oee),disponibilidade:pct(r.disponibilidade),performance:pct(r.performance),qualidade:pct(r.qualidade),rejeicao:pct(r.rejeicao)}));
 const headings={overview:['OBSERVATÓRIO DA OPERAÇÃO','Da fábrica ao resultado.','Explore a evolução financeira e industrial da empresa, com indicadores rastreáveis às fontes da pesquisa.'],financial:['DESEMPENHO FINANCEIRO','Receitas, custos e resultados.','Consulte cada fonte financeira separadamente e acompanhe os valores disponíveis ao longo do tempo.'],industrial:['DESEMPENHO INDUSTRIAL','A operação em perspectiva.','Observe volume registrado, eficiência dos equipamentos, qualidade e paradas no período selecionado.'],sources:['TRANSPARÊNCIA DA PESQUISA','Os dados por trás dos números.','Consulte a cobertura, as definições dos indicadores e os limites de interpretação desta base sintética.']};
 const heading=headings[tab];
 let html:string;
 if(tab==='overview'){
  html=head('Panorama do período',scope()+' · filtros aplicados')+'<div class="cards">'+
   card('Receita das vendas',compact(t.receita),'u.m.','Soma das vendas disponíveis · não conciliada com resultados')+
   card('Volume nas operações',compact(t.volume),'un. registradas','Soma por operação · não representa unidades finais únicas','▤')+
   card('OEE médio informado',percent(pct(t.oee)),'','Média das observações de equipamentos','◉')+
   card('Rejeição nas inspeções',percent(pct(t.rejeicao)),'','Rejeitadas ÷ total de unidades inspecionadas','◇')+'</div>'+
   '<div class="grid">'+panel('Evolução das vendas','Receita calculada a partir das transações de venda.',chart(rows,[series('receita','Receita das vendas')],'u.m.'))+
   panel('Volume registrado nas operações','Quantidade produzida somada em todos os registros de operação.',chart(rows,[series('volume','Volume nas operações',palette.blue)],'un. registradas'))+
   panel('Eficiência dos equipamentos','Média simples do OEE informado nas observações.',chart(percentRows,[series('oee','OEE médio')],'%',[0,100]))+
   panel('Custo por unidade','Razão entre custo total e unidades da tabela de custos.',chart(rows,[series('custo_unitario','Custo unitário',palette.amber)],'u.m./un.'))+
   panel('Leitura integrada por período','Alinhamento temporal de fontes distintas. A comparação não demonstra causalidade nem conciliação entre bases.',integratedTable(rows),true)+'</div>';
 }else if(tab==='financial'){
  html=head('Indicadores financeiros',scope()+' · u.m. = unidades monetárias')+'<div class="cards">'+
   card('Receita das vendas',compact(t.receita),'u.m.','Fonte: vendas · quantidade × preço')+
   card('Receita reportada',compact(t.receita_reportada),'u.m.','Fonte: resultados financeiros · soma dos registros')+
   card('Lucro líquido reportado',compact(t.lucro),'u.m.','Fonte: resultados financeiros · soma dos registros')+
   card('Custo unitário agregado',num(t.custo_unitario,3),'u.m./un.','Custo total ÷ unidades da tabela de custos')+'</div>';
  const components=[['Matéria-prima',t.materia_prima,palette.teal],['Mão de obra',t.mao_obra,palette.blue],['Custos indiretos',t.indiretos,palette.amber]],max=Math.max(1,...components.map(c=>c[1]??0));
  const bars=components.every(c=>c[1]==null)?'<div class="empty">Sem custos disponíveis neste período.</div>':'<div style="padding:20px 0">'+components.map(([label,v,color])=>`<div class="barrow"><span>${label}</span><div class="bartrack"><div class="barfill" style="width:${Math.max(0,(v??0)/max*100)}%;background:${color}"></div></div><span class="barvalue">${num(v,2)}</span></div>`).join('')+'</div>';
  html+='<div class="grid">'+panel('Resultados reportados','Receita e lucro da mesma fonte. Não são derivados da tabela de vendas.',chart(rows,[series('receita_reportada','Receita reportada'),series('lucro','Lucro líquido',palette.blue)],'u.m.'))+
   panel('Componentes do custo de produção','Soma de cada componente disponível no período · u.m.',bars)+
   panel('Receita das vendas','Transações disponíveis na base; meses sem vendas registradas aparecem como lacunas.',chart(rows,[series('receita','Receita das vendas')],'u.m.'))+
   panel('Custos totais registrados','Soma do campo custo_total nos registros disponíveis.',chart(rows,[series('custo','Custo total',palette.amber)],'u.m.'))+
   panel('Detalhamento financeiro','Valores das fontes financeiras no filtro selecionado.',table(rows,[{key:'period',label:'Período'},{key:'receita',label:'Vendas · u.m.',format:v=>num(v,2)},{key:'receita_reportada',label:'Receita reportada · u.m.',format:v=>num(v,2)},{key:'lucro',label:'Lucro reportado · u.m.',format:v=>num(v,2)},{key:'custo',label:'Custo total · u.m.',format:v=>num(v,2)},{key:'custo_unitario',label:'Custo/un. · u.m.',format:v=>num(v,3)}]),true)+'</div>';
 }else if(tab==='industrial'){
  html=head('Indicadores da operação',scope()+' · observações disponíveis')+'<div class="cards">'+
   card('Volume nas operações',compact(t.volume),'un. registradas','Pode contar unidades em múltiplas operações','▤')+
   card('Energia registrada',compact(t.energia),'kWh','Soma do consumo nos registros de operação','ϟ')+
   card('Tempo de parada',num(t.horas,1),'h','Soma dos eventos · sem deduplicar sobreposições','◷')+
   card('OEE médio informado',percent(pct(t.oee)),'','Média das observações · não recalculado','◉')+'</div>'+
   '<div class="grid">'+panel('Indicadores dos equipamentos','Médias das observações em cada período. Escala original convertida para %.',chart(percentRows,[series('oee','OEE'),series('disponibilidade','Disponibilidade',palette.blue),series('performance','Performance',palette.amber),series('qualidade','Qualidade',palette.red)],'%',[0,100]))+
   panel('Rejeição nas inspeções','Unidades rejeitadas ÷ total inspecionado. Fonte distinta da qualidade dos equipamentos.',chart(percentRows,[series('rejeicao','Taxa de rejeição',palette.red)],'%'))+
   panel('Horas de parada','Eventos agrupados pela data de início.',chart(rows,[series('horas','Horas de parada',palette.amber)],'h'))+
   panel('Consumo de energia','Soma do consumo registrado nas operações.',chart(rows,[series('energia','Energia',palette.blue)],'kWh'))+
   panel('Detalhamento industrial','Médias ponderadas pela quantidade de observações; rejeição calculada sobre os totais inspecionados.',table(rows,[{key:'period',label:'Período'},{key:'volume',label:'Volume registrado',format:num},{key:'energia',label:'Energia · kWh',format:v=>num(v,1)},{key:'oee',label:'OEE médio',format:v=>percent(pct(v))},{key:'horas',label:'Paradas · h',format:v=>num(v,1)},{key:'aprovadas',label:'Aprovadas',format:num},{key:'rejeitadas',label:'Rejeitadas',format:num}]),true)+'</div>';
 }else{
  const ind=Object.values(data.inventory.industrial).reduce((a,b)=>a+b,0),fin=Object.values(data.inventory.financeiro).reduce((a,b)=>a+b,0);
  html=head('Inventário completo da base','Totais gerais · não seguem o filtro de período')+'<div class="cards">'+card('Registros industriais',num(ind),'','14 tabelas com origem em CSV','▤')+card('Registros financeiros',num(fin),'','11 tabelas com origem em CSV','▤')+card('Tabelas usadas no painel','7','','Agregações incorporadas ao arquivo na exportação','≡')+card('Camada analítica DW','Local v1','','Este retrato offline não consulta o DW','◇')+'</div>'+
   '<div class="grid">'+panel('Cobertura das fontes do painel','Início, fim e contagem global por fonte. Meses com dados respeitam o filtro atual.',table(data.sources.map(s=>({...s,inicio:s.inicio?.slice(0,10),fim:s.fim?.slice(0,10),meses:filtered(s.key).length})),[{key:'label',label:'Fonte'},{key:'linhas',label:'Linhas totais',format:num},{key:'inicio',label:'Primeiro registro'},{key:'fim',label:'Último registro'},{key:'meses',label:'Meses no filtro',format:num},{key:'sem_data',label:'Sem data',format:num}]),true)+
   panel('Como os indicadores são calculados','Definições usadas no painel e na exportação.',`<div class="source-list">${data.sources.map(s=>`<div class="source-item"><b>${esc(s.label)}</b><p>${esc(s.definition)}</p><p><code>${esc(s.domain+'.'+s.table)}</code> · data: <code>${esc(s.date_field)}</code></p></div>`).join('')}</div>`)+
   panel('Limites de interpretação','A importação preserva as fontes; a validação científica é uma etapa posterior.',`<div class="source-list"><div class="source-item"><b>Dados sintéticos</b><p>Este painel descreve a empresa simulada. Não representa resultados observados de uma empresa real.</p></div><div class="source-item"><b>Ausência não é zero</b><p>Períodos sem observações ficam vazios nos gráficos e no CSV. Custos e resultados encerram em 2023; 2026 tem apenas observações industriais de fronteira.</p></div><div class="source-item"><b>Fontes ainda não conciliadas</b><p>Receita das vendas e receita reportada são séries independentes. As unidades da tabela de custos não são substituídas pelo volume das operações.</p></div><div class="source-item"><b>Identidades por período</b><p>Os cadastros preservam versões por período, com IDs remapeados. Este painel não consolida automaticamente a identidade histórica de produtos e máquinas.</p></div><div class="source-item"><b>Comparação temporal</b><p>Alinhar indicadores por ano ou mês não comprova que automação causou uma variação financeira. Não há avaliação de LLMs neste painel.</p></div><div class="source-item"><b>Arquivo independente</b><p>Este retrato sintético foi exportado em 06/09/2026. Filtros, gráficos e CSV usam o snapshot protegido pela sessão; não há atualização automática.</p></div></div>`)+
   panel('Tabelas carregadas','Contagens das tabelas de origem na exportação. A camada bruta não é somada novamente.',table(Object.entries(data.inventory).flatMap(([domain,tables])=>Object.entries(tables).map(([name,linhas])=>({nome:domain+'.'+name,linhas}))),[{key:'nome',label:'Banco / tabela'},{key:'linhas',label:'Registros',format:num}]),true)+'</div>';
 }
 return {heading,html,rows,total:t,context:coverageNote()};
}
export function csvText(rows:any[]){const columns=['period','receita','receita_reportada','lucro','volume','energia','oee','disponibilidade','performance','qualidade','rejeicao','horas','custo','custo_unitario','materia_prima','mao_obra','indiretos','aprovadas','rejeitadas'];
 const labels=['periodo','receita_vendas_um','receita_reportada_um','lucro_reportado_um','volume_registrado_operacoes','energia_kwh','oee_fracao','disponibilidade_fracao','performance_fracao','qualidade_equipamentos_fracao','rejeicao_fracao','paradas_horas','custo_total_um','custo_unitario_um','materia_prima_um','mao_obra_um','custos_indiretos_um','unidades_aprovadas','unidades_rejeitadas'];
 const lines=[labels.join(';'),...rows.map(r=>columns.map(k=>r[k]==null?'':String(r[k]).replace('.',',')).join(';'))];
 return '\ufeff'+lines.join('\r\n');
}
export function renderBI(snapshot:unknown,selectedTab:'overview'|'financial'|'industrial'|'sources',startYear:number,endYear:number,selectedGrain:'year'|'month'){data=snapshot as Snapshot;tab=selectedTab;start=startYear;end=endYear;grain=selectedGrain;return render()}
