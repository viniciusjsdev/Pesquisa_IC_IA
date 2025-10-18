# core/services/etl/loaders/fatos_loader.py
"""
Loader para carregar fatos na DW
"""
from typing import List, Dict, Any
from infrastructure.database.sessions import get_dw_db
from core.repositories.dw import FatosRepository

class FatosLoader:
    """Loader para fatos da DW"""
    
    def __init__(self):
        self.fatos_repo = None
    
    def _get_repository(self, db_session):
        """Inicializa repositório com sessão"""
        if not self.fatos_repo:
            self.fatos_repo = FatosRepository(db_session)
    
    def carregar_vendas(self, vendas_data: List[Dict[str, Any]]) -> int:
        """Carrega vendas na DW"""
        carregados = 0
        
        with get_dw_db() as db:
            self._get_repository(db)
            
            for venda_data in vendas_data:
                try:
                    # Verificar se venda já existe (por data e produto)
                    vendas_existentes = self.fatos_repo.get_vendas_by_periodo(
                        venda_data.get('data_venda'),
                        venda_data.get('data_venda')
                    )
                    
                    # Verificar se já existe venda com mesmo produto e data
                    venda_existente = None
                    for venda in vendas_existentes:
                        if (venda.produto_sk == venda_data.get('produto_sk') and
                            venda.data_venda == venda_data.get('data_venda')):
                            venda_existente = venda
                            break
                    
                    if not venda_existente:
                        # Criar nova venda
                        venda = self.fatos_repo.create_venda(venda_data)
                        carregados += 1
                    else:
                        # Atualizar venda existente
                        for key, value in venda_data.items():
                            if hasattr(venda_existente, key):
                                setattr(venda_existente, key, value)
                        db.commit()
                        carregados += 1
                        
                except Exception as e:
                    print(f"Erro ao carregar venda: {e}")
                    continue
        
        return carregados
    
    def carregar_producao(self, producao_data: List[Dict[str, Any]]) -> int:
        """Carrega produção na DW"""
        carregados = 0
        
        with get_dw_db() as db:
            self._get_repository(db)
            
            for producao_item in producao_data:
                try:
                    # Verificar se produção já existe (por data, produto e máquina)
                    producoes_existentes = self.fatos_repo.get_producao_by_periodo(
                        producao_item.get('data_producao'),
                        producao_item.get('data_producao')
                    )
                    
                    # Verificar se já existe produção com mesmo produto, máquina e data
                    producao_existente = None
                    for producao in producoes_existentes:
                        if (producao.produto_sk == producao_item.get('produto_sk') and
                            producao.maquina_sk == producao_item.get('maquina_sk') and
                            producao.data_producao == producao_item.get('data_producao')):
                            producao_existente = producao
                            break
                    
                    if not producao_existente:
                        # Criar nova produção
                        producao = self.fatos_repo.create_producao(producao_item)
                        carregados += 1
                    else:
                        # Atualizar produção existente
                        for key, value in producao_item.items():
                            if hasattr(producao_existente, key):
                                setattr(producao_existente, key, value)
                        db.commit()
                        carregados += 1
                        
                except Exception as e:
                    print(f"Erro ao carregar produção: {e}")
                    continue
        
        return carregados
    
    def carregar_custos(self, custos_data: List[Dict[str, Any]]) -> int:
        """Carrega custos na DW"""
        carregados = 0
        
        with get_dw_db() as db:
            self._get_repository(db)
            
            for custo_data in custos_data:
                try:
                    # Verificar se custo já existe (por data e produto)
                    custos_existentes = self.fatos_repo.get_custos_by_periodo(
                        custo_data.get('data_custo'),
                        custo_data.get('data_custo')
                    )
                    
                    # Verificar se já existe custo com mesmo produto e data
                    custo_existente = None
                    for custo in custos_existentes:
                        if (custo.produto_sk == custo_data.get('produto_sk') and
                            custo.data_custo == custo_data.get('data_custo')):
                            custo_existente = custo
                            break
                    
                    if not custo_existente:
                        # Criar novo custo
                        custo = self.fatos_repo.create_custo(custo_data)
                        carregados += 1
                    else:
                        # Atualizar custo existente
                        for key, value in custo_data.items():
                            if hasattr(custo_existente, key):
                                setattr(custo_existente, key, value)
                        db.commit()
                        carregados += 1
                        
                except Exception as e:
                    print(f"Erro ao carregar custo: {e}")
                    continue
        
        return carregados
    
    def carregar_qualidade(self, qualidade_data: List[Dict[str, Any]]) -> int:
        """Carrega qualidade na DW"""
        carregados = 0
        
        with get_dw_db() as db:
            self._get_repository(db)
            
            for qualidade_item in qualidade_data:
                try:
                    # Verificar se qualidade já existe (por data, produto e máquina)
                    qualidades_existentes = self.fatos_repo.get_qualidade_by_periodo(
                        qualidade_item.get('data_qualidade'),
                        qualidade_item.get('data_qualidade')
                    )
                    
                    # Verificar se já existe qualidade com mesmo produto, máquina e data
                    qualidade_existente = None
                    for qualidade in qualidades_existentes:
                        if (qualidade.produto_sk == qualidade_item.get('produto_sk') and
                            qualidade.maquina_sk == qualidade_item.get('maquina_sk') and
                            qualidade.data_qualidade == qualidade_item.get('data_qualidade')):
                            qualidade_existente = qualidade
                            break
                    
                    if not qualidade_existente:
                        # Criar nova qualidade
                        qualidade = self.fatos_repo.create_qualidade(qualidade_item)
                        carregados += 1
                    else:
                        # Atualizar qualidade existente
                        for key, value in qualidade_item.items():
                            if hasattr(qualidade_existente, key):
                                setattr(qualidade_existente, key, value)
                        db.commit()
                        carregados += 1
                        
                except Exception as e:
                    print(f"Erro ao carregar qualidade: {e}")
                    continue
        
        return carregados
    
    def carregar_energia(self, energia_data: List[Dict[str, Any]]) -> int:
        """Carrega energia na DW"""
        carregados = 0
        
        with get_dw_db() as db:
            self._get_repository(db)
            
            for energia_item in energia_data:
                try:
                    # Verificar se energia já existe (por data e máquina)
                    energias_existentes = self.fatos_repo.get_energia_by_periodo(
                        energia_item.get('data_energia'),
                        energia_item.get('data_energia')
                    )
                    
                    # Verificar se já existe energia com mesma máquina e data
                    energia_existente = None
                    for energia in energias_existentes:
                        if (energia.maquina_sk == energia_item.get('maquina_sk') and
                            energia.data_energia == energia_item.get('data_energia')):
                            energia_existente = energia
                            break
                    
                    if not energia_existente:
                        # Criar nova energia
                        energia = self.fatos_repo.create_energia(energia_item)
                        carregados += 1
                    else:
                        # Atualizar energia existente
                        for key, value in energia_item.items():
                            if hasattr(energia_existente, key):
                                setattr(energia_existente, key, value)
                        db.commit()
                        carregados += 1
                        
                except Exception as e:
                    print(f"Erro ao carregar energia: {e}")
                    continue
        
        return carregados
    
    def carregar_todos_fatos(self, fatos_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, int]:
        """Carrega todos os fatos na DW"""
        resultados = {}
        
        if 'vendas' in fatos_data:
            resultados['vendas'] = self.carregar_vendas(fatos_data['vendas'])
        
        if 'producao' in fatos_data:
            resultados['producao'] = self.carregar_producao(fatos_data['producao'])
        
        if 'custos' in fatos_data:
            resultados['custos'] = self.carregar_custos(fatos_data['custos'])
        
        if 'qualidade' in fatos_data:
            resultados['qualidade'] = self.carregar_qualidade(fatos_data['qualidade'])
        
        if 'energia' in fatos_data:
            resultados['energia'] = self.carregar_energia(fatos_data['energia'])
        
        return resultados
