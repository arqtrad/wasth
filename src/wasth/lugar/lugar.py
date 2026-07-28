"""Operações com as fichas de lugares

Cria e edita fichas de lugares.
"""
from pathlib import Path

import geojson
from rich import print

from wasth.core import models


def extract_feature(collection: geojson.FeatureCollection) -> list | None:
    features = []
    if not isinstance(collection, geojson.FeatureCollection) or not collection[0]:
        return None
    for feature in collection['features']:
        features.append(feature)
    return features

def lugar_from_ibge_bc(
        features: geojson.FeatureCollection | None
) -> list[models.Lugar] | None:
    lugares = []
    if not features:
        return None
    for feature in features:
        try:
            lugar = models.Lugar.from_geojson_ibge_bc(feature)
            lugares.append(lugar)
        except Exception as e:
            raise Exception(f"""
===============================================================================
:x: Erro ao converter geojson.Feature:
   {feature}
   ----------------------------------------------------------------------------
   {e}
   ----------------------------------------------------------------------------
===============================================================================
            """) from e
    return lugares

def main(args: models.InOutPaths | None = None) -> list | None:
    """Compila todos os arquivos/ficheiros a serem gravados."""
    if args is None:
        args = models.paths()
        if args is None:
            return None
    files = []
    raw_files = sorted(args['filelist'])
    for f in raw_files:
        if Path(f).suffix == ".geojson":
            files.append(f)
    output_dir = args['output_dir']
    if len(files) == 0:
        print("Nenhum dado geoJSON encontrado.")
        return None
    try:
        out_path = Path(output_dir)
        out_path.mkdir(exist_ok=True, parents=True)
        print(f":open_file_folder:  Pasta '{output_dir}' criada com sucesso.")
    except PermissionError as e:
        raise PermissionError(f"""
:x:  Não foi possível criar a pasta '{output_dir}': sem permissões.
        """) from e
    except Exception as e:
        raise OSError(f":x:  Erro na criação da pasta: {e}") from e
    pass

if __name__ == "__main__":
    raise SystemExit(main())
