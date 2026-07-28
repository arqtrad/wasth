"""Modelos de objeto usados no WASTH, especialmente a ficha de obra"""

import os
import sys
from pathlib import Path
from typing import TypedDict

import frontmatter
import geojson
import yamale
from openlocationcode import openlocationcode
from rich import print
from ruamel.yaml import YAML

yaml = YAML(typ='safe')

class Obra(frontmatter.Post):
    """
    Arcabouço dos dados e métodos das fichas de obras.
    """
    def __init__(self, content: str = '', handler=None, **metadata) -> None:
        super().__init__(content=content, handler=handler, **metadata)

    @classmethod
    def from_file(cls, f) -> "Obra":
        """Gera o objeto a partir de um arquivo/ficheiro."""
        post = frontmatter.load(f)
        return cls(content=post.content, handler=post.handler, **post.metadata)

    @classmethod
    def from_post(cls, post: frontmatter.Post) -> "Obra":
        """Gera o objeto a partir de um objeto frontmatter.Post"""
        return cls(content=post.content, handler=post.handler, **post.metadata)

    def places(self) -> geojson.FeatureCollection | None:
        """Cria geoJSON a partir de 'spatial'"""
        spatial = self.get('spatial')
        if not spatial:
            raise ValueError(
                ":globe_with_meridians::w:  A obra não está georreferenciada."
            )
        places = []
        for place in spatial:
            props = {
                'type': place.get('type') or 'site',
            }
            if place.get('display'):
                props['display'] = place['display']
            if place.get('zoom'):
                props['zoom'] = place['zoom']
            if place.get('location'):
                location = place.get('location')
                lat = location.get('lat')
                lon = location.get('lon')
                alt = location.get('alt')
                if lat is None or lon is None:
                    raise ValueError(
                ":globe_with_meridians::x:  Latitude e/ou longitude ausentes."
                    )
                if alt is not None:
                    geom = geojson.Point((lon, lat, alt))
                else:
                    geom = geojson.Point((lon, lat))
            elif place.get('extent'):
                extent = place['extent']
                coords = extent.get('coordinates')
                geom_type = extent.get('type') or 'Polygon'
                if geom_type == 'Polygon':
                    geom = geojson.Polygon(coords)
                elif geom_type == 'MultiPolygon':
                    geom = geojson.MultiPolygon(coords)
                else:
                    raise ValueError(
f":globe_with_meridians::x:  {geom_type} não é um tipo de geometria válido."
                                     )
            else:
                raise ValueError(
":globe_with_meridians::x:  Dados de georreferenciamento inexistentes."
                                 )
            feature = geojson.Feature(geometry=geom, properties=props)
            if feature.is_valid:
                places.append(feature)
            else:
                raise ValueError(f"""
:globe_with_meridians::x:  Dados de georreferenciamento inválidos:
{feature.errors()}
                    """)
        return geojson.FeatureCollection(places)

    def olc_id(self) -> str | None:
        """
        Processa entradas de georreferenciamento

        Gera ID no formato Open Location Code a partir da latitude e longitude
        inseridas na ficha ou na interface.
        """
        spatial = self.get('spatial', [])
        if spatial is None:
            return None
        for place in spatial:
            if place.get('type') != "site":
                continue
            location = place.get('location')
            if not location:
                continue
            lat = location.get('lat')
            lon = location.get('lon')
            if lat is None or lon is None:
                continue
            return openlocationcode.encode(lat, lon, 11)

    def valida(
        self,
        schema_file: str = "data/schema.yaml",
        parser: str = "ruamel",
        encoding: str = 'utf-8'
    ) -> None:
        """Valida os dados do objeto contra o esquema usando Yamale"""
        root_dir = Path(__file__).resolve().parent.parent
        schema_path = os.path.join(root_dir, schema_file)
        with open(schema_path, 'r', encoding=encoding) as f:
            schema = f.read()
        schema = yamale.make_schema(content=schema, parser=parser)
        content = yaml.dump(self.metadata)
        data = yamale.make_data(content=content, parser=parser)
        yamale.validate(schema, data)

class GeoFeatures(geojson.FeatureCollection):
    pass

class Lugar(Obra):
    """
    Define a ficha de lugares como variante da ficha de obra e fornece
    os métodos adicionais:

    - Gera ou atualiza a partir da base cartográfica do IBGE;
    - Gera ou atualiza a partir da toponímia de Portugal continental do DGT.
    """
    @classmethod
    def from_geojson_ibge_bc(cls, feature: geojson.Feature) -> "Lugar":
        "Gera fichas a partir de geojson.Feature"
        pass

class InOutPaths(TypedDict):
    filelist: list[str]
    output_dir: str

def paths(
    args: list[str] | None = None,
    overwrite: bool | None = None
) -> InOutPaths | None:
    """Gera os nomes de arquivos de entrada e a pasta de saída.

    Primeiro argumento: caminho de entrada (arquivo/ficheiro ou pasta)
    Segundo argumento: caminho de saída (pasta), opcional;
    se for deixado em branco sobrescreve o existente.
    """
    if not args:
        if 2 <= len(sys.argv) <= 3:
            args = sys.argv[1:]
        else:
            args = input("""
Informar um caminho de arquivo/ficheiro ou pasta de leitura
e opcionalmente uma pasta de gravação.
Omitir a pasta de gravação sobrescreve os arquivos/ficheiros existentes.
                """).strip().split()
    if not args:
        print("Operação cancelada.")
        return None
    source = args[0]
    if len(args) == 1:
        if overwrite is None:
            prompt = input(
                ":warning:  Sobrescrever arquivos/ficheiros existentes? s/n"
            ).strip().lower()
            overwrite = prompt in { "s", "sim", "y", "yes", "sobrescrever" }
        if overwrite is False:
            print("Operação cancelada.")
            return None
    if len(args) > 2:
        raise OSError("Número excessivo de argumentos.")
    if len(args) == 2 and Path(args[1]).is_file():
        raise OSError("O segundo argumento deve ser uma pasta ou ser omitido.")
    if Path(source).is_dir():
        filelist = [
            Path(source).joinpath(f)
            for f in Path(source).iterdir()
            if Path(source).joinpath(f).is_file()
        ]
        output_dir = Path(args[1]) if len(args) == 2 else source
        return { 'filelist': filelist, 'output_dir': output_dir }
    output_dir = args[1] if len(args) == 2\
        else Path(source).resolve().parent
    return { 'filelist': [source], 'output_dir': output_dir}

def write_file(
        post: frontmatter.Post | Obra | Lugar,
        output_dir: Path,
        filename: Path
) -> Path | None:
    """Grava cada arquivo/ficheiro conforme nome e pasta recebidos."""
    try:
        output_dir.mkdir(exist_ok=True, parents=True)
        dest = Path(output_dir) / Path(filename)
        frontmatter.dump(post, dest, sort_keys=False)
        print(f"""
:card_index:  {post.get('id')} --- [bold]{post.get('title')}[/bold]
   gravado em '{str(dest)}'
        """)
        return dest
    except Exception as e:
        raise OSError(f"""
:x:  Erro na escrita em '{str(output_dir)}/{str(filename)}':\n {e}
        """) from e
