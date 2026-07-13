"""Converte fichas em Markdown+YAML para geoJSON

Usa frontmatter para extrair metadados.
Não temos previsão de implementar o caminho inverso
(geoJSON para fichas em Markdown+YAML).
"""

import sys
import os
import geojson
import geopandas as gpd
import wasth.normalize as norm

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

def make_feature(post: norm.Work) -> geojson.Feature:
    for place in post.get('spatial', []):
        if place.get('type') == 'site':
            lon = place.get('location', {}).get('lon')
            lat = place.get('location', {}).get('lat')
            break
    if lon is not None and lat is not None:
        point = geojson.Point((lon, lat))
    props = {
        'id': post.get('id'),
        'name': post.get('title'),
        'teaser': post.get('header', {}).get('teaser'),
    }
    feature = geojson.Feature(geometry=point, properties=props)
    return feature

def collect_features(features: list[geojson.Feature]) -> geojson.FeatureCollection | None:
    collection = geojson.FeatureCollection(features)
    return collection

def f_write(collection: geojson.FeatureCollection | None, dir, filename) -> None:
    try:
        os.makedirs(dir)
        print(f"📁  Pasta '{dir}' criada com sucesso.")
        dest = os.path.join(dir, filename)
    except FileExistsError:
        print(f"📁  Pasta '{dir}' já existe.")
    except PermissionError:
        print(f"❌  Não foi possível criar a pasta '{dir}': sem permissões.")
    except Exception as e:
        print(f"❌  Erro na criação da pasta: {e}")
    try:
        with open(dest, 'w') as f:
            geojson.dump(collection, f)
        print(f"📄  Arquivo '{dest}' gravado com sucesso.")
    except Exception as e:
        print(f"❌  Erro na escrita do arquivo '{dest}': {e}")

def main(args: list[str] | None = None) -> int:
    if args is None:
        args = sys.argv
    files = filelist(args)
    features = []
    for f in files:
        post = norm.Work(f)
        feature = make_feature(post)
        valid_geojson = feature.valid_geojson(feature)
        features.append(valid_geojson)
    collection = collect_features(features)
    f_write(collection, sort_keys=True)

if __name__ == "__main__":
    raise SystemExit(main())
