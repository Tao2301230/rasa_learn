from abc import ABC
from typing import List, TYPE_CHECKING, Text

from rasa.core.actions import Action
from rasa.core.events import Event, ActiveLoop

if TYPE_CHECKING:
    from rasa.core.channels import OutputChannel
    from rasa.core.domain import Domain
    from rasa.core.nlg import NaturalLanguageGenerator
    from rasa.core.trackers import DialogueStateTracker


class LoopAction(Action, ABC):  # pytype: disable=base-class-error
    async def run(
        self,
        output_channel: "OutputChannel",
        nlg: "NaturalLanguageGenerator",
        tracker: "DialogueStateTracker",
        domain: "Domain",
    ) -> List[Event]:
        events = []

        if not await self.is_activated(output_channel, nlg, tracker, domain):
            events += self._default_activation_events()
            events += await self.activate(output_channel, nlg, tracker, domain)

        if not await self.is_done(output_channel, nlg, tracker, domain, events):
            events += await self.do(output_channel, nlg, tracker, domain, events)

        if await self.is_done(output_channel, nlg, tracker, domain, events):
            events += self._default_deactivation_events()
            events += await self.deactivate(
                output_channel, nlg, tracker, domain, events
            )

        return events

    async def is_activated(
        self,
        output_channel: "OutputChannel",
        nlg: "NaturalLanguageGenerator",
        tracker: "DialogueStateTracker",
        domain: "Domain",
    ) -> bool:
        # pytype: disable=attribute-error
        return tracker.active_loop_name == self.name()
        # pytype: enable=attribute-error

    # default implementation checks if form active
    def _default_activation_events(self) -> List[Event]:
        return [ActiveLoop(self.name())]  # pytype: disable=attribute-error

    async def activate(
        self,
        output_channel: "OutputChannel",
        nlg: "NaturalLanguageGenerator",
        tracker: "DialogueStateTracker",
        domain: "Domain",
    ) -> List[Event]:
        # can be overwritten
        return []

    async def do(
        self,
        output_channel: "OutputChannel",
        nlg: "NaturalLanguageGenerator",
        tracker: "DialogueStateTracker",
        domain: "Domain",
        events_so_far: List[Event],
    ) -> List[Event]:
        raise NotImplementedError()

    async def is_done(
        self,
        output_channel: "OutputChannel",
        nlg: "NaturalLanguageGenerator",
        tracker: "DialogueStateTracker",
        domain: "Domain",
        events_so_far: List[Event],
    ) -> bool:
        raise NotImplementedError()

    def _default_deactivation_events(self) -> List[Event]:
        return [ActiveLoop(None)]

    async def deactivate(
        self,
        output_channel: "OutputChannel",
        nlg: "NaturalLanguageGenerator",
        tracker: "DialogueStateTracker",
        domain: "Domain",
        events_so_far: List[Event],
    ) -> List[Event]:
        # can be overwritten
        return []
