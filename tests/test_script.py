import os
import subprocess
import sys

import pytest

from pydantic2ts import generate_typescript_defs
from pydantic2ts.cli.script import parse_cli_args


def _results_directory() -> str:
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), "expected_results")


def get_input_module(test_name: str) -> str:
    return os.path.join(_results_directory(), test_name, "input.py")


def get_expected_output(test_name: str) -> str:
    path = os.path.join(_results_directory(), test_name, "output.ts")
    with open(path, "r") as f:
        return f.read()


def run_test(
    tmpdir, test_name, *, module_path=None, call_from_python=False, exclude=()
):
    """
    Execute pydantic2ts logic for converting pydantic models into tyepscript definitions.
    Compare the output with the expected output, verifying it is identical.
    """
    module_path = module_path or get_input_module(test_name)
    output_path = tmpdir.join(f"cli_{test_name}.ts").strpath

    if call_from_python:
        generate_typescript_defs(module_path, output_path, exclude)
    else:
        cmd = f"pydantic2ts --module {module_path} --output {output_path}"
        for model_to_exclude in exclude:
            cmd += f" --exclude {model_to_exclude}"
        subprocess.run(cmd, shell=True)

    with open(output_path, "r") as f:
        output = f.read()
    assert output == get_expected_output(test_name)


def test_single_module(tmpdir):
    run_test(tmpdir, "single_module")


@pytest.mark.skipif(
    sys.version_info < (3, 8),
    reason="Literal requires python 3.8 or higher (Ref.: PEP 586)",
)
def test_submodules(tmpdir):
    run_test(tmpdir, "submodules")


@pytest.mark.skipif(
    sys.version_info < (3, 7),
    reason=(
        "GenericModel is only supported for python>=3.7 "
        "(Ref.: https://pydantic-docs.helpmanual.io/usage/models/#generic-models)"
    ),
)
def test_generics(tmpdir):
    run_test(tmpdir, "generics")


def test_excluding_models(tmpdir):
    run_test(
        tmpdir, "excluding_models", exclude=("LoginCredentials", "LoginResponseData")
    )


def test_relative_filepath(tmpdir):
    test_name = "single_module"
    relative_path = os.path.join(
        ".", "tests", "expected_results", test_name, "input.py"
    )
    run_test(
        tmpdir,
        "single_module",
        module_path=relative_path,
    )


def test_calling_from_python(tmpdir):
    run_test(tmpdir, "single_module", call_from_python=True)
    if sys.version_info >= (3, 8):
        run_test(tmpdir, "submodules", call_from_python=True)
    if sys.version_info >= (3, 7):
        run_test(tmpdir, "generics", call_from_python=True)
    run_test(
        tmpdir,
        "excluding_models",
        call_from_python=True,
        exclude=("LoginCredentials", "LoginResponseData"),
    )


def test_error_if_json2ts_not_installed(tmpdir):
    module_path = get_input_module("single_module")
    output_path = tmpdir.join(f"cli_single_module.ts").strpath

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
        generate_typescript_defs(
            "fake_module", tmpdir.join(f"fake_module_output.ts").strpath
        )


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
