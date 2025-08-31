#Scripts/factory.py

from .strategies.interface import RaspagemStrategy
from .strategies.raiaDrogasil import RaiaDrogasilStrategy
from .strategies.magalu import MagaluStrategy
from .strategies.gpa import GPAStrategy
from .strategies.casas_bahia import CasasBahiaStrategy
from .strategies.raiaDrogasil import RaiaDrogasilStrategy
from .strategies.americanas import AmericanasStrategy
from .strategies.pagueMenos import PagueMenosStrategy
from .strategies.pernambucanas import PernambucanasStrategy
from .strategies.gerdau import GerdauStrategy

class StrategyFactory:
    _estrategias = {
        "MAGALU": MagaluStrategy,
        "GPA": GPAStrategy,
        "CasasBahia": CasasBahiaStrategy,
        "RaiaDrogasil": RaiaDrogasilStrategy,
        "AmericanasSA": AmericanasStrategy,
        "PagueMenos": PagueMenosStrategy,
        "Pernambucanas": PernambucanasStrategy,
        "Gerdau": GerdauStrategy
    }

    @staticmethod
    def get_strategy(empresa: str) -> RaspagemStrategy:
        if empresa not in StrategyFactory._estrategias:
            raise ValueError(f"Estratégia para a empresa '{empresa}' não está implementada.")
        return StrategyFactory._estrategias[empresa]()

    @staticmethod
    def listar_empresas():
        return list(StrategyFactory._estrategias.keys())