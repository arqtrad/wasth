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
        - spatial:locationHistoric para root:locationHistoric
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
        if isinstance(spatial, dict):
            extent = spatial.get('extent', {})
            if isinstance(extent, dict) and extent.get('type') is not None:
                fp_props = {}
                if extent['type'] == 'Polygon':
                    fp_geom = geojson.Polygon(extent['coordinates'])
                elif extent['type'] == 'MultiPolygon':
                    fp_geom = geojson.MultiPolygon(extent['coordinates'])
                if isinstance(extent['projection'], str) and extent['projection'] == 'EPSG:4326 WGS84':
                    fp_props['srsName'] = {}
                    fp_props['srsName']['type'] = 'uri'
                    fp_props['srsName']['refid'] = 'http://www.opengis.net/def/crs/EPSG/0/4326'
                    fp_props['srsName']['display'] = extent['projection']
                footprint = geojson.Feature(geometry=fp_geom, properties=fp_props)

            location = spatial.get('location', {})
            if location.get('locationHistoric') is not None:
                self['locationHistoric'] = location['locationHistoric']
                del self['spatial']['location']['locationHistoric']

            if location.get('name') is not None:
                self['tmp'] = {}
                self['tmp']['type'] = 'site'
                self['tmp']['display'] = self.get('spatial', {}).get('location', {}).get('name', {}).get('text') + '\n' + self.get('spatial', {}).get('location', {}).get('city')
                self['tmp']['term'] = self.get('spatial', {}).get('location', {}).get('state')
                del self['spatial']['location']['name']
                del self['spatial']['location']['city']
                del self['spatial']['location']['state']
                del self['spatial']['location']['country']

                self['tmp']['location'] = deepcopy(self.get('spatial', {}).get('location'))
                del self['spatial']['location']
                if self.get('tmp', {}).get('location', {}).get('long') is not None:
                    self['tmp']['location']['lon'] = self['tmp']['location']['long']
                    self['tmp']['location']['lat'] = self['tmp']['location']['lat']
                    del self['tmp']['location']['long']
                    del self['tmp']['location']['lat']

                self['spatial'] = [ deepcopy(self['tmp']) ]
                del self['tmp']

    def locations(self) -> geojson.FeatureCollection | None:
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
        features = geojson.FeatureCollection(locations)
        return features

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
