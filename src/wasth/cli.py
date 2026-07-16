"""Acesso ao CLI do Typer (assistente de preenchimento das fichas)
"""

from typing import Optional
from typing import Annotated
import typer
from pyorcid_checksum import ORCID_Checksum
from rich import print

app = typer.Typer()

def user_orcid(orcid: str) -> str:
    user_orcid = orcid.strip()
    checker = ORCID_Checksum()
    try:
        valida = checker.check_orcid_checksum(user_orcid)
    except Exception as e:
        raise typer.BadParameter(f"❌  Erro de validação: {e}.")
    if valida is False:
        raise typer.BadParameter("❌  ORCiD inválido.")
    return checker.parse_orcid(user_orcid)

@app.command()
def main(
    orcid: Annotated[
        str,
        typer.Option(
            "--orcid",
            prompt="Para começar, digite o seu ORCiD",
            callback=user_orcid,
            help="Seu número do ORCiD.",
        ),
    ]
):
    """
    Esta é a tela de acesso à interfaz de preenchimento das fichas dos
    Documentários de arquitetura tradicional.
    """
    typer.echo(f"ORCiD {orcid} válido.")
    print("""
-------------------------------------------------------
 Interfaz de linha de comando da aplicação
 [bold]WASTH[/bold] : Web App para Sítios Tradicionais e Históricos
-------------------------------------------------------

Para instruções, digitar o comando:
uv run typer src/wasth/app.py run --help
        """)
    print("""
Por ora, não temos funcionalidade nenhuma nesta app.
    """)

if __name__ == "__main__":
    app()
