"""WASTH: Web App para Sítios Tradicionais e Históricos"""

__version__ = "0.2.0"

from .normalize import NormalizedWork
from .valida_yaml import ValidaYAML

__all__ = ["NormalizedWork", "ValidaYAML"]
