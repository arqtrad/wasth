from glob import glob
import os
import pytest
import frontmatter
import xmlschema
from wasth.core import valida_yaml
from wasth.core import valida_xml

@pytest.fixture
def testfile():
    f = "testdata/casa/br_df-planaltina-casarao_azul.md"
    return f

def test_f_read(testfile):
    "Testa se o arquivo pode ser lido"
    assert isinstance(valida_yaml.f_read(testfile), dict)

def test_parse_metadata(testfile):
    "Testa se os metadados podem ser lidos"
    post = valida_yaml.parse_metadata(testfile)
    assert post['title'] == "Casarão Azul"
    assert len(post.content) > 1
    assert isinstance(post, frontmatter.Post)

def test_f_lint(testfile):
    assert isinstance(valida_yaml.f_lint(testfile), list)


def test_create_schema():
    "Testa o esquema XML"
    xml_profile = valida_xml.create_schema()
    assert isinstance(xml_profile, xmlschema.XMLSchema11)

def test_valid_xml():
    "Testa que o arquivo exemplo valida com o esquema"
    assert valida_xml.valid_xml(
        "testdata/lido/Stabkirche_Gol_Original_de_en_v1.1_20250331.xml"
    ) is True

def test_invalid_xml():
    "Testa que um arquivo inválido falha na validação"
    with pytest.raises(xmlschema.exceptions.XMLResourceParseError):
        valida_xml.valid_xml("testdata/invalid.xml")
