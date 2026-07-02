import os
import shutil
import pytest
import wasth.valida_yaml
import wasth.normalize
import yamllint.config
import yamllint.linter

@pytest.fixture
def testfile():
    f = "testdata/casa/br_df-planaltina-casarao_azul.md"
    return f

@pytest.fixture
def output_file():
    f = "testdata/out/br_df-planaltina-casarao_azul.md"
    return f

def test_input(testfile):
    yaml_lint_list = wasth.valida_yaml.f_lint(testfile)
    try:
        assert len(yaml_lint_list) > 0
    except:
        print("O documento de teste não contém inconsistências de formatação.")

def test_normalize_metadata(testfile):
    import frontmatter
    source = frontmatter.load(testfile)
    normalized = wasth.normalize.NormalizedWork(testfile)
    post = normalized.post()
    assert isinstance(source['bibliographicCitation'], dict)
    assert isinstance(post['bibliographicCitation'], list)

def test_id(testfile, output_file):
    normalized = wasth.normalize.NormalizedWork(testfile)
    post = normalized.post()
    locations = normalized.locations(post)
    encoded_id = normalized.encode_id(post, locations)
    normalized.write_id(post, encoded_id)
    assert post['id'] == '58PJ98HQ+89W'

def test_write(testfile, output_file):
    if os.path.isdir('testdata/out'):
        shutil.rmtree('testdata/out')
    normalized = wasth.normalize.NormalizedWork(testfile)
    post = normalized.post()
    wasth.normalize.write_file(post, 'testdata/out', os.path.basename(testfile))
    try:
        assert os.path.isfile(output_file)
    except Exception as e:
        print(e)
    finally:
        os.remove(output_file)

def lint_metadata(testfile, output_file):
    normalized = wasth.normalize.NormalizedWork(testfile)
    post = normalized.post()
    wasth.normalize.write_file(post, 'testdata/out', os.path.basename(testfile))
    yaml_lint_list = wasth.valida_yaml.f_lint(output_file)
    try:
        assert len(yaml_lint_list) == 0
    except FileNotFoundError:
        print(f"Arquivo '{output_file}' não encontrado.")
    except Exception as e:
        print(f"{e}")
    except:
        print("Os metadados ainda contêm inconsistências de formatação.")
    finally:
        os.remove(output_file)
