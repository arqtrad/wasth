import pytest
import geojson
import frontmatter
import wasth
import wasth.core.normalize as norm
from wasth.core import md2geojson

@pytest.fixture
def testfile():
    f = "testdata/casa/br_df-planaltina-casarao_azul.md"
    return f

@pytest.fixture
def input_dir():
    d = "testdata/casa"
    return d

def test_md2geojson(testfile):
    "Testa tipos de objetos retornados pelas funções"
    metadata = frontmatter.load(testfile)
    post = norm.normalize(metadata)
    assert isinstance(post, frontmatter.Post)
    work = wasth.Work.from_post(post)
    assert isinstance(work, wasth.Work)
    places = work.places()
    assert isinstance(places, geojson.FeatureCollection)
    assert places.errors() == []
    for place in places['features']:
        assert isinstance(place, geojson.Feature)
