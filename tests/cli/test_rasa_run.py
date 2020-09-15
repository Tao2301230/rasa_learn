import os
from typing import Callable
from _pytest.pytester import RunResult


def test_run_does_not_start(run_in_simple_project: Callable[..., RunResult]):
    os.remove("domain.yml")

    # the server should not start as no model is configured
    output = run_in_simple_project("run")

    assert "No model found." in output.outlines[0]


def test_run_help(run: Callable[..., RunResult]):
    output = run("run", "--help")

    help_text = """usage: rasa run [-h] [-v] [-vv] [--quiet] [-m MODEL] [--log-file LOG_FILE]
                [--endpoints ENDPOINTS] [-p PORT] [-t AUTH_TOKEN]
                [--cors [CORS [CORS ...]]] [--enable-api]
                [--response-timeout RESPONSE_TIMEOUT]
                [--remote-storage REMOTE_STORAGE]
                [--ssl-certificate SSL_CERTIFICATE]
                [--ssl-keyfile SSL_KEYFILE] [--ssl-ca-file SSL_CA_FILE]
                [--ssl-password SSL_PASSWORD] [--credentials CREDENTIALS]
                [--connector CONNECTOR] [--jwt-secret JWT_SECRET]
                [--jwt-method JWT_METHOD]
                {actions} ... [model-as-positional-argument]"""

    lines = help_text.split("\n")

    for i, line in enumerate(lines):
        assert output.outlines[i] == line


def test_run_action_help(run: Callable[..., RunResult]):
    output = run("run", "actions", "--help")

    help_text = """usage: rasa run actions [-h] [-v] [-vv] [--quiet] [-p PORT]
                        [--cors [CORS [CORS ...]]] [--actions ACTIONS]"""

    lines = help_text.split("\n")

    for i, line in enumerate(lines):
        assert output.outlines[i] == line
