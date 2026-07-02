"""Converte fichas em Markdown+YAML para geoJSON

Usa frontmatter para extrair metadados.
"""

import sys
import os
import frontmatter
import json
import geopandas as gpd
import wasth.normalize

def filelist(input) -> list | None:
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
    else:
        print("Operação cancelada")
    return filelist

def frontmatter(file, enc='utf-8') -> dict:
    with open(file, 'r', encoding=enc) as f:
        post = frontmatter.load(f)
    return post['metadata']

def md2geojson(dict) -> dict:
    pass

def f_write(dict) -> None:
    pass

def main(args: list[str] | None = None) -> int:
    if args is None:
        args = sys.argv
    files = filelist(args)
    posts = []
    for f in files:
        posts.append(frontmatter(f))
    f_write(md2geojson(posts))

if __name__ == "__main__":
    raise SystemExit(main())
