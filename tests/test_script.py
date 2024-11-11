import os
import subprocess
from itertools import product
from pathlib import Path

import pytest

from pydantic2ts import generate_typescript_defs
from pydantic2ts.cli.script import parse_cli_args

try:
    from pydantic import BaseModel
    from pydantic.v1 import BaseModel as BaseModelV1

    assert BaseModel is not BaseModelV1
    _PYDANTIC_VERSIONS = ("v1", "v2")
except (ImportError, AttributeError):
    _PYDANTIC_VERSIONS = ("v1",)

_RESULTS_DIRECTORY = Path(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "expected_results")
)


def _get_input_module(test_name: str, pydantic_version: str) -> Path:
    return _RESULTS_DIRECTORY / test_name / pydantic_version / "input.py"


def _get_expected_output(test_name: str, pydantic_version: str) -> str:
    return (_RESULTS_DIRECTORY / test_name / pydantic_version / "output.ts").read_text()


def _run_test(
    tmpdir,
    test_name,
    pydantic_version,
    *,
    module_path=None,
    call_from_python=False,
    exclude=(),
):
    """
    Execute pydantic2ts logic for converting pydantic models into tyepscript definitions.
    Compare the output with the expected output, verifying it is identical.
    """
    module_path = module_path or _get_input_module(test_name, pydantic_version)
    output_path = tmpdir.join(f"cli_{test_name}_{pydantic_version}.ts").strpath

    if call_from_python:
        generate_typescript_defs(module_path, output_path, exclude)
    else:
        cmd = f"pydantic2ts --module {module_path} --output {output_path}"
        for model_to_exclude in exclude:
            cmd += f" --exclude {model_to_exclude}"
        subprocess.run(cmd, shell=True, check=True)

    assert Path(output_path).read_text() == _get_expected_output(test_name, pydantic_version)


@pytest.mark.parametrize(
    "pydantic_version, call_from_python",
    product(_PYDANTIC_VERSIONS, [False, True]),
)
def test_single_module(tmpdir, pydantic_version, call_from_python):
    _run_test(tmpdir, "single_module", pydantic_version, call_from_python=call_from_python)


@pytest.mark.parametrize(
    "pydantic_version, call_from_python",
    product(_PYDANTIC_VERSIONS, [False, True]),
)
def test_submodules(tmpdir, pydantic_version, call_from_python):
    _run_test(tmpdir, "submodules", pydantic_version, call_from_python=call_from_python)


@pytest.mark.parametrize(
    "pydantic_version, call_from_python",
    product(_PYDANTIC_VERSIONS, [False, True]),
)
def test_generics(tmpdir, pydantic_version, call_from_python):
    _run_test(tmpdir, "generics", pydantic_version, call_from_python=call_from_python)


@pytest.mark.parametrize(
    "pydantic_version, call_from_python",
    product(_PYDANTIC_VERSIONS, [False, True]),
)
def test_excluding_models(tmpdir, pydantic_version, call_from_python):
    _run_test(
        tmpdir,
        "excluding_models",
        pydantic_version,
        call_from_python=call_from_python,
        exclude=("LoginCredentials", "LoginResponseData"),
    )


@pytest.mark.parametrize(
    "pydantic_version, call_from_python",
    product(_PYDANTIC_VERSIONS, [False, True]),
)
def test_computed_fields(tmpdir, pydantic_version, call_from_python):
    if pydantic_version == "v1":
        pytest.skip("Computed fields are a pydantic v2 feature")
    _run_test(tmpdir, "computed_fields", pydantic_version, call_from_python=call_from_python)


@pytest.mark.parametrize(
    "pydantic_version, call_from_python",
    product(_PYDANTIC_VERSIONS, [False, True]),
)
def test_extra_fields(tmpdir, pydantic_version, call_from_python):
    _run_test(tmpdir, "extra_fields", pydantic_version, call_from_python=call_from_python)


def test_relative_filepath(tmpdir):
    test_name = "single_module"
    pydantic_version = _PYDANTIC_VERSIONS[0]
    relative_path = (
        Path(".") / "tests" / "expected_results" / test_name / pydantic_version / "input.py"
    )
    _run_test(
        tmpdir,
        test_name,
        pydantic_version,
        module_path=relative_path,
    )


def test_error_if_json2ts_not_installed(tmpdir):
    module_path = _get_input_module("single_module", _PYDANTIC_VERSIONS[0])
    output_path = tmpdir.join("json2ts_test_output.ts").strpath

    # If the json2ts command has no spaces and the executable cannot be found,
    # that means the user either hasn't installed json-schema-to-typescript or they made a typo.
    # We should raise a descriptive error with installation instructions.
    invalid_global_cmd = "someCommandWhichDefinitelyDoesNotExist"
    with pytest.raises(Exception) as exc1:
        generate_typescript_defs(
            module_path,
            output_path,
            json2ts_cmd=invalid_global_cmd,
        )
    assert (
        str(exc1.value)
        == "json2ts must be installed. Instructions can be found here: https://www.npmjs.com/package/json-schema-to-typescript"
    )

    # But if the command DOES contain spaces (ex: "yarn json2ts") they're likely using a locally installed CLI.
    # We should not be validating the command in this case.
    # Instead we should just be *trying* to run it and checking the exit code.
    invalid_local_cmd = "yaaaarn json2tsbutwithatypo"
    with pytest.raises(RuntimeError) as exc2:
        generate_typescript_defs(
            module_path,
            output_path,
            json2ts_cmd=invalid_local_cmd,
        )
    assert str(exc2.value).startswith(f'"{invalid_local_cmd}" failed with exit code ')


def test_error_if_invalid_module_path(tmpdir):
    with pytest.raises(ModuleNotFoundError):
        generate_typescript_defs("fake_module", tmpdir.join("fake_module_output.ts").strpath)


def test_parse_cli_args():
    args_basic = parse_cli_args(["--module", "my_module.py", "--output", "myOutput.ts"])
    assert args_basic.module == "my_module.py"
    assert args_basic.output == "myOutput.ts"
    assert args_basic.exclude == []
    assert args_basic.json2ts_cmd == "json2ts"
    args_with_excludes = parse_cli_args(
        [
            "--module",
            "my_module.py",
            "--output",
            "myOutput.ts",
            "--exclude",
            "Foo",
            "--exclude",
            "Bar",
        ]
    )
    assert args_with_excludes.exclude == ["Foo", "Bar"]
