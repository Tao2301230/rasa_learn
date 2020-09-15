import asyncio
import pprint as pretty_print
import typing
from typing import Any, Dict, Text, Optional
from rasa.cli.utils import print_success, print_error
from rasa.core.interpreter import NaturalLanguageInterpreter, RasaNLUInterpreter

if typing.TYPE_CHECKING:
    from rasa.core.agent import Agent


def pprint(obj: Any):
    pretty_print.pprint(obj, indent=2)


def chat(
    model_path: Optional[Text] = None,
    endpoints: Optional[Text] = None,
    agent: Optional["Agent"] = None,
    interpreter: Optional[NaturalLanguageInterpreter] = None,
) -> None:
    """Chat to the bot within a Jupyter notebook.

    Args:
        model_path: Path to a combined Rasa model.
        endpoints: Path to a yaml with the action server is custom actions are defined.
        agent: Rasa Core agent (used if no Rasa model given).
        interpreter: Rasa NLU interpreter (used with Rasa Core agent if no
                     Rasa model is given).
    """

    if model_path:
        from rasa.run import create_agent

        agent = create_agent(model_path, endpoints)

    elif agent is not None and interpreter is not None:
        # HACK: this skips loading the interpreter and directly
        # sets it afterwards
        nlu_interpreter = RasaNLUInterpreter(
            "skip this and use given interpreter", lazy_init=True
        )
        nlu_interpreter.interpreter = interpreter
        agent.interpreter = interpreter
    else:
        print_error(
            "You either have to define a model path or an agent and an interpreter."
        )
        return

    print("Your bot is ready to talk! Type your messages here or send '/stop'.")
    loop = asyncio.get_event_loop()
    while True:
        message = input()
        if message == "/stop":
            break

        responses = loop.run_until_complete(agent.handle_text(message))
        for response in responses:
            _display_bot_response(response)


def _display_bot_response(response: Dict):
    from IPython.display import Image, display  # pytype: disable=import-error

    for response_type, value in response.items():
        if response_type == "text":
            print_success(value)

        if response_type == "image":
            image = Image(url=value)
            display(image)
