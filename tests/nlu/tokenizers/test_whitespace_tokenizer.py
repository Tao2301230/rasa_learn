import pytest


from rasa.nlu.components import UnsupportedLanguageError
from rasa.nlu.config import RasaNLUModelConfig
from rasa.nlu.constants import (
    TOKENS_NAMES,
    TEXT,
    INTENT,
    ACTION_NAME,
    ACTION_TEXT,
)

from rasa.nlu.training_data import TrainingData, Message
from rasa.nlu.tokenizers.whitespace_tokenizer import WhitespaceTokenizer


@pytest.mark.parametrize(
    "text, expected_tokens, expected_indices",
    [
        (
            "Forecast for lunch",
            ["Forecast", "for", "lunch"],
            [(0, 8), (9, 12), (13, 18)],
        ),
        (
            "hey ńöñàśçií how're you?",
            ["hey", "ńöñàśçií", "how", "re", "you"],
            [(0, 3), (4, 12), (13, 16), (17, 19), (20, 23)],
        ),
        (
            "50 क्या आपके पास डेरी मिल्क 10 वाले बॉक्स मिल सकते है",
            [
                "50",
                "क्या",
                "आपके",
                "पास",
                "डेरी",
                "मिल्क",
                "10",
                "वाले",
                "बॉक्स",
                "मिल",
                "सकते",
                "है",
            ],
            [
                (0, 2),
                (3, 7),
                (8, 12),
                (13, 16),
                (17, 21),
                (22, 27),
                (28, 30),
                (31, 35),
                (36, 41),
                (42, 45),
                (46, 50),
                (51, 53),
            ],
        ),
        (
            "https://www.google.com/search?client=safari&rls=en&q=i+like+rasa&ie=UTF-8&oe=UTF-8 https://rasa.com/docs/nlu/components/#tokenizer-whitespace",
            [
                "https://www.google.com/search?"
                "client=safari&rls=en&q=i+like+rasa&ie=UTF-8&oe=UTF-8",
                "https://rasa.com/docs/nlu/components/#tokenizer-whitespace",
            ],
            [(0, 82), (83, 141)],
        ),
        (
            "Joselico gracias Dois 🙏🇺🇸🏦🛠🔥⭐️🦅👑💪",
            ["Joselico", "gracias", "Dois"],
            [(0, 8), (9, 16), (17, 21)],
        ),
        (":)", [":)"], [(0, 2)]),
        ("Hi :-)", ["Hi"], [(0, 2)]),
        ("👍", ["👍"], [(0, 1)]),
    ],
)
def test_whitespace(text, expected_tokens, expected_indices):

    tk = WhitespaceTokenizer()

    tokens = tk.tokenize(Message.build(text=text), attribute=TEXT)

    assert [t.text for t in tokens] == expected_tokens
    assert [t.start for t in tokens] == [i[0] for i in expected_indices]
    assert [t.end for t in tokens] == [i[1] for i in expected_indices]


@pytest.mark.parametrize(
    "text, expected_tokens",
    [
        ("Forecast_for_LUNCH", ["Forecast_for_LUNCH"]),
        ("Forecast for LUNCH", ["Forecast for LUNCH"]),
    ],
)
def test_custom_intent_symbol(text, expected_tokens):
    component_config = {"intent_tokenization_flag": True, "intent_split_symbol": "+"}

    tk = WhitespaceTokenizer(component_config)

    message = Message.build(text=text)
    message.set(INTENT, text)

    tk.train(TrainingData([message]))

    assert [t.text for t in message.get(TOKENS_NAMES[INTENT])] == expected_tokens


