// Pure computation tests: no browser or external packages required.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const html = fs.readFileSync(require('node:path').join(__dirname, 'index.html'), 'utf8');
const script = html.split('<script>')[1].split('</script>')[0];
const pure = script.slice(0, script.indexOf("for(const id of ['start','end','grain'])"));
const fields = {start:{value:'2021'},end:{value:'2022'},grain:{value:'year'}};
const context = vm.createContext({document:{getElementById:id=>fields[id]},Intl});
vm.runInContext(pure, context);
const run = code => vm.runInContext(code, context);
run(`data={series:{
 vendas:[{mes:'2021-01',receita:100},{mes:'2021-02',receita:200},{mes:'2020-01',receita:9999}],
 custos:[{mes:'2021-01',custo_total:10,unidades:1},{mes:'2021-02',custo_total:90,unidades:99}],
 equipamentos:[{mes:'2021-01',oee_soma:0.5,oee_n:1},{mes:'2021-02',oee_soma:81,oee_n:99}],
 qualidade:[{mes:'2021-01',aprovadas:0,rejeitadas:1},{mes:'2021-02',aprovadas:999,rejeitadas:0}],
 resultados:[],operacoes:[],paradas:[]}};`);
assert.equal(run('build().total.receita'),300);
assert.equal(run('build().total.custo_unitario'),1); // Not the mean of monthly ratios.
assert.equal(run('build().total.oee'),0.815); // Not the mean of monthly means.
assert.equal(run('build().total.rejeicao'),0.001);
assert.equal(run('build().rows[1].receita'),null); // Missing is not zero.
assert.equal(run('build().rows.length'),2);
fields.grain.value='month';
assert.equal(run('build().rows.length'),24);
assert.equal(run('build().rows[2].receita'),null);
assert.equal(run('ratio(1,0)'),null);
assert.equal(run('metrics({}).custo_unitario'),null);
assert.equal(run('sum([], "x")'),null);
assert.equal(run('sum([{x:0}], "x")'),0);
const csv = run('csvText(build().rows)').split('\r\n');
assert.equal(csv.length,25); // Header plus 24 filtered months.
assert.equal(csv[0].split(';').length,19);
assert.equal(csv[3].split(';')[1],''); // Missing revenue stays blank.
assert.equal(csv[1].split(';')[7],''); // Missing availability stays blank.
assert.ok(run("chart([{period:'2021',x:2},{period:'2022',x:null},{period:'2023',x:3}], [series('x','Example')])").match(/<path/g).length===2);
console.log('PASS: filtering, weighted ratios, empty periods, zero denominator and chart gaps.');
