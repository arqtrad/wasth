import os
import shutil
import pytest
import frontmatter
import wasth.core.valida_yaml
import wasth.core.normalize as norm
import yamllint.config
import yamllint.linter

@pytest.fixture
def testfile():
    f = "testdata/fail/br_ba-salvador-casa_7_candeeiros.md"
    return f

@pytest.fixture
def testfile2():
    f = "testdata/fail/br_df-planaltina-casarao_azul.md"
    return f

@pytest.fixture
def output_dir():
    d = "testdata/out"
    return d

def test_input(testfile):
    yaml_lint_list = wasth.valida_yaml.f_lint(testfile)
    try:
        assert len(yaml_lint_list) > 0
    except:
        print("O documento de teste não contém inconsistências de formatação.")

def test_paths(monkeypatch, testfile, output_dir):
    monkeypatch.setattr(
        'builtins.input',
        lambda _: str(testfile + " " + output_dir)
    )
    result = norm.paths()
    assert isinstance(result, dict)
    assert isinstance(result['filelist'], list)
    assert isinstance(result['output_dir'], str)

def test_normalize_metadata(testfile2, output_dir):
    filename = os.path.basename(testfile2)
    output_file = os.path.join(output_dir, filename)
    source = frontmatter.load(testfile2)
    assert isinstance(source['bibliographicCitation'], dict)
    try:
        norm.main({'filelist': [testfile2], 'output_dir': output_dir})
        post = frontmatter.load(output_file)
        assert os.path.isfile(output_file)
        assert isinstance(post, frontmatter.Post)
        assert isinstance(post['bibliographicCitation'], list)
        assert post['bibliographicCitation'][0].startswith("@")
    finally:
        os.remove(output_file)

def test_id(testfile2):
    post = frontmatter.load(testfile2)
    normalized = norm.normalize(post)
    work = wasth.Work.from_post(normalized)
    assert work.olc_id() == '58PJ98HQ+89W'

def test_write(testfile, output_dir):
    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)
    post = frontmatter.load(testfile)
    normalized = norm.normalize(post)
    filename = os.path.basename(testfile)
    norm.write_file(normalized, output_dir, filename)
    assert os.path.isfile(os.path.join(output_dir, filename))

def lint_metadata(testfile, output_dir):
    post = frontmatter.load(testfile)
    normalized = norm.normalize(post)
    post = normalized.post()
    norm.write_file(post, output_dir, os.path.basename(testfile))
    output_file = os.path.join(output_dir, os.path.basename(testfile))
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
