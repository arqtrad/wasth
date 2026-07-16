"""WASTH: Web App para Sítios Tradicionais e Históricos"""

__version__ = "0.2.1"

__all__ = ["Work", "f_valida"]

from .core.models import Work
from .core.valida_yaml import f_valida
