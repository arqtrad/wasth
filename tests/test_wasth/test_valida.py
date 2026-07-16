from glob import glob
import os
import pytest
import xmlschema
import wasth.core.valida_yaml
import wasth.core.valida_xml

@pytest.fixture
def testfile():
    f = "testdata/casa/br_df-planaltina-casarao_azul.md"
    return f

# Testes de YAML linting

def test_f_read(testfile):
    assert type(wasth.core.valida_yaml.f_read(testfile)) is dict

def test_parse_metadata(testfile):
    import frontmatter
    post = wasth.core.valida_yaml.parse_metadata(testfile)
    assert post['title'] == "Casarão Azul"
    assert len(post.content) > 1
    assert type(post) is frontmatter.Post

def test_f_lint(testfile):
    assert type(wasth.core.valida_yaml.f_lint(testfile)) is list

# Testes de validação do esquema XML

def test_create_schema(schema_path="schemata/lido-v1.1-profile-architecture-v1.1.xsd"):
    wasth.core.valida_xml.create_schema()
    assert os.path.isfile(schema_path)

def test_valid_xml(schema="schemata/lido-v1.1-profile-architecture-v1.1.xsd"):
    assert wasth.core.valida_xml.valid_xml("testdata/lido/Stabkirche_Gol_Original_de_en_v1.1_20250331.xml") == True

def test_invalid_xml(schema="schemata/lido-v1.1-profile-architecture-v1.1.xsd"):
    with pytest.raises(xmlschema.exceptions.XMLResourceParseError):
        wasth.core.valida_xml.valid_xml("testdata/invalid.xml")
