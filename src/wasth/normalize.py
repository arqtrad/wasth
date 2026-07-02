"""Limpeza na formatação das fichas

Importa e reexporta o conteúdo das fichas para limpar a formatação.
Não valida a estrutura do conteúdo.
"""

from copy import deepcopy
import sys
import os
from pprint import pprint
import frontmatter
from ruamel.yaml import YAML
import pandoc
from wasth.geoprocess import OpenLocation
yaml = YAML(typ='safe')

class NormalizedWork:
    def __init__(self, input_path: str, encoding='utf-8') -> None:
        self.inp = input_path
        self.enc = encoding

    def post(self) -> frontmatter.Post:
        """Processa metadados e faz algumas correções de estrutura"""
        with open(self.inp, 'r', encoding=self.enc) as f:
            post = frontmatter.load(f)

        if post['bibliographicCitation']['citekey']:
            post['bibliographicCitation'] = [ post['bibliographicCitation']['citekey'] ]

        if post['coverage']:
            post['spatial'] = deepcopy(post['coverage']['spatial'])
            post['temporal'] = deepcopy(post['coverage']['temporal'])
            del post['coverage']

        if post['spatial']['location']:
            post['locationHistoric'] = post['spatial']['location']['locationHistoric']
            del post['spatial']['location']['locationHistoric']

            post['tmp'] = {}
            post['tmp']['type'] = 'site'
            post['tmp']['display'] = post['spatial']['location']['name']['text'] + '\n' + post['spatial']['location']['city']
            post['tmp']['term'] = post['spatial']['location']['state']
            del post['spatial']['location']['name']
            del post['spatial']['location']['city']
            del post['spatial']['location']['state']
            del post['spatial']['location']['country']

            post['tmp']['location'] = deepcopy(post['spatial']['location'])
            del post['spatial']['location']
            if post['tmp']['location']['long']:
                post['tmp']['location']['lon'] = post['tmp']['location']['long']
                del post['tmp']['location']['long']


            post['spatial'] = [ deepcopy(post['tmp']) ]
            del post['tmp']

        return post

    def metadata(self, post: frontmatter.Post) -> dict:
        metadata = post['metadata']
        return metadata

    def content(self, post: frontmatter.Post) -> str | None:
        content = post['content']
        ast = pandoc.read(content)
        normalized_content = pandoc.write(ast)
        return normalized_content

    def locations(self, post: frontmatter.Post) -> list[dict[str, str | int | float]]:
        """Valida valores do georreferenciamento:

1. Normaliza root:coverage:spatial para root:spatial
2. Normaliza spatial:location para lista"""
        locations = []
        for place in post['spatial']:
            place_type = place['type']
            lat = place['location']['lat']
            lon = place['location']['lon']
            if not isinstance(lat, (int, float)):
                raise TypeError(f"{lat} não é uma latitude válida")
            elif not isinstance(lon, (int, float)):
                raise TypeError(f"{lon} não é uma longitude válida")
            elif (lat < -90) or (lat > 90):
                raise ValueError(f"Latitude '{lat}' deve ser um número decimal entre -90 e 90")
            elif (lon < -180) or (lon > 180):
                raise ValueError(f"Longitude '{lon}' deve ser um número decimal entre -180 e 180")
            else:
                locations.append({'type': place_type, 'lat': lat, 'lon': lon})
        return locations

    def encode_id(self, post: frontmatter.Post, locations: list[dict[str, str | int | float]]) -> str | None:
        if post.get('id'):
            current_id = post['id']
        else:
            current_id = None
        for location in locations:
            if location['type'] == 'site':
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
Informar um caminho de arquivo/ficheiro de entrada e uma pasta de saída:
(deixar em branco cancela a operação)
""").split()
    if args:
        if os.path.isfile(args[0]):
            input_path = args[0]
        else:
            print("O primeiro argumento não é um arquivo válido.")
            exit(1)
        if not os.path.isfile(args[1]):
            output_path = args[1]
        else:
            print("O segundo argumento não é uma pasta válida.")
            exit(1)
        result = { 'input': input_path, 'outdir': output_path }
        return result
    else:
        print("Operação cancelada")

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

if __name__ == "__main__":
    args = read_write_paths(sys.argv)
    normalized = NormalizedWork(args['input'])
    filename = os.path.basename(args['input'])
    post = normalized.post()
    locations = normalized.locations(post)
    encoded_id = normalized.encode_id(post, locations)
    normalized.write_id(post, encoded_id)
    write_file(post, args['outdir'], filename)
