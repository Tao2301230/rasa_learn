import os
from pathlib import Path
from typing import Callable
from _pytest.pytester import RunResult


def test_init_using_init_dir_option(run_with_stdin: Callable[..., RunResult]):
    os.makedirs("./workspace")
    run_with_stdin(
        "init", "--quiet", "--init-dir", "./workspace", stdin=b"N"
    )  # avoid training an initial model

    required_files = [
        "actions.py",
        "domain.yml",
        "config.yml",
        "credentials.yml",
        "endpoints.yml",
        "data/nlu.yml",
        "data/stories.yml",
        "data/rules.yml",
    ]
    assert all((Path("workspace") / file).exists() for file in required_files)


def test_not_found_init_path(run: Callable[..., RunResult]):
    output = run("init", "--no-prompt", "--quiet", "--init-dir", "./workspace")

    assert (
        output.outlines[-1]
        == "\033[91mProject init path './workspace' not found.\033[0m"
    )


def test_init_help(run: Callable[..., RunResult]):
    output = run("init", "--help")

    assert (
        output.outlines[0]
        == "usage: rasa init [-h] [-v] [-vv] [--quiet] [--no-prompt] [--init-dir INIT_DIR]"
    )


def test_user_asked_to_train_model(run_with_stdin: Callable[..., RunResult]):
    run_with_stdin("init", stdin=b"\nYN")
    assert not os.path.exists("models")
