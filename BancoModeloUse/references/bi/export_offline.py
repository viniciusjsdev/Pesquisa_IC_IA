"""Export a self-contained HTML snapshot of the current local BI data."""
import argparse
import json
from pathlib import Path

from server import collect, encode, ENGINES


def build_html(payload):
    html = Path(__file__).with_name('index.html').read_text(encoding='utf-8')
    live = "const res=await fetch('/api/data'+(force?'?refresh=1':''));const result=await res.json();if(!res.ok)throw new Error(result.error||'Falha na consulta.');"
    if html.count(live) != 1:
        raise RuntimeError('BI template changed; review the offline data loader.')
    html = html.replace(live, "const result=JSON.parse(document.getElementById('embedded-data').textContent);")
    html = html.replace("$('refresh').disabled=false;$('refresh').textContent='↻ Atualizar dados'", "$('refresh').hidden=true")
    html = html.replace('id="refresh">', 'id="refresh" hidden>')
    html = html.replace('Base sintética · consulta local', 'Base sintética · versão offline')
    html = html.replace('Consultando as bases locais…', 'Carregando os dados incorporados…')
    html = html.replace('Aguardando consulta ao PostgreSQL', 'Dados incorporados neste arquivo')
    html = html.replace("'Última consulta: '", "'Retrato dos dados: '")
    html = html.replace("+' · PostgreSQL local'", "+' · versão offline, sem atualização automática'")
    html = html.replace('Agregações consultadas diretamente no PostgreSQL', 'Agregações incorporadas ao arquivo na exportação')
    html = html.replace('Contagens atuais das tabelas de origem.', 'Contagens das tabelas de origem na exportação.')
    html = html.replace('<b>Leitura local</b><p>Consultas em transações somente leitura. A atualização recarrega as agregações do PostgreSQL; não altera os dados. Os dois bancos são lidos em transações separadas.</p>',
                        '<b>Arquivo independente</b><p>Os dados agregados estão incorporados neste HTML. Filtros, gráficos e CSV funcionam sem servidor ou internet. Para atualizar os dados, é necessário gerar uma nova versão do arquivo.</p>')
    html = html.replace('Inicie o PostgreSQL da pesquisa e clique em Atualizar dados.', 'Não foi possível ler os dados incorporados. Solicite uma nova cópia deste arquivo.')
    # Escape HTML-significant characters even if future source labels contain markup.
    embedded = json.dumps(payload, default=encode, ensure_ascii=False, allow_nan=False, separators=(',', ':'))
    embedded = embedded.replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    html = html.replace('<script>', f'<script id="embedded-data" type="application/json">{embedded}</script>\n<script>', 1)
    html = html.replace('<meta charset="utf-8">', '<meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; script-src \'unsafe-inline\'; style-src \'unsafe-inline\'; img-src data:; connect-src \'none\'; base-uri \'none\'; form-action \'none\'">', 1)
    return html


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'exports/BI_Pesquisa_Offline.html')
    args = parser.parse_args()
    try:
        payload = collect()
        html = build_html(payload)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(html, encoding='utf-8')
        print(f'HTML independente: {args.output.resolve()}')
        print(f'Tamanho: {args.output.stat().st_size:,} bytes; fontes: {len(payload["sources"])}')
        print(f'Dados consultados em: {payload["snapshot_at"]}')
    finally:
        for db_engine in ENGINES.values():
            db_engine.dispose()


if __name__ == '__main__':
    main()
