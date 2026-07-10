"""WASTH: Web App para Sítios Tradicionais e Históricos"""

__version__ = "0.2.0"

from .normalize import Work
from .valida_yaml import valida_yaml

__all__ = ["Work", "valida_yaml"]
