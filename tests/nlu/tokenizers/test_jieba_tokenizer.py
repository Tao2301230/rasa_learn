from pathlib import Path
from unittest.mock import patch

from rasa.nlu.tokenizers.jieba_tokenizer import JiebaTokenizer

import pytest

from rasa.nlu.training_data import Message, TrainingData
from rasa.nlu.constants import TEXT, INTENT, TOKENS_NAMES


@pytest.mark.parametrize(
    "text, expected_tokens, expected_indices",
    [
        (
            "我想去吃兰州拉面",
            ["我", "想", "去", "吃", "兰州", "拉面"],
            [(0, 1), (1, 2), (2, 3), (3, 4), (4, 6), (6, 8)],
        ),
        (
            "Micheal你好吗？",
            ["Micheal", "你好", "吗", "？"],
            [(0, 7), (7, 9), (9, 10), (10, 11)],
        ),
    ],
)
def test_jieba(text, expected_tokens, expected_indices):
    tk = JiebaTokenizer()

    tokens = tk.tokenize(Message(data={TEXT: text}), attribute=TEXT)

    assert [t.text for t in tokens] == expected_tokens
    assert [t.start for t in tokens] == [i[0] for i in expected_indices]
    assert [t.end for t in tokens] == [i[1] for i in expected_indices]


def test_jieba_load_dictionary(tmp_path: Path):
    dictionary_path = str(tmp_path)

    component_config = {"dictionary_path": dictionary_path}

    with patch.object(
        JiebaTokenizer, "load_custom_dictionary", return_value=None
    ) as mock_method:
        tk = JiebaTokenizer(component_config)
        tk.tokenize(Message(data={TEXT: ""}), attribute=TEXT)

    mock_method.assert_called_once_with(dictionary_path)


@pytest.mark.parametrize(
    "text, expected_tokens",
    [
        ("Forecast_for_LUNCH", ["Forecast_for_LUNCH"]),
        ("Forecast for LUNCH", ["Forecast for LUNCH"]),
    ],
)
def test_custom_intent_symbol(text, expected_tokens):
    component_config = {"intent_tokenization_flag": True, "intent_split_symbol": "+"}

    tk = JiebaTokenizer(component_config)

    message = Message(data={TEXT: text})
    message.set(INTENT, text)

    tk.train(TrainingData([message]))

    assert [t.text for t in message.get(TOKENS_NAMES[INTENT])] == expected_tokens
