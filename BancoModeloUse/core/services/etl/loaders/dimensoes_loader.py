# core/services/etl/loaders/dimensoes_loader.py
"""
Loader para carregar dimensões na DW
"""
from typing import List, Dict, Any
from infrastructure.database.sessions import get_dw_db
from core.repositories.dw import DimensoesRepository
from core.models.dw.dimensoes import DimProduto, DimTempo, DimMaquina, DimCliente, DimFornecedor

class DimensoesLoader:
    """Loader para dimensões da DW"""
    
    def __init__(self):
        self.dimensoes_repo = None
    
    def _get_repository(self, db_session):
        """Inicializa repositório com sessão"""
        if not self.dimensoes_repo:
            self.dimensoes_repo = DimensoesRepository(db_session)
    
    def carregar_produtos(self, produtos_data: List[Dict[str, Any]]) -> int:
        """Carrega produtos na DW"""
        carregados = 0
        
        with get_dw_db() as db:
            self._get_repository(db)
            
            for produto_data in produtos_data:
                try:
                    # Verificar se produto já existe
                    produto_existente = None
                    if produto_data.get('produto_id_financeiro'):
                        produto_existente = self.dimensoes_repo.get_produto_by_financeiro_id(
                            produto_data['produto_id_financeiro']
                        )
                    elif produto_data.get('produto_id_industrial'):
                        produto_existente = self.dimensoes_repo.get_produto_by_industrial_id(
                            produto_data['produto_id_industrial']
                        )
                    
                    if not produto_existente:
                        # Criar novo produto
                        produto = self.dimensoes_repo.create_produto(produto_data)
                        carregados += 1
                    else:
                        # Atualizar produto existente
                        for key, value in produto_data.items():
                            if hasattr(produto_existente, key):
                                setattr(produto_existente, key, value)
                        db.commit()
                        carregados += 1
                        
                except Exception as e:
                    print(f"Erro ao carregar produto: {e}")
                    continue
        
        return carregados
    
    def carregar_tempos(self, tempos_data: List[Dict[str, Any]]) -> int:
        """Carrega tempos na DW"""
        carregados = 0
        
        with get_dw_db() as db:
            self._get_repository(db)
            
            for tempo_data in tempos_data:
                try:
                    # Verificar se tempo já existe
                    tempo_existente = self.dimensoes_repo.get_tempo_by_data(tempo_data['data'])
                    
                    if not tempo_existente:
                        # Criar novo tempo
                        tempo = self.dimensoes_repo.create_tempo(tempo_data)
                        carregados += 1
                    else:
                        # Atualizar tempo existente
                        for key, value in tempo_data.items():
                            if hasattr(tempo_existente, key):
                                setattr(tempo_existente, key, value)
                        db.commit()
                        carregados += 1
                        
                except Exception as e:
                    print(f"Erro ao carregar tempo: {e}")
                    continue
        
        return carregados
    
    def carregar_maquinas(self, maquinas_data: List[Dict[str, Any]]) -> int:
        """Carrega máquinas na DW"""
        carregados = 0
        
        with get_dw_db() as db:
            self._get_repository(db)
            
            for maquina_data in maquinas_data:
                try:
                    # Verificar se máquina já existe
                    maquina_existente = self.dimensoes_repo.get_maquina_by_industrial_id(
                        maquina_data['maquina_id_industrial']
                    )
                    
                    if not maquina_existente:
                        # Criar nova máquina
                        maquina = self.dimensoes_repo.create_maquina(maquina_data)
                        carregados += 1
                    else:
                        # Atualizar máquina existente
                        for key, value in maquina_data.items():
                            if hasattr(maquina_existente, key):
                                setattr(maquina_existente, key, value)
                        db.commit()
                        carregados += 1
                        
                except Exception as e:
                    print(f"Erro ao carregar máquina: {e}")
                    continue
        
        return carregados
    
    def carregar_clientes(self, clientes_data: List[Dict[str, Any]]) -> int:
        """Carrega clientes na DW"""
        carregados = 0
        
        with get_dw_db() as db:
            self._get_repository(db)
            
            for cliente_data in clientes_data:
                try:
                    # Verificar se cliente já existe
                    cliente_existente = self.dimensoes_repo.get_cliente_by_financeiro_id(
                        cliente_data['cliente_id_financeiro']
                    )
                    
                    if not cliente_existente:
                        # Criar novo cliente
                        cliente = self.dimensoes_repo.create_cliente(cliente_data)
                        carregados += 1
                    else:
                        # Atualizar cliente existente
                        for key, value in cliente_data.items():
                            if hasattr(cliente_existente, key):
                                setattr(cliente_existente, key, value)
                        db.commit()
                        carregados += 1
                        
                except Exception as e:
                    print(f"Erro ao carregar cliente: {e}")
                    continue
        
        return carregados
    
    def carregar_fornecedores(self, fornecedores_data: List[Dict[str, Any]]) -> int:
        """Carrega fornecedores na DW"""
        carregados = 0
        
        with get_dw_db() as db:
            self._get_repository(db)
            
            for fornecedor_data in fornecedores_data:
                try:
                    # Verificar se fornecedor já existe
                    fornecedor_existente = self.dimensoes_repo.get_fornecedor_by_industrial_id(
                        fornecedor_data['fornecedor_id_industrial']
                    )
                    
                    if not fornecedor_existente:
                        # Criar novo fornecedor
                        fornecedor = self.dimensoes_repo.create_fornecedor(fornecedor_data)
                        carregados += 1
                    else:
                        # Atualizar fornecedor existente
                        for key, value in fornecedor_data.items():
                            if hasattr(fornecedor_existente, key):
                                setattr(fornecedor_existente, key, value)
                        db.commit()
                        carregados += 1
                        
                except Exception as e:
                    print(f"Erro ao carregar fornecedor: {e}")
                    continue
        
        return carregados
    
    def carregar_todas_dimensoes(self, dimensoes_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, int]:
        """Carrega todas as dimensões na DW"""
        resultados = {}
        
        if 'produtos' in dimensoes_data:
            resultados['produtos'] = self.carregar_produtos(dimensoes_data['produtos'])
        
        if 'tempos' in dimensoes_data:
            resultados['tempos'] = self.carregar_tempos(dimensoes_data['tempos'])
        
        if 'maquinas' in dimensoes_data:
            resultados['maquinas'] = self.carregar_maquinas(dimensoes_data['maquinas'])
        
        if 'clientes' in dimensoes_data:
            resultados['clientes'] = self.carregar_clientes(dimensoes_data['clientes'])
        
        if 'fornecedores' in dimensoes_data:
            resultados['fornecedores'] = self.carregar_fornecedores(dimensoes_data['fornecedores'])
        
        return resultados
