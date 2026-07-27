"""Limpeza na formatação das fichas

Importa e reexporta o conteúdo das fichas para limpar a formatação.
Realiza algumas conversões do esquema DCMI para LIDO.
Valida a estrutura do conteúdo.
"""

import os
from copy import deepcopy
from pathlib import Path

import frontmatter
from rich import print
from ruamel.yaml import YAML

from wasth.core import models

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

def make_id(work: models.Obra, overwrite: bool | None = None) -> models.Obra:
    "Roda o método de geração de ID Open Location no objeto models.Obra"
    if work.get('spatial') is None:
        pass
    current_id = work.get('id')
    new_id = work.olc_id()
    if new_id is None:
        pass
    if current_id == new_id or new_id is None:
        return work
    if current_id is None:
        work['id'] = new_id
        return work
    if current_id != new_id:
        if overwrite is None:
            prompt = input(
f"Sobrescrever ID {current_id} existente com novo ID {new_id}? s/n"
            ).strip().lower()
            overwrite = prompt in { "s", "sim", "y", "yes", "true" }
        if overwrite is False:
            return work
    work['id'] = new_id
    return work

def write_id(source_file: str | None, enc: str = 'utf-8') -> models.Obra:
    "Grava o Open Location Code para o arquivo/ficheiro indicado."
    if not source_file:
        source_file = input("Inserir um caminho de arquivo/ficheiro:")
    if not os.path.isfile(source_file):
        raise ValueError(
            f":x:  Arquivo/ficheiro não encontrado em {source_file}"
        )
    if Path(source_file).suffix.lower() != ".md":
        raise ValueError(f":x:  {source_file} não é um arquivo válido.")
    try:
        work = models.Obra.from_file(source_file)
    except Exception as e:
        raise ValueError(f"""
:x:  Erro ao ler {source_file}:
   {e}
            """) from e
    work = make_id(work)
    with open(source_file, 'w', encoding=enc) as f:
        frontmatter.dump(work, f, sort_keys=False)
        print(
f":card_index:  ID: {make_id(work).get('id')} gravado em {source_file}."
        )
    return work

def main(args: models.InOutPaths | None = None) -> int | None:
    """Compila todos os arquivos/ficheiros a serem gravados."""
    if args is None:
        args = models.paths()
        if args is None:
            return None
    files = []
    raw_files = sorted(args['filelist'])
    for f in raw_files:
        if ".md" in f:
            files.append(f)
    output_dir = args['output_dir']
    try:
        os.makedirs(output_dir, exist_ok=True)
        print(f":open_file_folder:  Pasta '{output_dir}' criada com sucesso.")
    except PermissionError as e:
        raise PermissionError(f"""
:x:  Não foi possível criar a pasta '{output_dir}': {e}.
        """) from e
    except Exception as e:
        raise Exception(f":x:  Erro na criação da pasta: {e}") from e
    for file in files:
        post = frontmatter.load(file)
        filename = os.path.basename(file)
        post = normalize(post)
# Funcionalidade temporária abaixo, remover quando não for mais necessária.
        obra = models.Obra.from_post(post)
        post = make_id(obra)
# Funcionalidade temporária acima, remover quando não for mais necessária.
        models.write_file(post, output_dir, filename)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
