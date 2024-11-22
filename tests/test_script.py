import os
import subprocess
from itertools import product
from pathlib import Path
from typing import Optional, Tuple

import pytest

from pydantic2ts import generate_typescript_defs
from pydantic2ts.cli.script import parse_cli_args
from pydantic2ts.pydantic_v2 import enabled as v2_enabled

_PYDANTIC_VERSIONS = (1, 2) if v2_enabled else (1,)
_RESULTS_DIRECTORY = Path(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "expected_results")
)


def _python_module_path(test_name: str, pydantic_version: int) -> str:
    return str(_RESULTS_DIRECTORY / test_name / f"v{pydantic_version}_input.py")


def _expected_typescript_code(test_name: str) -> str:
    return (_RESULTS_DIRECTORY / test_name / "output.ts").read_text()


def _run_test(
    tmp_path: Path,
    test_name: str,
    pydantic_version: int,
    *,
    module_path: Optional[str] = None,
    call_from_python: bool = False,
    exclude: Tuple[str, ...] = (),
):
    """
    Execute pydantic2ts logic for converting pydantic models into tyepscript definitions.
    Compare the output with the expected output, verifying it is identical.
    """
    module_path = module_path or _python_module_path(test_name, pydantic_version)
    output_path = str(tmp_path / f"{test_name}_v{pydantic_version}.ts")

    if call_from_python:
        generate_typescript_defs(module_path, output_path, exclude)
    else:
        cmd = f"pydantic2ts --module {module_path} --output {output_path}"
        for model_to_exclude in exclude:
            cmd += f" --exclude {model_to_exclude}"
        subprocess.run(cmd, shell=True, check=True)

    assert Path(output_path).read_text() == _expected_typescript_code(test_name)


@pytest.mark.parametrize(
    "pydantic_version, call_from_python",
    product(_PYDANTIC_VERSIONS, [False, True]),
)
def test_single_module(tmp_path: Path, pydantic_version: int, call_from_python: bool):
    _run_test(tmp_path, "single_module", pydantic_version, call_from_python=call_from_python)


@pytest.mark.parametrize(
    "pydantic_version, call_from_python",
    product(_PYDANTIC_VERSIONS, [False, True]),
)
def test_submodules(tmp_path: Path, pydantic_version: int, call_from_python: bool):
    _run_test(tmp_path, "submodules", pydantic_version, call_from_python=call_from_python)


@pytest.mark.parametrize(
    "pydantic_version, call_from_python",
    product(_PYDANTIC_VERSIONS, [False, True]),
)
def test_generics(tmp_path: Path, pydantic_version: int, call_from_python: bool):
    _run_test(tmp_path, "generics", pydantic_version, call_from_python=call_from_python)


@pytest.mark.parametrize(
    "pydantic_version, call_from_python",
    product(_PYDANTIC_VERSIONS, [False, True]),
)
def test_excluding_models(tmp_path: Path, pydantic_version: int, call_from_python: bool):
    _run_test(
        tmp_path,
        "excluding_models",
        pydantic_version,
        call_from_python=call_from_python,
        exclude=("LoginCredentials", "LoginResponseData"),
    )


@pytest.mark.parametrize(
    "pydantic_version, call_from_python",
    product([v for v in _PYDANTIC_VERSIONS if v > 1], [False, True]),
)
def test_computed_fields(tmp_path: Path, pydantic_version: int, call_from_python: bool):
    _run_test(tmp_path, "computed_fields", pydantic_version, call_from_python=call_from_python)


@pytest.mark.parametrize(
    "pydantic_version, call_from_python",
    product(_PYDANTIC_VERSIONS, [False, True]),
)
def test_extra_fields(tmp_path: Path, pydantic_version: int, call_from_python: bool):
    _run_test(tmp_path, "extra_fields", pydantic_version, call_from_python=call_from_python)


def test_relative_filepath(tmp_path: Path):
    test_name = "single_module"
    pydantic_version = _PYDANTIC_VERSIONS[0]
    absolute_path = _python_module_path(test_name, pydantic_version)
    relative_path = Path(absolute_path).relative_to(Path.cwd())
    _run_test(
        tmp_path,
        test_name,
        pydantic_version,
        module_path=str(relative_path),
    )


def test_error_if_json2ts_not_installed(tmp_path: Path):
    module_path = _python_module_path("single_module", _PYDANTIC_VERSIONS[0])
    output_path = str(tmp_path / "json2ts_test_output.ts")

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


def test_error_if_invalid_module_path(tmp_path: Path):
    with pytest.raises(ModuleNotFoundError):
        generate_typescript_defs("fake_module", str(tmp_path / "fake_module_output.ts"))


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
