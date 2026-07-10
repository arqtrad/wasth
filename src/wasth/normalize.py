"""Limpeza na formatação das fichas

Importa e reexporta o conteúdo das fichas para limpar a formatação.
Realiza algumas conversões do esquema DCMI para LIDO.
Valida a estrutura do conteúdo.
"""

from copy import deepcopy
import sys
import os
import frontmatter
from ruamel.yaml import YAML
import yamale
import geojson
from wasth.geoprocess import OpenLocation
yaml = YAML(typ='safe')

class Work(frontmatter.Post):
    """
    Arcabouço dos dados e métodos das fichas de obras

    Validação e correções embutidas.
    """
    def __init__(self, content: str = '', handler=None, **metadata) -> None:
        super().__init__(content=content, handler=handler, **metadata)
        self.normalize()

    @classmethod
    def from_file(cls, f):
        post = frontmatter.load(f)
        return cls(content=post.content, handler=post.handler, **post.metadata)

    def normalize(self):
        """
        Processa metadados e migra DCMI para LIDO:

        - bibliographicCitation de map para lista contendo apenas citekeys
        - root:coverage:spatial para root:spatial
        - root:coverage:temporal para root:temporal
        - spatial:location:locationHistoric para root:locationHistoric
        - spatial:extent de map para lista
        - spatial:location de map para lista
        """
        bibliographicCitation = self.get('bibliographicCitation')
        if isinstance(bibliographicCitation, dict) and bibliographicCitation.get('citekey'):
            self['bibliographicCitation'] = [
                bibliographicCitation.get('citekey')
            ]
        elif isinstance(bibliographicCitation, list):
            citekeys = []
            for citation in bibliographicCitation:
                if isinstance(citation, str) and citation:
                    citekeys.append(citation if citation.startswith('@') else '@' + citation else)
                elif isinstance(citation, dict) and isinstance(citation.get('relids'), str):
                    citekeys.append(citation['relids'] if citation['relids'].startswith('@') else "@" + citation['relids'])
                else:
                    print(f"⚠️  O registro {citation} não contém um campo com chave de citação, ignorando...")
            self['bibliographicCitation'] = citekeys or None
        elif bibliographicCitation is None:
            self['bibliographicCitation'] = None
        else:
            raise ValueError(
                f"📖  {bibliographicCitation} não contém uma chave de citação."
            )

        coverage = self.get('coverage')
        if isinstance(coverage, dict):
            if coverage.get('spatial') is not None and self.get('spatial') is None:
                self['spatial'] = deepcopy(coverage['spatial'])
            if coverage.get('temporal') is not None and self.get('temporal') is None:
                self['temporal'] = deepcopy(coverage['temporal'])
            del self['coverage']

        spatial = self.get('spatial')
        places = []
        if isinstance(spatial, dict):
            location = spatial.get('location', {})
            if location.get('locationHistoric') is not None:
                self['locationHistoric'] = location['locationHistoric']
                del self['spatial']['location']['locationHistoric']

            if location.get('name') is not None:
                location_migration = {}
                location_migration['type'] = 'site'
                location_migration['display'] = self.get('spatial', {}).get('location', {}).get('name', {}).get('text') + '\n' + self.get('spatial', {}).get('location', {}).get('city')
                location_migration['term'] = self.get('spatial', {}).get('location', {}).get('state')
                del self['spatial']['location']['name']
                del self['spatial']['location']['city']
                del self['spatial']['location']['state']
                del self['spatial']['location']['country']
                location_migration['location'] = deepcopy(location)
                if location_migration.get('long') is not None:
                    location_migration['location']['lon'] = location_migration['location']['long']
                    location_migration['location']['lat'] = location_migration['location']['lat']
                    del location_migration['location']['long']
                    del location_migration['location']['lat']
                places.append(location_migration)
                del self['spatial']['location']

            extent = spatial.get('extent', {})
            if isinstance(extent, dict) and extent.get('coordinates') is not None:
                place_footprint = {}
                place_footprint['type'] = 'site'
                place_footprint['extent'] = {}
                place_footprint['extent']['type'] = extent['type']
                place_footprint['extent']['coordinates'] = extent['coordinates']
                if isinstance(extent['projection'], str) and extent['projection'] == 'EPSG:4326 WGS84':
                    place_srsName = {}
                    place_srsName['type'] = 'uri'
                    place_srsName['refid'] = 'http://www.opengis.net/def/crs/EPSG/0/4326'
                    place_srsName['display'] = extent['projection']
                place_footprint['srsName'] = place_srsName
                if extent.get('source') is not None:
                    place_footprint['source'] = {}
                    place_footprint['source']['display'] = extent['source']
                    place_footprint['source']['type'] = 'corporate'
                places.append(place_footprint)
                del self['spatial']['extent']

                if extent['type'] == 'Polygon':
                    fp_geom = geojson.Polygon(extent['coordinates'])
                elif extent['type'] == 'MultiPolygon':
                    fp_geom = geojson.MultiPolygon(extent['coordinates'])
                footprint = geojson.Feature(geometry=fp_geom, properties=fp_props)

    def places(self) -> geojson.FeatureCollection | None:
        """Valida valores do georreferenciamento"""
        if post.get('spatial'):
            locations = []
        else:
            raise ValueError("🌐❌  A obra não está georreferenciada.")
        for place in post['spatial']:
            place_type = place['type']
            lat = place['location']['lat']
            lon = place['location']['lon']
            location = geojson.Feature(geometry=geojson.Point((lon, lat)), properties={'type': place_type})
            if location.is_valid:
                locations.append(location)
            else:
                raise ValueError(f"🌐❌  Dados de georreferenciamento inválidos: {location.errors()}")
        places = geojson.FeatureCollection(locations)
        return places

    def encode_id(self, post: frontmatter.Post, locations: geojson.FeatureCollection) -> str | None:
        if post.get('id'):
            current_id = post['id']
        else:
            current_id = None
        for location in locations:
            if location['properties']['type'] == 'site':
                lat = location['lat']
                lon = location['lon']
                open_location = OpenLocation(current_id, lat, lon)
                id = open_location.encode()
                return id
        return None

    def write_id(self, post: frontmatter.Post, encode_id: str | None) -> None:
        if isinstance(encode_id, str):
            if encode_id != post.get('id'):
                post['id'] = encode_id

