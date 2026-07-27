import frontmatter
import geojson
import pytest

import wasth
import wasth.core.normalize as norm
from wasth.core import geoprocessa


@pytest.fixture
def testfile():
    f = "testdata/casa/br_df-planaltina-casarao_azul.md"
    return f

@pytest.fixture
def input_dir():
    d = "testdata/casa"
    return d

def test_geoprocessa(testfile):
    "Testa tipos de objetos retornados pelas funções"
    metadata = frontmatter.load(testfile)
    post = norm.normalize(metadata)
    assert isinstance(post, frontmatter.Post)
    work = wasth.Obra.from_post(post)
    assert isinstance(work, wasth.Obra)
    places = work.places()
    assert isinstance(places, geojson.FeatureCollection)
    assert places.errors() == []
    for place in places['features']:
        assert isinstance(place, geojson.Feature)
