# scripts/load_data.py
"""
Script para carregar dados dos CSVs e popular os bancos de dados
"""
import os
import sys
import csv
import logging
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importa conexões
from infrastructure.database.connections.industrial_connection import industrial_connection
from infrastructure.database.connections.financeiro_connection import financeiro_connection

# Importa modelos industriais
from core.models.industrial.cadastros import (
    Produto, Material, Maquina, Fornecedor
)
from core.models.industrial.producao import (
    OrdemProducao, RoteiroProducao, OperacaoRoteiro, RegistroOperacao,
    ParadaMaquina, ConsumoMaterial, LoteMaterial, LoteProducao
)
from core.models.industrial.equipamentos import (
    Equipamento, ProcessoIndustrial
)
from core.models.industrial.qualidade import (
    ControleQualidade, Defeito, RegistroDefeito
)

# Importa modelos financeiros
from core.models.financeiro.custos import (
    CustoPadrao, CustoIndiretoRateio, MaterialCustoHistorico,
    CustoMaoObraHistorico, CustoOperacionalVariavel, CustoProducao,
    ResultadoFinanceiro, AnaliseFinanceira
)
from core.models.financeiro.contabil import (
    ContaContabil, LancamentoFinanceiro, CategoriaContabilPadrao,
    SubcategoriaContabilPadrao, ContaContabilDetalhe
)
from core.models.financeiro.vendas import (
    Venda, Orcamento
)
from core.models.financeiro.kpis import (
    KPIGerencial
)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Diretório base dos dados
BASE_DATA_DIR = Path(__file__).parent.parent / "dados_simulados"

# Dicionários globais para mapeamento de IDs antigos → novos IDs
ID_MAPPING = {
    'produto': {},      # {id_antigo: id_novo}
    'material': {},
    'maquina': {},
    'fornecedor': {},
    'custo_padrao': {},
    'conta_contabil': {}
}

# Mapeamento de períodos para diretórios
INDUSTRIAL_PERIODS_MAPPING = {
    "2015-2017": "dados_industriais_automotivo_eletronica_2015_2017",
    "2017-2020": "dados_industriais_automotivo_eletronica_2017_2020",
    "2021-2025": "dados_industriais_automotivo_eletronics_2021_2025"
}

FINANCEIRO_PERIODS_MAPPING = {
    "2015-2016": "dados_financeiros_2015_2016",
    "2017-2020": "dados_financeiros_2017_2020",
    "2021-2025": "dados_financeiros_2021_2025"
}

def parse_date(date_str: Optional[str]) -> Optional[date]:
    """Converte string de data para objeto date"""
    if not date_str or date_str.strip() == '':
        return None
    try:
        # Tenta vários formatos
        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d']:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        logger.warning(f"Formato de data não reconhecido: {date_str}")
        return None
    except Exception as e:
        logger.warning(f"Erro ao converter data '{date_str}': {e}")
        return None

def parse_datetime(datetime_str: Optional[str]) -> Optional[datetime]:
    """Converte string de datetime para objeto datetime"""
    if not datetime_str or datetime_str.strip() == '':
        return None
    try:
        # Tenta vários formatos
        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y %H:%M:%S', '%d/%m/%Y']:
            try:
                dt = datetime.strptime(datetime_str.strip(), fmt)
                return dt
            except ValueError:
                continue
        logger.warning(f"Formato de datetime não reconhecido: {datetime_str}")
        return None
    except Exception as e:
        logger.warning(f"Erro ao converter datetime '{datetime_str}': {e}")
        return None

def parse_decimal(value: Optional[str]) -> Optional[Decimal]:
    """Converte string para Decimal"""
    if not value or value.strip() == '':
        return None
    try:
        # Remove espaços e substitui vírgula por ponto
        cleaned = value.strip().replace(',', '.')
        return Decimal(cleaned)
    except Exception as e:
        logger.warning(f"Erro ao converter para Decimal '{value}': {e}")
        return None

def parse_int(value: Optional[str]) -> Optional[int]:
    """Converte string para int"""
    if not value or value.strip() == '':
        return None
    try:
        # Remove espaços e tenta converter
        cleaned = value.strip()
        # Remove ponto decimal se houver
        if '.' in cleaned:
            cleaned = cleaned.split('.')[0]
        return int(cleaned)
    except Exception as e:
        logger.warning(f"Erro ao converter para int '{value}': {e}")
        return None

def parse_float(value: Optional[str]) -> Optional[float]:
    """Converte string para float"""
    if not value or value.strip() == '':
        return None
    try:
        cleaned = value.strip().replace(',', '.')
        return float(cleaned)
    except Exception as e:
        logger.warning(f"Erro ao converter para float '{value}': {e}")
        return None

def read_csv_file(file_path: Path) -> List[Dict[str, str]]:
    """Lê arquivo CSV e retorna lista de dicionários"""
    if not file_path.exists():
        logger.warning(f"Arquivo não encontrado: {file_path}")
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as e:
        logger.error(f"Erro ao ler arquivo {file_path}: {e}")
        return []

