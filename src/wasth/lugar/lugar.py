"""Operações com as fichas de lugares

Cria e edita fichas de lugares.
"""
import geojson

from wasth.core import models


def extract_feature(collection: geojson.FeatureCollection) -> list | None:
    features = []
    if not isinstance(collection, geojson.FeatureCollection) or not collection[0]:
        return None
    for feature in collection['features']:
        features.append(feature)
    return features
