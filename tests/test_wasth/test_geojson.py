from glob import glob
import os
import pytest
import geojson
import frontmatter
import wasth.md2geojson as md2geojson
import wasth.normalize as norm

@pytest.fixture
def testfile():
    f = "testdata/casa/br_df-planaltina-casarao_azul.md"
    return f

@pytest.fixture
def input_dir():
    dir = "testdata/casa"
    return dir

@pytest.fixture
def output_file():
    f = "testdata/test.geojson"
    return f

def test_md2geojson(testfile):
    post = norm.NormalizedWork(testfile)
    test_geofeature = md2geojson.make_feature(post)
    assert isinstance(test_geofeature, geojson.Feature)