def load_csv_to_model_with_id_mapping(
    session: Session,
    model_class: Any,
    csv_data: List[Dict[str, str]],
    field_mapping: Dict[str, str],
    transform_func: Optional[callable] = None,
    id_field_name: Optional[str] = None,
    mapping_key: Optional[str] = None
) -> Tuple[int, Dict[int, int]]:
    """
    Carrega dados do CSV para o modelo com mapeamento de IDs
    Usado para tabelas de cadastro com autoincrement
    OTIMIZADO: Insere em lotes usando session.add() para obter IDs
    
    Args:
        session: Sessão do banco de dados
        model_class: Classe do modelo SQLAlchemy
        csv_data: Lista de dicionários com dados do CSV
        field_mapping: Mapeamento de colunas CSV para campos do modelo
        transform_func: Função opcional para transformar os dados antes de inserir
        id_field_name: Nome do campo ID no modelo (ex: 'produto_id')
        mapping_key: Chave para armazenar mapeamento (ex: 'produto')
    
    Returns:
        Tupla (número de registros inseridos, mapeamento {id_antigo: id_novo})
    """
    if not csv_data:
        return 0, {}
    
    inserted_count = 0
    id_mapping = {}
    errors = []
    batch_size = 100  # Processa em lotes de 100 registros
    
    try:
        # Remove o ID do field_mapping se existir
        field_mapping_no_id = {k: v for k, v in field_mapping.items() if v != id_field_name}
        
        # Prepara todos os registros primeiro
        records_to_insert = []
        old_ids = []
        
        for row in csv_data:
            try:
                # Extrai ID antigo se existir
                old_id = None
                if id_field_name and mapping_key:
                    csv_id_field = id_field_name
                    if csv_id_field not in row:
                        # Tenta encontrar por nome similar
                        for csv_field in row.keys():
                            if csv_field.lower() == id_field_name.lower():
                                csv_id_field = csv_field
                                break
                    if csv_id_field in row:
                        old_id_str = row.get(csv_id_field)
                        if old_id_str:
                            old_id = parse_int(old_id_str)
                
                # Prepara registro sem o ID
                record = {}
                for csv_field, model_field in field_mapping_no_id.items():
                    value = row.get(csv_field)
                    if value is not None:
                        record[model_field] = value
                
                # Aplica transformação se fornecida
                if transform_func:
                    record = transform_func(record)
                    # Remove ID se foi adicionado pela transformação
                    if id_field_name and id_field_name in record:
                        del record[id_field_name]
                
                # Remove None values
                record = {k: v for k, v in record.items() if v is not None}
                
                if record:
                    records_to_insert.append(record)
                    old_ids.append(old_id)
                    
            except Exception as e:
                errors.append(f"Erro ao processar linha: {e}")
                continue
        
        # Insere em lotes para obter IDs
        for i in range(0, len(records_to_insert), batch_size):
            batch_records = records_to_insert[i:i+batch_size]
            batch_old_ids = old_ids[i:i+batch_size]
            
            try:
                # Cria instâncias do modelo
                instances = []
                for record in batch_records:
                    instance = model_class(**record)
                    instances.append(instance)
                    session.add(instance)
                
                # Flush para obter IDs gerados
                session.flush()
                
                # Mapeia IDs antigos para novos
                for instance, old_id in zip(instances, batch_old_ids):
                    new_id = getattr(instance, id_field_name) if id_field_name else None
                    if old_id and new_id:
                        id_mapping[old_id] = new_id
                        if mapping_key:
                            ID_MAPPING[mapping_key][old_id] = new_id
                    inserted_count += 1
                    
            except IntegrityError:
                # Se houver duplicatas, insere um por um
                session.rollback()
                for record, old_id in zip(batch_records, batch_old_ids):
                    try:
                        instance = model_class(**record)
                        session.add(instance)
                        session.flush()
                        
                        new_id = getattr(instance, id_field_name) if id_field_name else None
                        if old_id and new_id:
                            id_mapping[old_id] = new_id
                            if mapping_key:
                                ID_MAPPING[mapping_key][old_id] = new_id
                        inserted_count += 1
                    except IntegrityError:
                        # Duplicata, ignora
                        session.rollback()
                        continue
                    except Exception as e:
                        session.rollback()
                        errors.append(f"Erro ao inserir registro: {e}")
                        continue
        
        if errors:
            logger.warning(f"Erros ao processar {len(errors)} linhas: {errors[:5]}")
        
        if inserted_count > 0:
            logger.info(f"Inseridos {inserted_count} registros em {model_class.__tablename__}")
    
    except Exception as e:
        logger.error(f"Erro ao carregar dados para {model_class.__tablename__}: {e}")
        raise
    
    return inserted_count, id_mapping

def load_csv_to_model(
    session: Session,
    model_class: Any,
    csv_data: List[Dict[str, str]],
    field_mapping: Dict[str, str],
    transform_func: Optional[callable] = None
) -> int:
    """
    Carrega dados do CSV para o modelo
    Trata duplicatas ignorando registros que já existem
    
    Args:
        session: Sessão do banco de dados
        model_class: Classe do modelo SQLAlchemy
        csv_data: Lista de dicionários com dados do CSV
        field_mapping: Mapeamento de colunas CSV para campos do modelo
        transform_func: Função opcional para transformar os dados antes de inserir
    
    Returns:
        Número de registros inseridos
    """
    if not csv_data:
        return 0
    
    inserted_count = 0
    skipped_count = 0
    errors = []
    
    try:
        # Prepara dados para bulk insert
        records = []
        for row in csv_data:
            try:
                record = {}
                for csv_field, model_field in field_mapping.items():
                    value = row.get(csv_field)
                    if value is not None:
                        record[model_field] = value
                
                # Aplica transformação se fornecida
                if transform_func:
                    record = transform_func(record)
                
                # Remove None values
                record = {k: v for k, v in record.items() if v is not None}
                
                if record:
                    records.append(record)
            except Exception as e:
                errors.append(f"Erro ao processar linha: {e}")
                continue
        
        if records:
            try:
                # Tenta bulk insert primeiro (mais rápido)
                session.bulk_insert_mappings(model_class, records)
                inserted_count = len(records)
                logger.info(f"Inseridos {inserted_count} registros em {model_class.__tablename__}")
            except IntegrityError:
                # Se falhar por duplicatas, faz insert individual ignorando duplicatas
                session.rollback()
                logger.debug(f"Bulk insert falhou, tentando insert individual para {model_class.__tablename__}...")
                
                for record in records:
                    try:
                        session.bulk_insert_mappings(model_class, [record])
                        session.flush()  # Flush para detectar erro imediatamente
                        inserted_count += 1
                    except IntegrityError:
                        # Registro já existe, ignora e faz rollback do flush
                        session.rollback()
                        skipped_count += 1
                        continue
                    except Exception as e:
                        session.rollback()
                        errors.append(f"Erro ao inserir registro: {e}")
                        continue
                
                if inserted_count > 0:
                    logger.info(f"Inseridos {inserted_count} registros em {model_class.__tablename__}")
                if skipped_count > 0:
                    logger.debug(f"Pulados {skipped_count} registros duplicados em {model_class.__tablename__}")
        
        if errors:
            logger.warning(f"Erros ao processar {len(errors)} linhas: {errors[:5]}")
    
    except Exception as e:
        logger.error(f"Erro ao carregar dados para {model_class.__tablename__}: {e}")
        raise
    
    return inserted_count

