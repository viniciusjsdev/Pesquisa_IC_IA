"""Export the reviewed draw.io source-table grid as a portable JSON contract.

This is an offline maintenance command. It never connects to PostgreSQL.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'dados_complementares_datamind' / 'contrato_tabelas_canonicas.json'
MODEL_XML = ROOT / 'docs' / 'datamind_erd_canonical.drawio.xml'
TYPE_MAP = {
    'int': 'integer', 'decimal': 'numeric', 'text': 'text',
    'date': 'date', 'datetime': 'timestamp', 'time': 'time',
    'boolean': 'boolean', 'bool': 'boolean',
}


def warehouse_schema(cells: dict) -> tuple[dict, dict]:
    """Read the physical V1 grids and the 20 detailed new DW cards."""
    v1 = {}
    for head_id in sorted(cells):
        if not head_id.startswith('tbl_d_') or not head_id.endswith('_head'):
            continue
        prefix = head_id[:-5]
        fields = []
        index = 0
        while f'{prefix}_n{index}' in cells:
            raw_type = cells[f'{prefix}_t{index}'].get('value', '').strip()
            fields.append({
                'name': cells[f'{prefix}_n{index}'].get('value', '').strip(),
                'type': TYPE_MAP.get(raw_type, raw_type),
                'key': cells[f'{prefix}_k{index}'].get('value', '').strip(),
            })
            index += 1
        v1[prefix[6:]] = fields
    new = {}
    for cell_id, cell in cells.items():
        if not cell_id.startswith('dw_schema_'):
            continue
        if cell_id in ('dw_new_schema_title', 'dw_new_schema_note'):
            continue
        lines = cell.get('value', '').splitlines()
        name = cell_id[len('dw_schema_'):]
        if len(lines) < 3 or lines[0] != name or not lines[1].startswith('fonte: '):
            raise ValueError(f'Incomplete new DW schema card: {name}')
        sources = lines[1].removeprefix('fonte: ').split(' + ')
        fields = []
        for line in lines[2:]:
            if ' : ' in line:
                field, field_type = line.split(' : ', 1)
                if not field or field_type not in TYPE_MAP.values():
                    raise ValueError(f'Invalid DW field in {name}: {line}')
                fields.append({'name': field, 'type': field_type})
        if not fields or lines[-1] != '+ 3 colunas de origem/chave (acima)':
            raise ValueError(f'Incomplete DW fields or provenance in {name}')
        new[name] = {'sources': sources, 'fields': fields}
    note = cells.get('dw_new_schema_note')
    required = ('PK (source_file_id, original_id)',
                'source_file_id integer NOT NULL FK → dw.source_file',
                'period_index smallint NOT NULL FK → dw.dim_source_period',
                'original_id integer NOT NULL')
    if note is None or not all(item in note.get('value', '') for item in required):
        raise ValueError('New DW primary/foreign-key note differs from the loader.')
    if len(v1) != 15 or len(new) != 20 or sum(len(t['fields']) for t in new.values()) != 180:
        raise ValueError('Expected 15 V1 tables and 20 new DW tables with 180 source fields.')
    return v1, new


def export(diagram: Path) -> dict:
    cells = {cell.get('id'): cell for cell in ET.parse(diagram).iter('mxCell')}
    tables = {}
    for head_id in sorted(cells):
        if not head_id.endswith('_head') or not head_id.startswith(('tbl_i_', 'tbl_f_')):
            continue
        prefix = head_id[:-5]
        domain = 'industrial' if prefix.startswith('tbl_i_') else 'financeiro'
        table = prefix[6:]
        csv_name = 'processo_industrial' if table == 'processos_industriais' else table
        fields = []
        index = 0
        while f'{prefix}_n{index}' in cells:
            raw_type = cells[f'{prefix}_t{index}'].get('value', '').strip()
            base_type = raw_type.rstrip('?*')
            if base_type not in TYPE_MAP:
                raise ValueError(f'Unsupported type {raw_type!r} in {table}')
            fields.append({
                'name': cells[f'{prefix}_n{index}'].get('value', '').strip(),
                'type': TYPE_MAP[base_type],
                'key': cells[f'{prefix}_k{index}'].get('value', '').strip(),
                'source_date_only': raw_type == 'date*',
            })
            index += 1
        if not fields or not any('PK' in field['key'].split(',') for field in fields):
            raise ValueError(f'No primary key in {table}')
        if csv_name in tables:
            raise ValueError(f'Duplicate table {csv_name}')
        tables[csv_name] = {'database': f'db_{domain}', 'table': table, 'fields': fields}
    if len(tables) != 56:
        raise ValueError(f'Expected 56 source table types, got {len(tables)}')
    warehouse = {'v1': [], 'new': []}
    for cell_id, cell in cells.items():
        if not cell_id.startswith('d_') or not cell.get('value'):
            continue
        value = cell.get('value', '')
        name = cell_id[2:]
        if value.startswith(name + '\nV1'):
            warehouse['v1'].append(name)
        elif value.startswith(name + '\nPROPOSTA'):
            warehouse['new'].append(name)
    warehouse = {key: sorted(names) for key, names in warehouse.items()}
    if len(warehouse['v1']) != 15 or len(warehouse['new']) != 20:
        raise ValueError(f'Expected 15 V1 and 20 new DW tables, got {warehouse}')
    v1_schema, new_schema = warehouse_schema(cells)
    if set(v1_schema) != set(warehouse['v1']) or set(new_schema) != set(warehouse['new']):
        raise ValueError('DW schema grids/cards differ from DW table labels.')
    return {'version': 1, 'source': 'DER revisado do DataMind',
            'tables': tables, 'warehouse_tables': warehouse,
            'warehouse_v1_schema': v1_schema, 'warehouse_new_schema': new_schema}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('diagram', type=Path, help='Local uncompressed draw.io XML')
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    result = export(args.diagram)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{len(result["tables"])} source table types written to {args.output}')


if __name__ == '__main__':
    main()
