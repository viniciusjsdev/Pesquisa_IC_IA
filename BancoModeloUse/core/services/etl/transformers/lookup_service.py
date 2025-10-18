# core/services/etl/transformers/lookup_service.py
"""
Serviço de lookup para buscar surrogate keys
"""
from typing import Optional, Dict, Any
from infrastructure.database.sessions import get_dw_db
from core.repositories.dw import DimensoesRepository

class LookupService:
    """Serviço para buscar surrogate keys das dimensões"""
    
    def __init__(self):
        self.dimensoes_repo = None
        self.cache = {}
    
    def _get_repository(self, db_session):
        """Inicializa repositório com sessão"""
        if not self.dimensoes_repo:
            self.dimensoes_repo = DimensoesRepository(db_session)
    
    def buscar_produto_sk(self, produto_id: int, tipo_sistema: str) -> Optional[int]:
        """Busca surrogate key do produto"""
        cache_key = f"produto_{tipo_sistema}_{produto_id}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        with get_dw_db() as db:
            self._get_repository(db)
            
            if tipo_sistema == 'financeiro':
                produto = self.dimensoes_repo.get_produto_by_financeiro_id(produto_id)
            elif tipo_sistema == 'industrial':
                produto = self.dimensoes_repo.get_produto_by_industrial_id(produto_id)
            else:
                return None
            
            if produto:
                sk = produto.produto_sk
                self.cache[cache_key] = sk
                return sk
        
        return None
    
    def buscar_tempo_sk(self, data) -> Optional[int]:
        """Busca surrogate key do tempo"""
        if not data:
            return None
        
        cache_key = f"tempo_{data}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        with get_dw_db() as db:
            self._get_repository(db)
            tempo = self.dimensoes_repo.get_tempo_by_data(data)
            
            if tempo:
                sk = tempo.tempo_sk
                self.cache[cache_key] = sk
                return sk
        
        return None
    
    def buscar_maquina_sk(self, maquina_id: int) -> Optional[int]:
        """Busca surrogate key da máquina"""
        cache_key = f"maquina_{maquina_id}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        with get_dw_db() as db:
            self._get_repository(db)
            maquina = self.dimensoes_repo.get_maquina_by_industrial_id(maquina_id)
            
            if maquina:
                sk = maquina.maquina_sk
                self.cache[cache_key] = sk
                return sk
        
        return None
    
    def buscar_cliente_sk(self, cliente_id: int) -> Optional[int]:
        """Busca surrogate key do cliente"""
        cache_key = f"cliente_{cliente_id}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        with get_dw_db() as db:
            self._get_repository(db)
            cliente = self.dimensoes_repo.get_cliente_by_financeiro_id(cliente_id)
            
            if cliente:
                sk = cliente.cliente_sk
                self.cache[cache_key] = sk
                return sk
        
        return None
    
    def buscar_fornecedor_sk(self, fornecedor_id: int) -> Optional[int]:
        """Busca surrogate key do fornecedor"""
        cache_key = f"fornecedor_{fornecedor_id}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        with get_dw_db() as db:
            self._get_repository(db)
            fornecedor = self.dimensoes_repo.get_fornecedor_by_industrial_id(fornecedor_id)
            
            if fornecedor:
                sk = fornecedor.fornecedor_sk
                self.cache[cache_key] = sk
                return sk
        
        return None
    
    def limpar_cache(self):
        """Limpa o cache de lookup"""
        self.cache.clear()
    
    def obter_estatisticas_cache(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        return {
            'total_entradas': len(self.cache),
            'chaves': list(self.cache.keys())
        }