def clear_table(session: Session, model_class: Any) -> bool:
    """Limpa todos os registros de uma tabela"""
    try:
        session.query(model_class).delete()
        logger.info(f"Tabela {model_class.__tablename__} limpa")
        return True
    except Exception as e:
        logger.error(f"Erro ao limpar tabela {model_class.__tablename__}: {e}")
        return False

def load_industrial_base_tables(session: Session, data_dir: Path) -> Dict[str, int]:
    """Carrega tabelas base do banco industrial (sem dependências)"""
    results = {}
    
    logger.info("Carregando tabelas base do banco industrial...")
    
    # Produtos (com mapeamento de IDs)
    produtos_data = read_csv_file(data_dir / "produtos.csv")
    if produtos_data:
        transform = lambda r: {
            'nome_produto': r.get('nome_produto'),
            'descricao': r.get('descricao'),
            'unidade_medida': r.get('unidade_medida'),
            'data_registro': parse_datetime(r.get('data_registro'))
        }
        count, mapping = load_csv_to_model_with_id_mapping(
            session, Produto, produtos_data,
            {'produto_id': 'produto_id', 'nome_produto': 'nome_produto',
             'descricao': 'descricao', 'unidade_medida': 'unidade_medida',
             'data_registro': 'data_registro'},
            transform,
            id_field_name='produto_id',
            mapping_key='produto'
        )
        results['produtos'] = count
        results['produtos_mapping'] = mapping
    
    # Materiais (com mapeamento de IDs)
    materiais_data = read_csv_file(data_dir / "materiais.csv")
    if materiais_data:
        transform = lambda r: {
            'nome_material': r.get('nome_material'),
            'unidade_medida': r.get('unidade_medida'),
            'data_registro': parse_datetime(r.get('data_registro'))
        }
        count, mapping = load_csv_to_model_with_id_mapping(
            session, Material, materiais_data,
            {'material_id': 'material_id', 'nome_material': 'nome_material',
             'unidade_medida': 'unidade_medida', 'data_registro': 'data_registro'},
            transform,
            id_field_name='material_id',
            mapping_key='material'
        )
        results['materiais'] = count
        results['materiais_mapping'] = mapping
    
    # Máquinas (com mapeamento de IDs)
    maquinas_data = read_csv_file(data_dir / "maquinas.csv")
    if maquinas_data:
        transform = lambda r: {
            'nome_maquina': r.get('nome_maquina'),
            'linha_producao': r.get('linha_producao'),
            'capacidade_producao_max': parse_decimal(r.get('capacidade_producao_max')),
            'data_registro': parse_datetime(r.get('data_registro'))
        }
        count, mapping = load_csv_to_model_with_id_mapping(
            session, Maquina, maquinas_data,
            {'maquina_id': 'maquina_id', 'nome_maquina': 'nome_maquina',
             'linha_producao': 'linha_producao', 'capacidade_producao_max': 'capacidade_producao_max',
             'data_registro': 'data_registro'},
            transform,
            id_field_name='maquina_id',
            mapping_key='maquina'
        )
        results['maquinas'] = count
        results['maquinas_mapping'] = mapping
    
    # Fornecedores (com mapeamento de IDs)
    fornecedores_data = read_csv_file(data_dir / "fornecedores.csv")
    if fornecedores_data:
        transform = lambda r: {
            'nome_fornecedor': r.get('nome_fornecedor'),
            'data_registro': parse_datetime(r.get('data_registro'))
        }
        count, mapping = load_csv_to_model_with_id_mapping(
            session, Fornecedor, fornecedores_data,
            {'fornecedor_id': 'fornecedor_id', 'nome_fornecedor': 'nome_fornecedor',
             'data_registro': 'data_registro'},
            transform,
            id_field_name='fornecedor_id',
            mapping_key='fornecedor'
        )
        results['fornecedores'] = count
        results['fornecedores_mapping'] = mapping
    
    # Equipamentos
    equipamentos_data = read_csv_file(data_dir / "equipamentos.csv")
    if equipamentos_data:
        transform = lambda r: {
            'id': parse_int(r.get('id')),
            'nome': r.get('nome'),
            'disponibilidade': parse_float(r.get('disponibilidade')),
            'performance': parse_float(r.get('performance')),
            'qualidade': parse_float(r.get('qualidade')),
            'oee': parse_float(r.get('oee')),
            'taxa_producao': parse_float(r.get('taxa_producao')),
            'capacidade_producao': parse_float(r.get('capacidade_producao')),
            'eficiencia_linha': parse_float(r.get('eficiencia_linha')),
            'produtividade_mao_obra': parse_float(r.get('produtividade_mao_obra')),
            'data_registro': parse_datetime(r.get('data_registro'))
        }
        results['equipamentos'] = load_csv_to_model(
            session, Equipamento, equipamentos_data,
            {'id': 'id', 'nome': 'nome', 'disponibilidade': 'disponibilidade',
             'performance': 'performance', 'qualidade': 'qualidade', 'oee': 'oee',
             'taxa_producao': 'taxa_producao', 'capacidade_producao': 'capacidade_producao',
             'eficiencia_linha': 'eficiencia_linha', 'produtividade_mao_obra': 'produtividade_mao_obra',
             'data_registro': 'data_registro'},
            transform
        )
    
    # Processo Industrial
    processos_data = read_csv_file(data_dir / "processo_industrial.csv")
    if processos_data:
        transform = lambda r: {
            'id': parse_int(r.get('id')),
            'nome': r.get('nome'),
            'area1': parse_float(r.get('area1')),
            'velocidade1': parse_float(r.get('velocidade1')),
            'area2': parse_float(r.get('area2')),
            'velocidade2': parse_float(r.get('velocidade2')),
            'massa': parse_float(r.get('massa')),
            'calor_especifico': parse_float(r.get('calor_especifico')),
            'delta_t': parse_float(r.get('delta_t')),
            'calor_transferido': parse_float(r.get('calor_transferido')),
            'data_registro': parse_datetime(r.get('data_registro'))
        }
        results['processos_industriais'] = load_csv_to_model(
            session, ProcessoIndustrial, processos_data,
            {'id': 'id', 'nome': 'nome', 'area1': 'area1', 'velocidade1': 'velocidade1',
             'area2': 'area2', 'velocidade2': 'velocidade2', 'massa': 'massa',
             'calor_especifico': 'calor_especifico', 'delta_t': 'delta_t',
             'calor_transferido': 'calor_transferido', 'data_registro': 'data_registro'},
            transform
        )
    
    return results

