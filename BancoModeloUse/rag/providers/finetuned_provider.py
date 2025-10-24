"""
Provider para modelo fine-tuned local
"""

from typing import Optional
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from config.logger import get_logger

from .base import LLMClient, Provider, ModelConfig

logger = get_logger(__name__)


class FineTunedClient(LLMClient):
    """Cliente para modelo fine-tuned local"""
    
    def __init__(self, model_path: str, model_name: str, device: str = "auto"):
        self.model_path = model_path
        self.model_name = model_name
        self.device = device
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self):
        """Carrega o modelo fine-tuned"""
        try:
            logger.info(f"Carregando modelo fine-tuned: {self.model_name}")
            logger.info(f"Caminho do modelo: {self.model_path}")
            
            # Carregar tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )
            
            # Carregar modelo
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map=self.device,
                trust_remote_code=True
            )
            
            # Configurar pad_token se necessário
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            logger.info("Modelo fine-tuned carregado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao carregar modelo fine-tuned: {str(e)}")
            raise
    
    def ask(self, system_prompt: str, user_message: str,
            temperature: float, max_tokens: int, tools: list) -> str:
        """
        Executa inferência com modelo fine-tuned
        
        Args:
            system_prompt: Prompt do sistema
            user_message: Mensagem do usuário
            temperature: Temperatura para geração
            max_tokens: Máximo de tokens
            tools: Lista de ferramentas (não usado em modelo local)
            
        Returns:
            Resposta gerada pelo modelo
        """
        try:
            # Montar prompt completo
            full_prompt = f"<s>[INST] {system_prompt}\n\n{user_message} [/INST]"
            
            # Tokenizar
            inputs = self.tokenizer(
                full_prompt,
                return_tensors="pt",
                truncation=True,
                max_length=2048
            )
            
            # Mover para device correto
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # Gerar resposta
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # Decodificar resposta
            response = self.tokenizer.decode(
                outputs[0][inputs['input_ids'].shape[1]:],
                skip_special_tokens=True
            )
            
            logger.debug(f"Resposta gerada: {response[:100]}...")
            return response.strip()
            
        except Exception as e:
            logger.error(f"Erro na inferência do modelo fine-tuned: {str(e)}")
            return f"Erro na geração: {str(e)}"


class FineTunedProvider(Provider):
    """Provider para modelo fine-tuned local"""
    
    provider_name = "finetuned_local"
    
    @classmethod
    def build_client(cls, cfg: ModelConfig) -> LLMClient:
        """
        Constrói cliente para modelo fine-tuned
        
        Args:
            cfg: Configuração do modelo
            
        Returns:
            Cliente fine-tuned configurado
        """
        return FineTunedClient(
            model_path=cfg.model_path,
            model_name=cfg.model_name,
            device=cfg.extra.get("device", "auto")
        )
