import { describe, expect, it } from 'vitest';
import { csvText, renderBI } from './biRenderer';

const snapshot = {
  series: {
    vendas: [{ mes: '2020-01', receita: 120 }],
    operacoes: [{ mes: '2020-01', volume: 42, energia: 17 }],
    equipamentos: [{ mes: '2020-01', oee_soma: 0.8, oee_n: 1 }],
    qualidade: [{ mes: '2020-01', aprovadas: 9, rejeitadas: 1 }],
    paradas: [{ mes: '2020-01', horas: 2 }],
    custos: [{ mes: '2020-01', custo_total: 50, unidades: 10 }],
    resultados: [{ mes: '2020-01', receita_reportada: 90, lucro_liquido: 20 }],
  },
  sources: [],
  inventory: { industrial: {}, financeiro: {} },
};

describe('renderer portado da referência BI', () => {
  it('preserva agregações, colunas e formato CSV', () => {
    const view = renderBI(snapshot, 'overview', 2020, 2020, 'year');
    expect(view.rows[0]).toMatchObject({ period: '2020', receita: 120, volume: 42, oee: 0.8, rejeicao: 0.1 });
    expect(view.heading[1]).toContain('Da fábrica');
    const csv = csvText(view.rows);
    expect(csv.startsWith('\ufeffperiodo;receita_vendas_um;')).toBe(true);
    expect(csv).toContain('\r\n2020;120;90;20;42;17;0,8;');
  });

  it('corrige apenas o estado factual do DW no método', () => {
    const view = renderBI(snapshot, 'sources', 2020, 2020, 'year');
    expect(view.html).toContain('Local v1');
    expect(view.html).toContain('Este retrato offline não consulta o DW');
    expect(view.html).not.toContain('DW</div><div class="kpi-value">Pendente');
  });
});