def apply_id_mapping(value: Optional[int], mapping_key: str) -> Optional[int]:
    """Aplica mapeamento de ID antigo para novo ID"""
    if value is None:
        return None
    mapping = ID_MAPPING.get(mapping_key, {})
    return mapping.get(value, value)  # Retorna novo ID ou mantém o original se não encontrado

def load_industrial_dependent_tables(session: Session, data_dir: Path) -> Dict[str, int]:
    """Carrega tabelas dependentes do banco industrial"""
    results = {}
    
    logger.info("Carregando tabelas dependentes do banco industrial...")
    
    # Ordens de Produção (depende de Produto)
    ordens_data = read_csv_file(data_dir / "ordens_producao.csv")
    if ordens_data:
        transform = lambda r: {
            'ordem_producao_id': parse_int(r.get('ordem_producao_id')),
            'produto_id': apply_id_mapping(parse_int(r.get('produto_id')), 'produto'),
            'quantidade_planejada': parse_int(r.get('quantidade_planejada')),
            'data_planejamento': parse_date(r.get('data_planejamento')),
            'data_inicio_real': parse_datetime(r.get('data_inicio_real')),
            'data_fim_real': parse_datetime(r.get('data_fim_real')),
            'status_ordem': r.get('status_ordem')
        }
        results['ordens_producao'] = load_csv_to_model(
            session, OrdemProducao, ordens_data,
            {'ordem_producao_id': 'ordem_producao_id', 'produto_id': 'produto_id',
             'quantidade_planejada': 'quantidade_planejada', 'data_planejamento': 'data_planejamento',
             'data_inicio_real': 'data_inicio_real', 'data_fim_real': 'data_fim_real',
             'status_ordem': 'status_ordem'},
            transform
        )
    
    # Roteiros de Produção (depende de Produto)
    roteiros_data = read_csv_file(data_dir / "roteiros_producao.csv")
    if roteiros_data:
        transform = lambda r: {
            'roteiro_id': parse_int(r.get('roteiro_id')),
            'produto_id': apply_id_mapping(parse_int(r.get('produto_id')), 'produto'),
            'versao': parse_int(r.get('versao'))
        }
        results['roteiros_producao'] = load_csv_to_model(
            session, RoteiroProducao, roteiros_data,
            {'roteiro_id': 'roteiro_id', 'produto_id': 'produto_id', 'versao': 'versao'},
            transform
        )
    
    # Lotes de Materiais (depende de Material e Fornecedor)
    lotes_materiais_data = read_csv_file(data_dir / "lotes_materiais.csv")
    if lotes_materiais_data:
        transform = lambda r: {
            'lote_id': parse_int(r.get('lote_id')),
            'material_id': apply_id_mapping(parse_int(r.get('material_id')), 'material'),
            'fornecedor_id': apply_id_mapping(parse_int(r.get('fornecedor_id')), 'fornecedor'),
            'data_recebimento': parse_date(r.get('data_recebimento')),
            'lote_fornecedor': r.get('lote_fornecedor')
        }
        results['lotes_materiais'] = load_csv_to_model(
            session, LoteMaterial, lotes_materiais_data,
            {'lote_id': 'lote_id', 'material_id': 'material_id',
             'fornecedor_id': 'fornecedor_id', 'data_recebimento': 'data_recebimento',
             'lote_fornecedor': 'lote_fornecedor'},
            transform
        )
    
    # Lotes de Produção (depende de OrdemProducao)
    lotes_producao_data = read_csv_file(data_dir / "lotes_producao.csv")
    if lotes_producao_data:
        transform = lambda r: {
            'lote_producao_id': parse_int(r.get('lote_producao_id')),
            'ordem_producao_id': parse_int(r.get('ordem_producao_id')),
            'data_lote': parse_date(r.get('data_lote')),
            'quantidade_total': parse_int(r.get('quantidade_total'))
        }
        results['lotes_producao'] = load_csv_to_model(
            session, LoteProducao, lotes_producao_data,
            {'lote_producao_id': 'lote_producao_id', 'ordem_producao_id': 'ordem_producao_id',
             'data_lote': 'data_lote', 'quantidade_total': 'quantidade_total'},
            transform
        )
    
    # Registros de Operação (depende de OrdemProducao e Maquina)
    registros_data = read_csv_file(data_dir / "registros_operacao.csv")
    if registros_data:
        transform = lambda r: {
            'registro_id': parse_int(r.get('registro_id')),
            'ordem_producao_id': parse_int(r.get('ordem_producao_id')),
            'maquina_id': apply_id_mapping(parse_int(r.get('maquina_id')), 'maquina'),
            'operador_id': parse_int(r.get('operador_id')),
            'hora_inicio': parse_datetime(r.get('hora_inicio')),
            'hora_fim': parse_datetime(r.get('hora_fim')),
            'tempo_setup_real_min': parse_decimal(r.get('tempo_setup_real_min')),
            'quantidade_produzida_real': parse_int(r.get('quantidade_produzida_real')),
            'consumo_energia_kwh': parse_decimal(r.get('consumo_energia_kwh'))
        }
        results['registros_operacao'] = load_csv_to_model(
            session, RegistroOperacao, registros_data,
            {'registro_id': 'registro_id', 'ordem_producao_id': 'ordem_producao_id',
             'maquina_id': 'maquina_id', 'operador_id': 'operador_id',
             'hora_inicio': 'hora_inicio', 'hora_fim': 'hora_fim',
             'tempo_setup_real_min': 'tempo_setup_real_min',
             'quantidade_produzida_real': 'quantidade_produzida_real',
             'consumo_energia_kwh': 'consumo_energia_kwh'},
            transform
        )
    
    # Paradas de Máquinas (depende de Maquina)
    paradas_data = read_csv_file(data_dir / "paradas_maquinas.csv")
    if paradas_data:
        transform = lambda r: {
            'parada_id': parse_int(r.get('parada_id')),
            'maquina_id': apply_id_mapping(parse_int(r.get('maquina_id')), 'maquina'),
            'hora_inicio_parada': parse_datetime(r.get('hora_inicio_parada')),
            'hora_fim_parada': parse_datetime(r.get('hora_fim_parada')),
            'motivo_parada': r.get('motivo_parada')
        }
        results['paradas_maquinas'] = load_csv_to_model(
            session, ParadaMaquina, paradas_data,
            {'parada_id': 'parada_id', 'maquina_id': 'maquina_id',
             'hora_inicio_parada': 'hora_inicio_parada', 'hora_fim_parada': 'hora_fim_parada',
             'motivo_parada': 'motivo_parada'},
            transform
        )
    
    # Consumo de Materiais (depende de RegistroOperacao, Material, LoteMaterial)
    consumo_data = read_csv_file(data_dir / "consumo_materiais.csv")
    if consumo_data:
        transform = lambda r: {
            'consumo_id': parse_int(r.get('consumo_id')),
            'registro_id': parse_int(r.get('registro_id')),
            'material_id': apply_id_mapping(parse_int(r.get('material_id')), 'material'),
            'lote_material_id': parse_int(r.get('lote_material_id')),
            'quantidade_consumida': parse_decimal(r.get('quantidade_consumida'))
        }
        results['consumo_materiais'] = load_csv_to_model(
            session, ConsumoMaterial, consumo_data,
            {'consumo_id': 'consumo_id', 'registro_id': 'registro_id',
             'material_id': 'material_id', 'lote_material_id': 'lote_material_id',
             'quantidade_consumida': 'quantidade_consumida'},
            transform
        )
    
    # Controle de Qualidade (depende de LoteProducao)
    qualidade_data = read_csv_file(data_dir / "controle_qualidade.csv")
    if qualidade_data:
        transform = lambda r: {
            'controle_id': parse_int(r.get('controle_id')),
            'lote_producao_id': parse_int(r.get('lote_producao_id')),
            'data_inspecao': parse_datetime(r.get('data_inspecao')),
            'inspetor_id': parse_int(r.get('inspetor_id')),
            'unidades_aprovadas': parse_int(r.get('unidades_aprovadas')),
            'unidades_rejeitadas': parse_int(r.get('unidades_rejeitadas')),
            'motivo_rejeicao': r.get('motivo_rejeicao')
        }
        results['controle_qualidade'] = load_csv_to_model(
            session, ControleQualidade, qualidade_data,
            {'controle_id': 'controle_id', 'lote_producao_id': 'lote_producao_id',
             'data_inspecao': 'data_inspecao', 'inspetor_id': 'inspetor_id',
             'unidades_aprovadas': 'unidades_aprovadas',
             'unidades_rejeitadas': 'unidades_rejeitadas',
             'motivo_rejeicao': 'motivo_rejeicao'},
            transform
        )
    
    return results

