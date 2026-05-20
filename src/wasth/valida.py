"""
Módulo de validação: roda antes e depois de editar

Verifica se o arquivo/ficheiro existe, e se a sua sintaxe é válida.
"""

import sys
import os
from pprint import pprint
from ruamel.yaml import YAML
yaml = YAML(typ='safe')
# import datetime
# import json
# import jq
# import yq
# import pandas as pd
# import geopandas as gpd

def f_read(f, mode='r', enc="utf-8") -> None:
    with open(f, 'r', encoding=enc) as f:
        read_data = f.read()
        return read_data

def prt_title(f) -> str:
    """
    TODO: lidar com arquivos markdown que têm conteúdo após o bloco YAML
    """
    data = yaml.load(str(f_read(f)))
    return data['title']

def f_lint(f) -> None:
    """Mostra os problemas de formatação"""
    import yamllint.config
    import yamllint.linter
    yaml_config = yamllint.config.YamlLintConfig("extends: relaxed")
    yaml_lint = yamllint.linter.run(open(f, "r"), yaml_config)
    if yaml_lint == 0:
        print("Nenhum problema detetado no arquivo/ficheiro.\n")
    elif yaml_lint == 1:
        print("Erros de formatação detetados.\n")
    elif yaml_lint == 2:
        print("Nenhum erro detetado, mas inconsistências de formatação.\n")
    print(
        "--------------------------------------------------------------------",
        "\n",
        prt_title(f),
        "\n"
    )
    for p in yaml_lint:
        if p.level == "error":
            p_level = "❌ "
        elif p.level == "warning":
            p_level = "⚠️"
        else:
            p_level = p.level
        print(
            p_level,
            f"{p.line:>4}{':'}",
            f"{p.desc:<40}",
            f"{'['}{p.rule}{']'}"
        )

if __name__ == "__main__":
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if os.path.isfile(arg):
                f_lint(arg)
    else:
        print("Informar nome(s) de arquivo/ficheiro")
