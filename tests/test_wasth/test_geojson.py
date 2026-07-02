from glob import glob
import os
import pytest
import wasth.md2geojson

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

def test_md2geojson(input_dir, output_file):
    pass
