"""Módulo de validação do YAML: roda antes e depois de editar

Verifica se o arquivo/ficheiro existe, e se a sua sintaxe é válida.
"""

import sys
import os
import frontmatter
from pprint import pprint
from ruamel.yaml import YAML
yaml = YAML(typ='safe')
# import datetime
# import json
# import jq
# import yq
# import pandas as pd
# import geopandas as gpd

def f_read(f, mode='r', enc="utf-8") -> dict:
    """Lê o arquivo/ficheiro se ele não estiver vazio"""
    with open(f, 'r', encoding=enc) as f:
        contents = f.read().split('\n---\n\n', 2)
        metadata = contents[0] + '\n'
        body = contents[1].lstrip() or ''
        document = {
            'metadata': metadata.lstrip(),
            'body': body
        }
    return document

def f_load(f, mode='r', enc="utf-8") -> frontmatter.Post:
    """Carrega metadados em forma de dicionário com python-frontmatter"""
    with open(f, 'r', encoding=enc) as f:
        post = frontmatter.load(f)
    return post

def prt_title(f) -> str:
    post = f_load(f)
    return post['title']

def f_lint(f) -> list:
    """Mostra os problemas de formatação"""
    metadata = f_read(f)['metadata']
    title = prt_title(f)
    print(f"""
-------------------------------------------------------------------------------
{title.upper():^79s}

📄 {f}
    """)
    import yamllint.config
    import yamllint.linter
    yaml_config = yamllint.config.YamlLintConfig("extends: relaxed")
    yaml_lint = yamllint.linter.run(metadata, yaml_config)
    yaml_lint_list = []
    for p in yaml_lint:
        yaml_lint_list.append(p)
        match p.level:
            case "error":
                p_level = "❌ "
            case "warning":
                p_level = "⚠️"
            case _:
                p_level = p.level
        print(
            p_level,
            f"{p.line:>4}{':'}{p.column:>2}",
            f"{p.desc:<40}",
            f"{'['}{p.rule}{']'}"
        )
    return yaml_lint_list

if __name__ == "__main__":
    if len(sys.argv) > 1:
        args = sys.argv[1:]
    else:
        args = input("""
Informar um caminho relativo de pasta ou nomes de arquivos/ficheiros:
(deixar em branco cancela a operação)
""").split()
    if args:
        if os.path.isdir(args[0]):
            filelist = [
                os.path.join(args[0], f) for f in os.listdir(args[0])
                if os.path.isfile(os.path.join(args[0], f))
            ]
        elif os.path.isfile(args[0]):
            filelist = args
        for file in filelist:
            try:
                f_lint(file)
            except Exception as e:
                print(f"""
-------------------------------------------------------------------------------

🚫 Não foi possível ler {file}:""")
                print('  ' + str(e))
    else:
        print("Operação cancelada")
