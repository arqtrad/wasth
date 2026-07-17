"""Limpeza na formatação das fichas

Importa e reexporta o conteúdo das fichas para limpar a formatação.
Realiza algumas conversões do esquema DCMI para LIDO.
Valida a estrutura do conteúdo.
"""

from copy import deepcopy
from pathlib import Path
import os
import sys
import frontmatter
from rich import print
from ruamel.yaml import YAML
yaml = YAML(typ='safe')

def normalize(post: frontmatter.Post) -> frontmatter.Post:
    """
    Processa metadados e migra DCMI para LIDO:

    - bibliographicCitation de map para lista contendo apenas citekeys
    - root:coverage:spatial para root:spatial
    - root:coverage:temporal para root:temporal
    - spatial:location:locationHistoric para root:location_historic
    - spatial:extent de map para lista
    - spatial:location de map para lista
    - format:extent e spatial:extent normalizados para format:extent (lista)
    """
    bibliographic_citation = post.get('bibliographicCitation')
    if isinstance(bibliographic_citation, dict):
        if bibliographic_citation.get('citekey') is not None:
            post['bibliographicCitation'] = [
                bibliographic_citation.get('citekey')
            ]
        else:
            raise ValueError(
f":book:  {bibliographic_citation} não contém uma chave de citação para {post['title'].upper()}."
            )
    elif isinstance(bibliographic_citation, list):
        citekeys = []
        for citation in bibliographic_citation:
            if isinstance(citation, str):
                citekeys.append(
                    citation if citation.startswith('@') else '@' + citation
                )
            elif isinstance(citation, dict) and isinstance(citation.get('relids'), str):
                citekeys.append(
                    citation['relids'] if citation['relids'].startswith('@')
                    else "@" + citation['relids']
                )
            else:
                print(
f":warning:  O registro {citation} não contém um campo com chave de citação, ignorando..."
                )
        if len(citekeys) > 0:
            post['bibliographicCitation'] = citekeys

    coverage = post.get('coverage')
    if isinstance(coverage, dict):
        if coverage.get('spatial') is not None and post.get('spatial') is None:
            post['spatial'] = deepcopy(coverage['spatial'])
        if coverage.get('temporal') is not None and post.get('temporal') is None:
            post['temporal'] = deepcopy(coverage['temporal'])
        del post['coverage']

    spatial = post.get('spatial')
    post_format = post.get('format')
    if post_format is not None:
        format_extent = post_format.get('extent')
        if format_extent is not None and isinstance(format_extent, list):
            measurements = deepcopy(format_extent)
            for m in measurements:
                m['extent'] = deepcopy(m.get('type'))
                m['type'] = 'http://terminology.lido-schema.org/lido00927'
                m['value'] = deepcopy(m.get('measurements'))
                m['unit'] = { 'display': m.get('unit') } # Not schema-conforming
                if m.get('measurements') is not None:
                    del m['measurements']
            post['format']['extent'] = { 'measurements': measurements }

    elif isinstance(spatial, dict) and isinstance(spatial.get('extent'), list):
        measurements = deepcopy(spatial['extent'])
        for m in measurements:
            m['extent'] = deepcopy(m.get('type'))
            m['type'] = 'http://terminology.lido-schema.org/lido00927'
            m['value'] = deepcopy(m.get('measurements'))
            m['unit'] = { 'display': m.get('unit') } # Not schema-conforming
            if m.get('measurements') is not None:
                del m['measurements']
        post['format'] = post.get('format') or {}
        post['format']['extent'] = {
            'measurements': measurements,
        }

    places = []
    if isinstance(spatial, dict):
        location = spatial.get('location', {})
        if location.get('locationHistoric') is not None:
            post['location_historic'] = location['locationHistoric']

        if location.get('name') is not None:
            place_location = {
                'type': 'site',
                'term': location.get('state'),
                'location': deepcopy(location)
            }
            place_display = [location.get('name', {}).get('text'), location.get('city')]
            place_location['display'] = '\n'.join(part for part in place_display if part)

            place_location['location'].pop('name', None)
            place_location['location'].pop('city', None)
            place_location['location'].pop('state', None)
            place_location['location'].pop('country', None)
            place_location['location'].pop('locationHistoric', None)

            if place_location['location'].get('long') is not None:
                place_location['location']['lon'] = place_location['location'].pop('long')
            places.append(place_location)

        place_extent = spatial.get('extent', {})
        if isinstance(place_extent, dict) and place_extent.get('coordinates') is not None:
            place_footprint = {
                'type': 'site',
                'extent': {
                    'type': place_extent['type'],
                    'coordinates': str(place_extent['coordinates'])
                    # Otherwise it interprets WKT coordinates as nested lists
                },
            }
            if isinstance(place_extent['projection'], str) and place_extent.get('projection') is not None:
                place_footprint['srsName'] = {
                    'type': 'uri',
                    'display': place_extent['projection']
                }
                if place_extent['projection'] == 'EPSG:4326 WGS84':
                    place_footprint['srsName']['refid'] = 'http://www.opengis.net/def/crs/EPSG/0/4326'
            if place_extent.get('source') is not None:
                place_footprint['source'] = {
                    'display': place_extent['source'],
                    'type': 'corporate'
                }
            places.append(place_footprint)

        post['spatial'] = deepcopy(places) if places else None
    return post

def paths(args: list | None = None) -> dict[list[str], str] | None:
    """
    Gera os nomes de arquivos de entrada e a pasta de saída a partir
    da inserção do usuário.
    """
    if not args:
        if len(sys.argv) == 3:
            args = sys.argv[1:]
        else:
            text = input(
                """
                Informar um caminho de arquivo/ficheiro ou pasta de leitura
                e uma pasta de saída:
                (deixar em branco cancela a operação)
                """
            ).strip()
            args = text.split()
    if len(args) == 2:
        source, output_dir = args
    else:
        raise ValueError("Informar dois argumentos.")

    if os.path.isfile(source) and Path(source).suffix.lower() == ".md":
        filelist = [ source ]
    elif os.path.isdir(source):
        filelist = [
            os.path.join(source, f)
            for f in os.listdir(source)
            if os.path.isfile(os.path.join(source, f)) and Path(f).suffix.lower() == ".md"
        ]
    else:
        raise ValueError("O primeiro argumento não é um arquivo ou pasta válido.")
    return {'filelist': filelist, 'output_dir': output_dir}

def write_file(post: frontmatter.Post, output_dir: str, filename: str) -> None:
    """Grava cada arquivo/ficheiro conforme nome e pasta recebidos."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        dest = os.path.join(output_dir, filename)
        frontmatter.dump(post, dest, sort_keys=False)
        print(f"📄  '{dest}' gravado com sucesso.")
    except Exception as e:
        print(f":x:  Erro na escrita em '{dest}': {e}")

def main(args: dict[list, str] | None = None) -> int | None:
    """Compila todos os arquivos/ficheiros a serem gravados."""
    if args is None:
        args = paths()
        if args is None:
            return None
    files = args['filelist']
    output_dir = args['output_dir']
    try:
        os.makedirs(output_dir, exist_ok=True)
        print(f"📁  Pasta '{output_dir}' criada com sucesso.")
    except PermissionError:
        print(f"❌  Não foi possível criar a pasta '{output_dir}': sem permissões.")
    except Exception as e:
        print(f"❌  Erro na criação da pasta: {e}")
    for file in files:
        post = frontmatter.load(file)
        filename = os.path.basename(file)
        post = normalize(post)
        write_file(post, output_dir, filename)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
