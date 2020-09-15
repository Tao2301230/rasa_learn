from typing import Callable
from _pytest.pytester import RunResult


def test_shell_help(run: Callable[..., RunResult]):
    output = run("shell", "--help")

    help_text = """usage: rasa shell [-h] [-v] [-vv] [--quiet]
                  [--conversation-id CONVERSATION_ID] [-m MODEL]
                  [--log-file LOG_FILE] [--endpoints ENDPOINTS] [-p PORT]
                  [-t AUTH_TOKEN] [--cors [CORS [CORS ...]]] [--enable-api]
                  [--response-timeout RESPONSE_TIMEOUT]
                  [--remote-storage REMOTE_STORAGE]
                  [--ssl-certificate SSL_CERTIFICATE]
                  [--ssl-keyfile SSL_KEYFILE] [--ssl-ca-file SSL_CA_FILE]
                  [--ssl-password SSL_PASSWORD] [--credentials CREDENTIALS]
                  [--connector CONNECTOR] [--jwt-secret JWT_SECRET]
                  [--jwt-method JWT_METHOD]
                  {nlu} ... [model-as-positional-argument]"""

    lines = help_text.split("\n")

    for i, line in enumerate(lines):
        assert output.outlines[i] == line


def test_shell_nlu_help(run: Callable[..., RunResult]):
    output = run("shell", "nlu", "--help")

    help_text = """usage: rasa shell nlu [-h] [-v] [-vv] [--quiet] [-m MODEL]
                      [model-as-positional-argument]"""

    lines = help_text.split("\n")

    for i, line in enumerate(lines):
        assert output.outlines[i] == line
