"""
Provider para OpenAI API
"""

from openai import OpenAI
from config.logger import get_logger

from .base import LLMClient, Provider, ModelConfig

logger = get_logger(__name__)


class OpenAIClient(LLMClient):
    """Cliente para OpenAI API"""
    
    def __init__(self, api_key: str, model_name: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url
        
        # Inicializar cliente OpenAI
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        logger.info(f"Cliente OpenAI inicializado para modelo: {self.model_name}")
    
    def ask(self, system_prompt: str, user_message: str,
            temperature: float, max_tokens: int, tools: list) -> str:
        """
        Executa consulta via OpenAI API
        
        Args:
            system_prompt: Prompt do sistema
            user_message: Mensagem do usuário
            temperature: Temperatura para geração
            max_tokens: Máximo de tokens
            tools: Lista de ferramentas (não usado em API)
            
        Returns:
            Resposta da API
        """
        try:
            # Preparar mensagens
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Fazer chamada à API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            
            # Extrair resposta
            answer = response.choices[0].message.content
            
            logger.debug(f"Resposta OpenAI: {answer[:100]}...")
            return answer.strip()
            
        except Exception as e:
            logger.error(f"Erro na chamada OpenAI API: {str(e)}")
            return f"Erro na API: {str(e)}"


class OpenAIProvider(Provider):
    """Provider para OpenAI API"""
    
    provider_name = "openai"
    
    @classmethod
    def build_client(cls, cfg: ModelConfig) -> LLMClient:
        """
        Constrói cliente OpenAI
        
        Args:
            cfg: Configuração do modelo
            
        Returns:
            Cliente OpenAI configurado
        """
        return OpenAIClient(
            api_key=cfg.api_key,
            model_name=cfg.model_name,
            base_url=cfg.base_url
        )