def load_industrial_data(periods: Optional[List[str]] = None, clear_existing: bool = False) -> Dict[str, Any]:
    """
    Carrega todos os dados industriais
    
    Args:
        periods: Lista de períodos para carregar (None = todos)
        clear_existing: Se True, limpa dados existentes antes de carregar
    
    Returns:
        Dicionário com resultados do carregamento
    """
    if periods is None:
        periods = ["2015-2017", "2017-2020", "2021-2025"]
    
    session = industrial_connection.get_session()
    all_results = {}
    
    try:
        if clear_existing:
            logger.info("Limpando dados existentes do banco industrial...")
            # Limpa na ordem inversa das dependências
            clear_table(session, ControleQualidade)
            clear_table(session, ConsumoMaterial)
            clear_table(session, ParadaMaquina)
            clear_table(session, RegistroOperacao)
            clear_table(session, LoteProducao)
            clear_table(session, LoteMaterial)
            clear_table(session, RoteiroProducao)
            clear_table(session, OrdemProducao)
            clear_table(session, ProcessoIndustrial)
            clear_table(session, Equipamento)
            clear_table(session, Fornecedor)
            clear_table(session, Maquina)
            clear_table(session, Material)
            clear_table(session, Produto)
        
        for period in periods:
            period_dir_name = INDUSTRIAL_PERIODS_MAPPING.get(period)
            if not period_dir_name:
                logger.warning(f"Período não encontrado: {period}")
                continue
            
            data_dir = BASE_DATA_DIR / period_dir_name
            if not data_dir.exists():
                logger.warning(f"Diretório não encontrado: {data_dir}")
                continue
            
            logger.info(f"Carregando dados industriais do período {period}...")
            period_results = {}
            
            # Carrega tabelas base primeiro
            base_results = load_industrial_base_tables(session, data_dir)
            period_results.update(base_results)
            
            # Depois carrega tabelas dependentes
            dependent_results = load_industrial_dependent_tables(session, data_dir)
            period_results.update(dependent_results)
            
            all_results[period] = period_results
        
        session.commit()
        logger.info("Dados industriais carregados com sucesso!")
    
    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao carregar dados industriais: {e}")
        raise
    finally:
        session.close()
    
    return all_results

