"""WASTH: Web App para Sítios Tradicionais e Históricos"""

__version__ = "0.2.0"

import frontmatter
import geojson
from .valida_yaml import valida_yaml
from .geoprocess import OpenLocation

__all__ = ["Work", "valida_yaml"]

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

    def places(self) -> geojson.FeatureCollection | None:
        """Valida valores do georreferenciamento"""
        if self.get('spatial'):
            places = []
            for place in self['spatial']:
                props = {
                    'type': place['type'] if place.get('type') else 'site',
                    'display': place['display'] if place.get('display') else None,
                    'zoom': place['zoom'] if place.get('zoom') else None,
                }
                lat = place['location']['lat']
                lon = place['location']['lon']
                location = geojson.Feature(geometry=geojson.Point((lon, lat)), properties={'type': place_type})
                if location.is_valid:
                    locations.append(location)
                else:
                    raise ValueError(f"🌐❌  Dados de georreferenciamento inválidos: {location.errors()}")

            if extent['type'] == 'Polygon':
                fp_geom = geojson.Polygon(extent['coordinates'])
            elif extent['type'] == 'MultiPolygon':
                fp_geom = geojson.MultiPolygon(extent['coordinates'])
            footprint = geojson.Feature(geometry=fp_geom, properties=fp_props)

            places = geojson.FeatureCollection(locations)
            return places
        else:
            raise ValueError("🌐❌  A obra não está georreferenciada.")

    def encode_id(self) -> str | None:
        current_id = self['id'] if (self.get('id') is not None) else None
        for location in self['spatial']:
            if location['properties']['type'] == 'site':
                lat = location['lat']
                lon = location['lon']
                open_location = OpenLocation(current_id, lat, lon)
                id = open_location.encode()
                return id
        return None

    def write_id(self) -> None:
        if isinstance(self.encode_id(), str):
            if self.encode_id() != self.get('id'):
                self['id'] = self.encode_id()
