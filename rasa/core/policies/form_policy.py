import logging
from typing import List, Dict, Text, Optional, Any, Union, Tuple

from rasa.constants import DOCS_URL_MIGRATION_GUIDE
from rasa.core.actions.action import ACTION_LISTEN_NAME
from rasa.core.domain import Domain, State
from rasa.core.events import FormValidation
from rasa.core.featurizers.tracker_featurizers import TrackerFeaturizer
from rasa.core.interpreter import NaturalLanguageInterpreter
from rasa.core.policies.memoization import MemoizationPolicy
from rasa.core.trackers import DialogueStateTracker
from rasa.core.constants import (
    FORM_POLICY_PRIORITY,
    PREVIOUS_ACTION,
    ACTIVE_LOOP,
    LOOP_REJECTED,
    LOOP_NAME,
)
from rasa.nlu.constants import ACTION_NAME

from rasa.utils import common as common_utils


logger = logging.getLogger(__name__)


class FormPolicy(MemoizationPolicy):
    """Policy which handles prediction of Forms"""

    ENABLE_FEATURE_STRING_COMPRESSION = True

    def __init__(
        self,
        featurizer: Optional[TrackerFeaturizer] = None,
        priority: int = FORM_POLICY_PRIORITY,
        lookup: Optional[Dict] = None,
    ) -> None:

        # max history is set to 2 in order to capture
        # previous meaningful action before action listen
        super().__init__(
            featurizer=featurizer, priority=priority, max_history=2, lookup=lookup
        )

        common_utils.raise_deprecation_warning(
            f"'{FormPolicy.__name__}' is deprecated and will be removed in "
            "in the future. It is recommended to use the 'RulePolicy' instead.",
            docs=DOCS_URL_MIGRATION_GUIDE,
        )

    @staticmethod
    def _get_active_form_name(
        state: State,
    ) -> Optional[Union[Text, Tuple[Union[float, Text]]]]:
        return state.get(ACTIVE_LOOP, {}).get(LOOP_NAME)

    @staticmethod
    def _prev_action_listen_in_state(state: State) -> bool:
        prev_action_name = state.get(PREVIOUS_ACTION, {}).get(ACTION_NAME)
        return prev_action_name == ACTION_LISTEN_NAME

    @staticmethod
    def _modified_states(states: List[State]) -> List[State]:
        """Modifies the states to create feature keys for form unhappy path conditions.

        Args:
            states: a representation of a tracker
                as a list of dictionaries containing features

        Returns:
            modified states
        """
        if len(states) == 1 or states[0] == {}:
            action_before_listen = {}
        else:
            action_before_listen = {PREVIOUS_ACTION: states[0][PREVIOUS_ACTION]}

        return [action_before_listen, states[-1]]

    # pytype: disable=bad-return-type
    def _create_lookup_from_states(
        self,
        trackers_as_states: List[List[State]],
        trackers_as_actions: List[List[Text]],
    ) -> Dict[Text, Text]:
        """Add states to lookup dict"""
        lookup = {}
        for states in trackers_as_states:
            active_form = self._get_active_form_name(states[-1])
            if active_form and self._prev_action_listen_in_state(states[-1]):
                # modify the states
                states = self._modified_states(states)
                feature_key = self._create_feature_key(states)
                # even if there are two identical feature keys
                # their form will be the same
                # because of `active_form_...` feature
                lookup[feature_key] = active_form
        return lookup

    # pytype: enable=bad-return-type

    def recall(
        self, states: List[State], tracker: DialogueStateTracker, domain: Domain
    ) -> Optional[Text]:
        # modify the states
        return self._recall_states(self._modified_states(states))

    def state_is_unhappy(self, tracker: DialogueStateTracker, domain: Domain) -> bool:
        # since it is assumed that training stories contain
        # only unhappy paths, notify the form that
        # it should not be validated if predicted by other policy
        tracker_as_states = self.featurizer.prediction_states([tracker], domain)
        states = tracker_as_states[0]

        memorized_form = self.recall(states, tracker, domain)

        state_is_unhappy = (
            memorized_form is not None and memorized_form == tracker.active_loop_name
        )

        if state_is_unhappy:
            logger.debug(
                "There is a memorized tracker state {}, "
                "added `FormValidation(False)` event"
                "".format(self._modified_states(states))
            )

        return state_is_unhappy

    def predict_action_probabilities(
        self,
        tracker: DialogueStateTracker,
        domain: Domain,
        interpreter: NaturalLanguageInterpreter,
        **kwargs: Any,
    ) -> List[float]:
        """Predicts the corresponding form action if there is an active form"""
        result = self._default_predictions(domain)

        if tracker.active_loop_name:
            logger.debug(
                "There is an active form '{}'".format(tracker.active_loop_name)
            )
            if tracker.latest_action_name == ACTION_LISTEN_NAME:
                # predict form action after user utterance

                if tracker.active_loop.get(LOOP_REJECTED):
                    if self.state_is_unhappy(tracker, domain):
                        tracker.update(FormValidation(False))
                        return result

                result = self._prediction_result(
                    tracker.active_loop_name, tracker, domain
                )

            elif tracker.latest_action_name == tracker.active_loop_name:
                # predict action_listen after form action
                result = self._prediction_result(ACTION_LISTEN_NAME, tracker, domain)

        else:
            logger.debug("There is no active form")

        return result