def load_financeiro_base_tables(session: Session, data_dir: Path) -> Dict[str, int]:
    """Carrega tabelas base do banco financeiro (sem dependências)"""
    results = {}
    
    logger.info("Carregando tabelas base do banco financeiro...")
    
    # Contas Contábeis (com mapeamento de IDs)
    contas_data = read_csv_file(data_dir / "contas_contabeis.csv")
    if contas_data:
        transform = lambda r: {
            'numero_conta': r.get('numero_conta'),
            'nome_conta': r.get('nome_conta'),
            'tipo_conta': r.get('tipo_conta')
        }
        count, mapping = load_csv_to_model_with_id_mapping(
            session, ContaContabil, contas_data,
            {'conta_id': 'conta_id', 'numero_conta': 'numero_conta',
             'nome_conta': 'nome_conta', 'tipo_conta': 'tipo_conta'},
            transform,
            id_field_name='conta_id',
            mapping_key='conta_contabil'
        )
        results['contas_contabeis'] = count
        results['contas_contabeis_mapping'] = mapping
    
    # Custos Padrão (com mapeamento de IDs)
    custos_padrao_data = read_csv_file(data_dir / "custos_padrao.csv")
    if custos_padrao_data:
        transform = lambda r: {
            'tipo_custo': r.get('tipo_custo'),
            'unidade_medida': r.get('unidade_medida'),
            'valor_unitario_padrao': parse_decimal(r.get('valor_unitario_padrao')),
            'data_vigencia': parse_date(r.get('data_vigencia'))
        }
        count, mapping = load_csv_to_model_with_id_mapping(
            session, CustoPadrao, custos_padrao_data,
            {'custo_padrao_id': 'custo_padrao_id', 'tipo_custo': 'tipo_custo',
             'unidade_medida': 'unidade_medida', 'valor_unitario_padrao': 'valor_unitario_padrao',
             'data_vigencia': 'data_vigencia'},
            transform,
            id_field_name='custo_padrao_id',
            mapping_key='custo_padrao'
        )
        results['custos_padrao'] = count
        results['custos_padrao_mapping'] = mapping
    
    # Custos Indiretos Rateio
    rateio_data = read_csv_file(data_dir / "custos_indiretos_rateio.csv")
    if rateio_data:
        transform = lambda r: {
            'rateio_id': parse_int(r.get('rateio_id')),
            'descricao': r.get('descricao'),
            'custo_total_mes': parse_decimal(r.get('custo_total_mes')),
            'base_rateio': r.get('base_rateio'),
            'data_referencia': parse_date(r.get('data_referencia'))
        }
        results['custos_indiretos_rateio'] = load_csv_to_model(
            session, CustoIndiretoRateio, rateio_data,
            {'rateio_id': 'rateio_id', 'descricao': 'descricao',
             'custo_total_mes': 'custo_total_mes', 'base_rateio': 'base_rateio',
             'data_referencia': 'data_referencia'},
            transform
        )
    
    # Custos Operacionais Variáveis
    custos_op_var_data = read_csv_file(data_dir / "custos_operacionais_variaveis.csv")
    if custos_op_var_data:
        transform = lambda r: {
            'custo_operacional_id': parse_int(r.get('custo_operacional_id')),
            'insumo': r.get('insumo'),
            'valor_unitario': parse_decimal(r.get('valor_unitario')),
            'unidade_medida': r.get('unidade_medida'),
            'data_leitura': parse_date(r.get('data_leitura'))
        }
        results['custos_operacionais_variaveis'] = load_csv_to_model(
            session, CustoOperacionalVariavel, custos_op_var_data,
            {'custo_operacional_id': 'custo_operacional_id', 'insumo': 'insumo',
             'valor_unitario': 'valor_unitario', 'unidade_medida': 'unidade_medida',
             'data_leitura': 'data_leitura'},
            transform
        )
    
    return results

