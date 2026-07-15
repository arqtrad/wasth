from glob import glob
import os
import pytest
import geojson
import frontmatter
import wasth
import wasth.normalize as norm
import wasth.md2geojson as md2geojson

@pytest.fixture
def testfile():
    f = "testdata/casa/br_df-planaltina-casarao_azul.md"
    return f

@pytest.fixture
def input_dir():
    dir = "testdata/casa"
    return dir

def test_md2geojson(testfile):
    metadata = frontmatter.load(testfile)
    post = norm.normalize(metadata)
    assert type(post) is frontmatter.Post
    work = wasth.Work.from_post(post)
    assert type(work) is wasth.Work
    test_geofeature = md2geojson.make_feature(work)
    assert isinstance(test_geofeature, geojson.Feature)
