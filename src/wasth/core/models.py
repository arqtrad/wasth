"""Modelos de objeto usados no WASTH, especialmente a ficha de obra"""

import os
import frontmatter
import geojson
from ruamel.yaml import YAML
import yamale
import openlocationcode.openlocationcode as openlocationcode
from .valida_yaml import f_valida
yaml = YAML(typ='safe')

class Work(frontmatter.Post):
    """
    Arcabouço dos dados e métodos das fichas de obras
    """
    def __init__(self, content: str = '', handler=None, **metadata) -> None:
        super().__init__(content=content, handler=handler, **metadata)

    @classmethod
    def from_file(cls, f):
        self = frontmatter.load(f)
        return cls(content=self.content, handler=self.handler, **self.metadata)

    @classmethod
    def from_post(cls, post: frontmatter.Post) -> Work:
        return cls(content=post.content, handler=post.handler, **post.metadata)

    def places(self) -> geojson.FeatureCollection | None:
        """Cria geoJSON a partir de 'spatial'"""
        spatial = self.get('spatial')
        if not spatial:
            raise ValueError("🌐❌  A obra não está georreferenciada.")
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
                    raise ValueError("🌐❌  Latitude e/ou longitude ausentes.")
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
                        f"🌐❌  {geom_type} não é um tipo de geometria válido."
                                     )
            else:
                raise ValueError(
                    "🌐❌  Dados de georreferenciamento inexistentes."
                                 )
            feature = geojson.Feature(geometry=geom, properties=props)
            if feature.is_valid:
                places.append(feature)
            else:
                raise ValueError(f"""
                    🌐❌  Dados de georreferenciamento inválidos:
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
        current_id = self.get('id')
        for place in spatial:
            if place.get('type') == 'site' and place.get('location'):
                location = place['location']
                lat = location.get('lat')
                lon = location.get('lon')
                if lat is None or lon is None:
                    continue
                new_id = openlocationcode.encode(lat, lon, 11)
                if current_id is None:
                    self['id'] = new_id
                    return new_id
                elif new_id != current_id:
                    overwrite = input(
                        f"🌐⚠️  Sobrescrever ID existente {current_id} com novo {new_id} ? s/n"
                    ).strip().lower()
                    if overwrite in {"s", "sim", "y", "yes"}:
                        self['id'] = new_id
                        return new_id
                    else:
                        return current_id
                else:
                    return None
        return current_id

    def valida(self, schema_file: str = "data/schema.yaml", parser: str = "ruamel") -> None:
        dir = os.path.abspath(os.path.dirname(__file__))
        with open(os.path.join(dir, schema_file), 'r') as f:
            schema = f.read()
        schema = yamale.make_schema(content=schema, parser=parser)
        content = yaml.dump(self.metadata, sort_keys=False, allow_unicode=True)
        data = yamale.make_data(content=content, parser=parser)
        yamale.validate(schema, data)

class GeoFeatures(geojson.FeatureCollection):
    pass