def load_financeiro_dependent_tables(session: Session, data_dir: Path) -> Dict[str, int]:
    """Carrega tabelas dependentes do banco financeiro"""
    results = {}
    
    logger.info("Carregando tabelas dependentes do banco financeiro...")
    
    # Lançamentos Financeiros (depende de ContaContabil)
    lancamentos_data = read_csv_file(data_dir / "lancamentos_financeiros.csv")
    if lancamentos_data:
        transform = lambda r: {
            'lancamento_id': parse_int(r.get('lancamento_id')),
            'conta_id': apply_id_mapping(parse_int(r.get('conta_id')), 'conta_contabil'),
            'data_lancamento': parse_date(r.get('data_lancamento')),
            'valor': parse_decimal(r.get('valor')),
            'descricao': r.get('descricao')
        }
        results['lancamentos_financeiros'] = load_csv_to_model(
            session, LancamentoFinanceiro, lancamentos_data,
            {'lancamento_id': 'lancamento_id', 'conta_id': 'conta_id',
             'data_lancamento': 'data_lancamento', 'valor': 'valor',
             'descricao': 'descricao'},
            transform
        )
    
    # Vendas
    vendas_data = read_csv_file(data_dir / "vendas.csv")
    if vendas_data:
        transform = lambda r: {
            'venda_id': parse_int(r.get('venda_id')),
            'produto_id': parse_int(r.get('produto_id')),
            'quantidade_vendida': parse_int(r.get('quantidade_vendida')),
            'preco_unitario_venda': parse_decimal(r.get('preco_unitario_venda')),
            'data_venda': parse_date(r.get('data_venda')),
            'cliente_id': parse_int(r.get('cliente_id'))
        }
        results['vendas'] = load_csv_to_model(
            session, Venda, vendas_data,
            {'venda_id': 'venda_id', 'produto_id': 'produto_id',
             'quantidade_vendida': 'quantidade_vendida',
             'preco_unitario_venda': 'preco_unitario_venda',
             'data_venda': 'data_venda', 'cliente_id': 'cliente_id'},
            transform
        )
    
    # Materiais Custo Histórico
    materiais_custo_data = read_csv_file(data_dir / "materiais_custo_historico.csv")
    if materiais_custo_data:
        transform = lambda r: {
            'custo_material_id': parse_int(r.get('custo_material_id')),
            'material_id': apply_id_mapping(parse_int(r.get('material_id')), 'material'),
            'custo_unitario': parse_decimal(r.get('custo_unitario')),
            'data_compra': parse_date(r.get('data_compra')),
            'lote_material_id': parse_int(r.get('lote_material_id'))
        }
        results['materiais_custo_historico'] = load_csv_to_model(
            session, MaterialCustoHistorico, materiais_custo_data,
            {'custo_material_id': 'custo_material_id', 'material_id': 'material_id',
             'custo_unitario': 'custo_unitario', 'data_compra': 'data_compra',
             'lote_material_id': 'lote_material_id'},
            transform
        )
    
    # Custo Mão de Obra Histórico
    custo_mo_data = read_csv_file(data_dir / "custo_mao_obra_historico.csv")
    if custo_mo_data:
        transform = lambda r: {
            'custo_mo_id': parse_int(r.get('custo_mo_id')),
            'operador_id': parse_int(r.get('operador_id')),
            'custo_hora': parse_decimal(r.get('custo_hora')),
            'data_vigencia': parse_date(r.get('data_vigencia')),
            'tipo_custo': r.get('tipo_custo')
        }
        results['custo_mao_obra_historico'] = load_csv_to_model(
            session, CustoMaoObraHistorico, custo_mo_data,
            {'custo_mo_id': 'custo_mo_id', 'operador_id': 'operador_id',
             'custo_hora': 'custo_hora', 'data_vigencia': 'data_vigencia',
             'tipo_custo': 'tipo_custo'},
            transform
        )
    
    # Custos de Produção
    custos_producao_data = read_csv_file(data_dir / "custos_producao.csv")
    if custos_producao_data:
        transform = lambda r: {
            'id': parse_int(r.get('id')),
            'materia_prima': parse_float(r.get('materia_prima')),
            'mao_obra_direta': parse_float(r.get('mao_obra_direta')),
            'custos_indiretos': parse_float(r.get('custos_indiretos')),
            'estoque_inicial_elaboracao': parse_float(r.get('estoque_inicial_elaboracao')),
            'estoque_final_elaboracao': parse_float(r.get('estoque_final_elaboracao')),
            'estoque_inicial_acabados': parse_float(r.get('estoque_inicial_acabados')),
            'estoque_final_acabados': parse_float(r.get('estoque_final_acabados')),
            'unidades_produzidas': parse_float(r.get('unidades_produzidas')),
            'custo_total': parse_float(r.get('custo_total')),
            'custo_unitario': parse_float(r.get('custo_unitario')),
            'data_registro': parse_datetime(r.get('data_registro'))
        }
        results['custos_producao'] = load_csv_to_model(
            session, CustoProducao, custos_producao_data,
            {'id': 'id', 'materia_prima': 'materia_prima',
             'mao_obra_direta': 'mao_obra_direta', 'custos_indiretos': 'custos_indiretos',
             'estoque_inicial_elaboracao': 'estoque_inicial_elaboracao',
             'estoque_final_elaboracao': 'estoque_final_elaboracao',
             'estoque_inicial_acabados': 'estoque_inicial_acabados',
             'estoque_final_acabados': 'estoque_final_acabados',
             'unidades_produzidas': 'unidades_produzidas', 'custo_total': 'custo_total',
             'custo_unitario': 'custo_unitario', 'data_registro': 'data_registro'},
            transform
        )
    
    # Resultados Financeiros
    resultados_data = read_csv_file(data_dir / "resultados_financeiros.csv")
    if resultados_data:
        transform = lambda r: {
            'id': parse_int(r.get('id')),
            'receita_total': parse_float(r.get('receita_total')),
            'custos_variaveis': parse_float(r.get('custos_variaveis')),
            'despesas_variaveis': parse_float(r.get('despesas_variaveis')),
            'custos_fixos': parse_float(r.get('custos_fixos')),
            'despesas_operacionais': parse_float(r.get('despesas_operacionais')),
            'juros': parse_float(r.get('juros')),
            'impostos': parse_float(r.get('impostos')),
            'custo_ativo': parse_float(r.get('custo_ativo')),
            'valor_residual': parse_float(r.get('valor_residual')),
            'vida_util_anos': parse_float(r.get('vida_util_anos')),
            'custo_investimento': parse_float(r.get('custo_investimento')),
            'ativos_circulantes': parse_float(r.get('ativos_circulantes')),
            'passivos_circulantes': parse_float(r.get('passivos_circulantes')),
            'margem_contribuicao': parse_float(r.get('margem_contribuicao')),
            'ponto_equilibrio': parse_float(r.get('ponto_equilibrio')),
            'lucro_bruto': parse_float(r.get('lucro_bruto')),
            'lucro_liquido': parse_float(r.get('lucro_liquido')),
            'depreciacao_anual': parse_float(r.get('depreciacao_anual')),
            'roi_percentual': parse_float(r.get('roi_percentual')),
            'capital_de_giro': parse_float(r.get('capital_de_giro'))
        }
        results['resultados_financeiros'] = load_csv_to_model(
            session, ResultadoFinanceiro, resultados_data,
            {'id': 'id', 'receita_total': 'receita_total',
             'custos_variaveis': 'custos_variaveis', 'despesas_variaveis': 'despesas_variaveis',
             'custos_fixos': 'custos_fixos', 'despesas_operacionais': 'despesas_operacionais',
             'juros': 'juros', 'impostos': 'impostos', 'custo_ativo': 'custo_ativo',
             'valor_residual': 'valor_residual', 'vida_util_anos': 'vida_util_anos',
             'custo_investimento': 'custo_investimento', 'ativos_circulantes': 'ativos_circulantes',
             'passivos_circulantes': 'passivos_circulantes', 'margem_contribuicao': 'margem_contribuicao',
             'ponto_equilibrio': 'ponto_equilibrio', 'lucro_bruto': 'lucro_bruto',
             'lucro_liquido': 'lucro_liquido', 'depreciacao_anual': 'depreciacao_anual',
             'roi_percentual': 'roi_percentual', 'capital_de_giro': 'capital_de_giro'},
            transform
        )
    
    # KPIs Gerenciais
    kpis_data = read_csv_file(data_dir / "kpis_gerenciais.csv")
    if kpis_data:
        transform = lambda r: {
            'kpi_id': parse_int(r.get('kpi_id')),
            'nome_kpi': r.get('nome_kpi'),
            'valor_kpi': parse_decimal(r.get('valor_kpi')),
            'data_referencia': parse_date(r.get('data_referencia'))
        }
        results['kpis_gerenciais'] = load_csv_to_model(
            session, KPIGerencial, kpis_data,
            {'kpi_id': 'kpi_id', 'nome_kpi': 'nome_kpi',
             'valor_kpi': 'valor_kpi', 'data_referencia': 'data_referencia'},
            transform
        )
    
    return results

