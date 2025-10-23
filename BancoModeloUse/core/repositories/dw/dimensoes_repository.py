# core/repositories/dw/dimensoes_repository.py
"""
Repositório para operações em dimensões da DW
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from core.models.dw.dimensoes import (
    DimProduto, DimTempo, DimMaquina, DimCliente, DimFornecedor
)
from core.repositories.base import BaseRepository

class DimensoesRepository(BaseRepository):
    """Repositório para operações em dimensões"""
    
    # Operações com DimProduto
    def get_all_produtos(self):
        """Retorna todos os produtos"""
        return self.db.query(DimProduto).all()
    
    def get_produto_by_sk(self, produto_sk: int):
        """Busca produto por surrogate key"""
        return self.db.query(DimProduto).filter(
            DimProduto.produto_sk == produto_sk
        ).first()
    
    def get_produto_by_financeiro_id(self, produto_id_financeiro: int):
        """Busca produto por ID financeiro"""
        return self.db.query(DimProduto).filter(
            DimProduto.produto_id_financeiro == produto_id_financeiro
        ).first()
    
    def get_produto_by_industrial_id(self, produto_id_industrial: int):
        """Busca produto por ID industrial"""
        return self.db.query(DimProduto).filter(
            DimProduto.produto_id_industrial == produto_id_industrial
        ).first()
    
    def get_produtos_ativos(self):
        """Retorna produtos ativos"""
        return self.db.query(DimProduto).filter(DimProduto.ativo == True).all()
    
    def get_produtos_by_categoria(self, categoria: str):
        """Busca produtos por categoria"""
        return self.db.query(DimProduto).filter(
            DimProduto.categoria == categoria
        ).all()
    
    # Operações com DimTempo
    def get_all_tempos(self):
        """Retorna todas as dimensões de tempo"""
        return self.db.query(DimTempo).all()
    
    def get_tempo_by_sk(self, tempo_sk: int):
        """Busca tempo por surrogate key"""
        return self.db.query(DimTempo).filter(
            DimTempo.tempo_sk == tempo_sk
        ).first()
    
    def get_tempo_by_data(self, data):
        """Busca tempo por data"""
        return self.db.query(DimTempo).filter(DimTempo.data == data).first()
    
    def get_tempos_by_ano(self, ano: int):
        """Busca tempos por ano"""
        return self.db.query(DimTempo).filter(DimTempo.ano == ano).all()
    
    def get_tempos_by_mes(self, mes: int, ano: int):
        """Busca tempos por mês e ano"""
        return self.db.query(DimTempo).filter(
            DimTempo.mes == mes,
            DimTempo.ano == ano
        ).all()
    
    def get_tempos_by_trimestre(self, trimestre: int, ano: int):
        """Busca tempos por trimestre e ano"""
        return self.db.query(DimTempo).filter(
            DimTempo.trimestre == trimestre,
            DimTempo.ano == ano
        ).all()
    
    def get_feriados(self):
        """Retorna datas que são feriados"""
        return self.db.query(DimTempo).filter(DimTempo.feriado == True).all()
    
    # Operações com DimMaquina
    def get_all_maquinas(self):
        """Retorna todas as máquinas"""
        return self.db.query(DimMaquina).all()
    
    def get_maquina_by_sk(self, maquina_sk: int):
        """Busca máquina por surrogate key"""
        return self.db.query(DimMaquina).filter(
            DimMaquina.maquina_sk == maquina_sk
        ).first()
    
    def get_maquina_by_industrial_id(self, maquina_id_industrial: int):
        """Busca máquina por ID industrial"""
        return self.db.query(DimMaquina).filter(
            DimMaquina.maquina_id_industrial == maquina_id_industrial
        ).first()
    
    def get_maquinas_ativas(self):
        """Retorna máquinas ativas"""
        return self.db.query(DimMaquina).filter(DimMaquina.ativo == True).all()
    
    def get_maquinas_by_linha_producao(self, linha_producao: str):
        """Busca máquinas por linha de produção"""
        return self.db.query(DimMaquina).filter(
            DimMaquina.linha_producao == linha_producao
        ).all()
    
    def get_maquinas_by_centro_custo(self, centro_custo: str):
        """Busca máquinas por centro de custo"""
        return self.db.query(DimMaquina).filter(
            DimMaquina.centro_custo == centro_custo
        ).all()
    
    # Operações com DimCliente
    def get_all_clientes(self):
        """Retorna todos os clientes"""
        return self.db.query(DimCliente).all()
    
    def get_cliente_by_sk(self, cliente_sk: int):
        """Busca cliente por surrogate key"""
        return self.db.query(DimCliente).filter(
            DimCliente.cliente_sk == cliente_sk
        ).first()
    
    def get_cliente_by_financeiro_id(self, cliente_id_financeiro: int):
        """Busca cliente por ID financeiro"""
        return self.db.query(DimCliente).filter(
            DimCliente.cliente_id_financeiro == cliente_id_financeiro
        ).first()
    
    def get_clientes_ativos(self):
        """Retorna clientes ativos"""
        return self.db.query(DimCliente).filter(DimCliente.ativo == True).all()
    
    def get_clientes_by_segmento(self, segmento: str):
        """Busca clientes por segmento"""
        return self.db.query(DimCliente).filter(
            DimCliente.segmento == segmento
        ).all()
    
    def get_clientes_by_regiao(self, regiao: str):
        """Busca clientes por região"""
        return self.db.query(DimCliente).filter(
            DimCliente.regiao == regiao
        ).all()
    
    # Operações com DimFornecedor
    def get_all_fornecedores(self):
        """Retorna todos os fornecedores"""
        return self.db.query(DimFornecedor).all()
    
    def get_fornecedor_by_sk(self, fornecedor_sk: int):
        """Busca fornecedor por surrogate key"""
        return self.db.query(DimFornecedor).filter(
            DimFornecedor.fornecedor_sk == fornecedor_sk
        ).first()
    
    def get_fornecedor_by_industrial_id(self, fornecedor_id_industrial: int):
        """Busca fornecedor por ID industrial"""
        return self.db.query(DimFornecedor).filter(
            DimFornecedor.fornecedor_id_industrial == fornecedor_id_industrial
        ).first()
    
    def get_fornecedores_ativos(self):
        """Retorna fornecedores ativos"""
        return self.db.query(DimFornecedor).filter(DimFornecedor.ativo == True).all()
    
    def get_fornecedores_by_categoria(self, categoria: str):
        """Busca fornecedores por categoria"""
        return self.db.query(DimFornecedor).filter(
            DimFornecedor.categoria == categoria
        ).all()
    
    def get_fornecedores_by_regiao(self, regiao: str):
        """Busca fornecedores por região"""
        return self.db.query(DimFornecedor).filter(
            DimFornecedor.regiao == regiao
        ).all()
    
    # Métodos de criação
    def create_produto(self, produto_data: dict):
        """Cria novo produto"""
        produto = DimProduto(**produto_data)
        self.db.add(produto)
        self.db.commit()
        self.db.refresh(produto)
        return produto
    
    def create_tempo(self, tempo_data: dict):
        """Cria nova dimensão de tempo"""
        tempo = DimTempo(**tempo_data)
        self.db.add(tempo)
        self.db.commit()
        self.db.refresh(tempo)
        return tempo
    
    def create_maquina(self, maquina_data: dict):
        """Cria nova máquina"""
        maquina = DimMaquina(**maquina_data)
        self.db.add(maquina)
        self.db.commit()
        self.db.refresh(maquina)
        return maquina
    
    def create_cliente(self, cliente_data: dict):
        """Cria novo cliente"""
        cliente = DimCliente(**cliente_data)
        self.db.add(cliente)
        self.db.commit()
        self.db.refresh(cliente)
        return cliente
    
    def create_fornecedor(self, fornecedor_data: dict):
        """Cria novo fornecedor"""
        fornecedor = DimFornecedor(**fornecedor_data)
        self.db.add(fornecedor)
        self.db.commit()
        self.db.refresh(fornecedor)
        return fornecedor
