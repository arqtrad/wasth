"""Ponto de entrada do WASTH: Web App para Sítios Tradicionais e Históricos

Para rodar este pacote como um programa, ativando a interfaz na linha de
comando contida em wasth.cli:

    python -m wasth --orcid SEU_ORCID [options]
"""

from .cli import main

raise SystemExit(main())
