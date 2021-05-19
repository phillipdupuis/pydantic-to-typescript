import os
from pydantic2ts import generate_typescript_defs


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
        os.system(cmd)

    with open(output_path, "r") as f:
        output = f.read()
    assert output == get_expected_output(test_name)


def test_single_module(tmpdir):
    run_test(tmpdir, "single_module")


def test_submodules(tmpdir):
    run_test(tmpdir, "submodules")


def test_generics(tmpdir):
    run_test(tmpdir, "generics")


def test_excluding_models(tmpdir):
    run_test(
        tmpdir, "excluding_models", exclude=("LoginCredentials", "LoginResponseData")
    )


def test_relative_filepath(tmpdir):
    test_name = "single_module"
    relative_path = os.path.join(".", "expected_results", test_name, "input.py")
    run_test(
        tmpdir, "single_module", module_path=relative_path,
    )


def test_calling_from_python(tmpdir):
    run_test(tmpdir, "single_module", call_from_python=True)
    run_test(tmpdir, "submodules", call_from_python=True)
    run_test(tmpdir, "generics", call_from_python=True)
    run_test(
        tmpdir,
        "excluding_models",
        call_from_python=True,
        exclude=("LoginCredentials", "LoginResponseData"),
    )
