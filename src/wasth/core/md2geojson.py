"""Converte fichas em Markdown+YAML para geoJSON

Usa frontmatter para extrair metadados.
Não temos previsão de implementar o caminho inverso
(geoJSON para fichas em Markdown+YAML).
"""

import sys
import os
import geojson
from rich import print
import wasth

def filelist(input) -> list | None:
    """
    Gera uma lista de arquivos a serem processados a partir da entrada
    do usuário na forma de um caminho relativo de pasta ou de nome(s) de
    arquivos/ficheiros separados por espaços.
    """
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
            return filelist
        if os.path.isfile(args[0]):
            filelist = args
            return filelist
        return None
    else:
        print("Operação cancelada")
        return None

def make_feature(post: wasth.Work) -> geojson.Feature | None:
    """
    Gera um geojson.Feature a partir dos metadados de georreferenciamento
    da ficha de obra.
    """
    props = {
        'id': post.get('id'),
        'name': post.get('title'),
        'teaser': post.get('header', {}).get('teaser'),
    }
    for place in post.get('spatial', []):
        if place.get('type') == 'site':
            location = place.get('location', {})
            lon = location.get('lon')
            lat = location.get('lat')
            alt = location.get('alt')
            if lon is not None and lat is not None and alt is None:
                point = geojson.Point((lon, lat))
                feature = geojson.Feature(geometry=point, properties=props)
                return feature
            if lon is not None and lat is not None and alt is not None:
                point = geojson.Point((lon, lat, alt))
                feature = geojson.Feature(geometry=point, properties=props)
                return feature
            return None
        return None
    return None

def collect_features(
        features: list[geojson.Feature]
) -> geojson.FeatureCollection | None:
    """
    Gera uma coleção de objetos geoJSON a partir dos objetos ingeridos.
    """
    collection = geojson.FeatureCollection(features)
    return collection

def f_write(
    collection: geojson.FeatureCollection | None,
    filename: str,
    directory: str = '.',
    enc: str = 'utf-8',
) -> None:
    """
    Escreve a coleção geojson.FeatureCollection para um arquivo/ficheiro.
    """
    try:
        os.makedirs(directory, exist_ok=True)
        print(f"📁  Pasta '{directory}' criada com sucesso.")
    except FileExistsError:
        print(f"📁  Pasta '{directory}' já existe.")
    except PermissionError:
        print(f":x:  Não foi possível criar a pasta '{directory}': sem permissões.")
    except Exception as e:
        print(f":x:  Erro na criação da pasta: {e}")
    dest = os.path.join(directory, filename)
    try:
        with open(dest, 'w', encoding=enc) as f:
            geojson.dump(collection, f)
        print(f"📄  Arquivo '{dest}' gravado com sucesso.")
    except Exception as e:
        print(f":x:  Erro na escrita do arquivo '{dest}': {e}")

def main(args: list[str] | None = None) -> None:
    """
    Recebe um ou mais arquivos/ficheiros ou um nome de pasta,
    grava um documento .geojson.
    """
    if args is None:
        args = sys.argv
    files = filelist(args)
    features = []
    for f in files:
        post = wasth.Work(f)
        feature = make_feature(post)
        valid_geojson = feature.valid_geojson(feature)
        features.append(valid_geojson)
    collection = collect_features(features)
    f_write(collection)

if __name__ == "__main__":
    raise SystemExit(main())