def read_write_paths(input) -> dict | None:
    if len(input) == 3:
        args = input[1:]
    else:
        args = input("""
Informar um caminho de arquivo/ficheiro ou pasta de leitura
e uma pasta de saída:
(deixar em branco cancela a operação)
""").split()
    if args:
        if os.path.isfile(args[0]):
            filelist = [ args[0] ]
        elif os.path.isdir(args[0]):
            filelist = [
                os.path.join(args[0], f) for f in os.listdir(args[0])
                if os.path.isfile(os.path.join(args[0], f))
            ]
        else:
            print("O primeiro argumento não é válido.")
            exit(1)
        if not os.path.isfile(args[1]):
            output_path = args[1]
        else:
            print("O segundo argumento não é uma pasta válida.")
            exit(1)
        result = { 'input': filelist, 'outdir': output_path }
    else:
        print("Operação cancelada")
    return result

def write_file(post, dir, filename):
    try:
        os.makedirs(dir)
        print(f"📁  Pasta '{dir}' criada com sucesso.")
        dest = os.path.join(dir, filename)
    except FileExistsError:
        print(f"📁  Pasta '{dir}' já existe.")
        dest = os.path.join(dir, filename)
    except PermissionError:
        print(f"❌  Não foi possível criar a pasta '{dir}': sem permissões.")
    except Exception as e:
        print(f"❌  Erro na criação da pasta: {e}")
    try:
        frontmatter.dump(post, dest, sort_keys=False)
        print(f"📄  Arquivo '{dest}' gravado com sucesso.")
    except Exception as e:
        print(f"❌  Erro na escrita do arquivo '{dest}': {e}")

def main(args: dict[list, str] | None = None) -> int:
    if args is None:
        args = sys.argv
    files = read_write_paths(args)
    output_dir = files['outdir']
    for file in files['input']:
        normalized = Work(file)
        filename = os.path.basename(file)
        post = normalized.post()
        locations = normalized.locations(post)
        encoded_id = normalized.encode_id(post, locations)
        normalized.write_id(post, encoded_id)
        write_file(post, output_dir, filename)

if __name__ == "__main__":
    raise SystemExit(main())
