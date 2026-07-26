"""Converte fichas em Markdown+YAML para geoJSON

Usa frontmatter para extrair metadados.
Não temos previsão de implementar o caminho inverso
(geoJSON para fichas em Markdown+YAML).
"""

import os
from pathlib import Path

import geojson
from rich import print

from wasth.core import models


def collect_features(
        features: list[geojson.Feature]
) -> geojson.FeatureCollection | None:
    """
    Gera uma coleção de objetos geoJSON a partir dos objetos ingeridos.
    """
    collection = geojson.FeatureCollection(features)
    return collection

def f_write(
    collection: geojson.FeatureCollection,
    output_file: str,
    encoding: str = 'utf-8',
) -> None:
    """
    Escreve a coleção geojson.FeatureCollection para um arquivo/ficheiro.
    """
    try:
        directory = Path(output_file).resolve().parent
        os.makedirs(directory, exist_ok=True)
        with open(output_file, 'w', encoding=encoding) as f:
            geojson.dump(collection, f)
        print(f":page_facing_up:  Arquivo '{output_file}' gravado com sucesso.")
    except Exception as e:
        print(f":x:  Erro na escrita do arquivo '{output_file}': {e}")

def main(
    args: models.InOutPaths | None = None,
    ignore_output_dir: bool | None = None,
    encoding: str = 'utf-8'
) -> None:
    """
    Recebe um ou mais arquivos/ficheiros ou um nome de pasta,
    grava um documento .geojson.
    """
    args = models.paths(overwrite=ignore_output_dir)
    if not args:
        return None
    files = args['filelist']
    features = []
    for f in files:
        work = models.Work.from_file(f)
        places = work.places()
        for place in places['features']:
            if isinstance(place, geojson.Point) and\
                place['properties']['type'] == 'site':
                features.append(place)
                break
    collection = collect_features(features)
    output_filename = input("""
    Escolha um nome de arquivo para gravar, por padrão 'wasth.geojson':
    """).strip() or 'wasth.geojson'
    output_file = os.path.join(args['output_dir'], output_filename)
    f_write(collection, output_file=output_file, encoding=encoding)

if __name__ == "__main__":
    raise SystemExit(main())