def load_financeiro_data(periods: Optional[List[str]] = None, clear_existing: bool = False) -> Dict[str, Any]:
    """
    Carrega todos os dados financeiros
    
    Args:
        periods: Lista de períodos para carregar (None = todos)
        clear_existing: Se True, limpa dados existentes antes de carregar
    
    Returns:
        Dicionário com resultados do carregamento
    """
    if periods is None:
        periods = ["2015-2016", "2017-2020", "2021-2025"]
    
    session = financeiro_connection.get_session()
    all_results = {}
    
    try:
        if clear_existing:
            logger.info("Limpando dados existentes do banco financeiro...")
            # Limpa na ordem inversa das dependências
            clear_table(session, KPIGerencial)
            clear_table(session, ResultadoFinanceiro)
            clear_table(session, CustoProducao)
            clear_table(session, CustoMaoObraHistorico)
            clear_table(session, MaterialCustoHistorico)
            clear_table(session, Venda)
            clear_table(session, LancamentoFinanceiro)
            clear_table(session, CustoOperacionalVariavel)
            clear_table(session, CustoIndiretoRateio)
            clear_table(session, CustoPadrao)
            clear_table(session, ContaContabil)
        
        for period in periods:
            period_dir_name = FINANCEIRO_PERIODS_MAPPING.get(period)
            if not period_dir_name:
                logger.warning(f"Período não encontrado: {period}")
                continue
            
            data_dir = BASE_DATA_DIR / period_dir_name
            if not data_dir.exists():
                logger.warning(f"Diretório não encontrado: {data_dir}")
                continue
            
            logger.info(f"Carregando dados financeiros do período {period}...")
            period_results = {}
            
            # Carrega tabelas base primeiro
            base_results = load_financeiro_base_tables(session, data_dir)
            period_results.update(base_results)
            
            # Depois carrega tabelas dependentes
            dependent_results = load_financeiro_dependent_tables(session, data_dir)
            period_results.update(dependent_results)
            
            all_results[period] = period_results
        
        session.commit()
        logger.info("Dados financeiros carregados com sucesso!")
    
    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao carregar dados financeiros: {e}")
        raise
    finally:
        session.close()
    
    return all_results

def load_all_data(
    industrial_periods: Optional[List[str]] = None,
    financeiro_periods: Optional[List[str]] = None,
    clear_existing: bool = False
) -> Dict[str, Any]:
    """
    Carrega todos os dados (industriais e financeiros)
    
    Args:
        industrial_periods: Lista de períodos industriais para carregar (None = todos)
        financeiro_periods: Lista de períodos financeiros para carregar (None = todos)
        clear_existing: Se True, limpa dados existentes antes de carregar
    
    Returns:
        Dicionário com resultados do carregamento
    """
    logger.info("=" * 60)
    logger.info("Iniciando carregamento de dados")
    logger.info("=" * 60)
    
    results = {
        'industrial': {},
        'financeiro': {}
    }
    
    try:
        # Carrega dados industriais
        logger.info("\n" + "=" * 60)
        logger.info("CARREGANDO DADOS INDUSTRIAIS")
        logger.info("=" * 60)
        results['industrial'] = load_industrial_data(industrial_periods, clear_existing)
        
        # Carrega dados financeiros
        logger.info("\n" + "=" * 60)
        logger.info("CARREGANDO DADOS FINANCEIROS")
        logger.info("=" * 60)
        results['financeiro'] = load_financeiro_data(financeiro_periods, clear_existing)
        
        logger.info("\n" + "=" * 60)
        logger.info("Carregamento concluído com sucesso!")
        logger.info("=" * 60)
    
    except Exception as e:
        logger.error(f"Erro durante carregamento: {e}")
        raise
    
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Carrega dados dos CSVs para os bancos de dados")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Limpa dados existentes antes de carregar"
    )
    parser.add_argument(
        "--industrial-only",
        action="store_true",
        help="Carrega apenas dados industriais"
    )
    parser.add_argument(
        "--financeiro-only",
        action="store_true",
        help="Carrega apenas dados financeiros"
    )
    parser.add_argument(
        "--periods",
        nargs="+",
        help="Períodos específicos para carregar (ex: 2021-2025 2017-2020)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.industrial_only:
            load_industrial_data(periods=args.periods, clear_existing=args.clear)
        elif args.financeiro_only:
            load_financeiro_data(periods=args.periods, clear_existing=args.clear)
        else:
            load_all_data(clear_existing=args.clear)
    except Exception as e:
        logger.error(f"Erro ao executar script: {e}")
        sys.exit(1)