def test_whitespace_training(supervised_embeddings_config: RasaNLUModelConfig):
    examples = [
        Message(
            data={
                TEXT: "Any Mexican restaurant will do",
                "intent": "restaurant_search",
                "entities": [
                    {"start": 4, "end": 11, "value": "Mexican", "entity": "cuisine"}
                ],
            },
        ),
        Message(
            data={
                TEXT: "I want Tacos!",
                "intent": "restaurant_search",
                "entities": [
                    {"start": 7, "end": 12, "value": "Mexican", "entity": "cuisine"}
                ],
            },
        ),
        Message(data={TEXT: "action_restart", "action_name": "action_restart"},),
        Message(
            data={
                TEXT: "Where are you going?",
                ACTION_NAME: "Where are you going?",
                ACTION_TEXT: "Where are you going?",
            },
        ),
    ]

    component_config = {"case_sensitive": False, "intent_tokenization_flag": True}
    tk = WhitespaceTokenizer(component_config)

    tk.train(TrainingData(training_examples=examples), supervised_embeddings_config)

    assert examples[0].data.get(TOKENS_NAMES[TEXT])[0].text == "Any"
    assert examples[0].data.get(TOKENS_NAMES[TEXT])[1].text == "Mexican"
    assert examples[0].data.get(TOKENS_NAMES[TEXT])[2].text == "restaurant"
    assert examples[0].data.get(TOKENS_NAMES[TEXT])[3].text == "will"
    assert examples[0].data.get(TOKENS_NAMES[TEXT])[4].text == "do"
    assert examples[1].data.get(TOKENS_NAMES[TEXT])[0].text == "I"
    assert examples[1].data.get(TOKENS_NAMES[TEXT])[1].text == "want"
    assert examples[1].data.get(TOKENS_NAMES[TEXT])[2].text == "Tacos"
    assert examples[2].data.get(TOKENS_NAMES[ACTION_NAME])[0].text == "action"
    assert examples[2].data.get(TOKENS_NAMES[ACTION_NAME])[1].text == "restart"
    assert examples[2].data.get(TOKENS_NAMES[TEXT])[0].text == "action_restart"
    assert examples[2].data.get(TOKENS_NAMES[ACTION_TEXT]) is None
    assert examples[3].data.get(TOKENS_NAMES[ACTION_TEXT])[0].text == "Where"
    assert examples[3].data.get(TOKENS_NAMES[ACTION_TEXT])[1].text == "are"
    assert examples[3].data.get(TOKENS_NAMES[ACTION_TEXT])[2].text == "you"
    assert examples[3].data.get(TOKENS_NAMES[ACTION_TEXT])[3].text == "going"


def test_whitespace_does_not_throw_error():
    import rasa.utils.io as io_utils

    texts = io_utils.read_json_file("data/test_tokenizers/naughty_strings.json")

    tk = WhitespaceTokenizer()

    for text in texts:
        tk.tokenize(Message.build(text=text), attribute=TEXT)


@pytest.mark.parametrize("language, error", [("en", False), ("zh", True)])
def test_whitespace_language_suuport(language, error, component_builder):
    config = RasaNLUModelConfig(
        {"language": language, "pipeline": [{"name": "WhitespaceTokenizer"}]}
    )

    if error:
        with pytest.raises(UnsupportedLanguageError):
            component_builder.create_component({"name": "WhitespaceTokenizer"}, config)
    else:
        component_builder.create_component({"name": "WhitespaceTokenizer"}, config)


def test_whitespace_processing_with_attribute(
    supervised_embeddings_config: RasaNLUModelConfig,
):
    message = Message(
        data={
            TEXT: "Any Mexican restaurant will do",
            "intent": "restaurant_search",
            "entities": [
                {"start": 4, "end": 11, "value": "Mexican", "entity": "cuisine"}
            ],
        },
    )
    expected_tokens_intent = ["restaurant_search"]
    expected_tokens_text = ["Any", "Mexican", "restaurant", "will", "do"]
    component_config = {"case_sensitive": False}
    tk = WhitespaceTokenizer(component_config)
    tk.process(message)
    tokens_intent = message.get(TOKENS_NAMES[INTENT])
    tk.process(message)
    tokens_text = message.get(TOKENS_NAMES[TEXT])
    assert [t.text for t in tokens_intent] == expected_tokens_intent
    assert [t.text for t in tokens_text] == expected_tokens_text

    message = Message(
        data={
            TEXT: "Where are you going?",
            ACTION_NAME: "Where are you going?",
            ACTION_TEXT: "Where are you going?",
        },
    )
    expected_action_tokens_text = ["Where", "are", "you", "going"]

    component_config = {"case_sensitive": False}
    tk = WhitespaceTokenizer(component_config)
    tk.process(message)
    tokens_action_text = message.get(TOKENS_NAMES[ACTION_TEXT])
    tk.process(message)
    tokens_text = message.get(TOKENS_NAMES[TEXT])
    assert [t.text for t in tokens_action_text] == expected_action_tokens_text
    assert [t.text for t in tokens_text] == expected_action_tokens_text
