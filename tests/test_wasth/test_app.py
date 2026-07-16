import pytest
import wasth.app
import typer

@pytest.fixture
def valid_orcid_no():
    o = "0000-0002-0187-774X"
    return o

@pytest.fixture
def valid_orcid_uri():
    o = "https://orcid.org/0000-0002-0187-774X"
    return o

@pytest.fixture
def invalid_orcid():
    o =  "0000-0002-0187-7741"
    return o

def test_orcid_no_passes(valid_orcid_no):
    assert wasth.app.user_orcid(valid_orcid_no) == valid_orcid_no

def test_orcid_uri_passes(valid_orcid_no, valid_orcid_uri):
    assert wasth.app.user_orcid(valid_orcid_uri) == valid_orcid_no

def test_orcid_fails(invalid_orcid):
    with pytest.raises(typer.BadParameter) as e:
        wasth.app.user_orcid(invalid_orcid)
    assert str(e.value) == "❌  ORCiD inválido."
