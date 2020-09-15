from typing import Text, List, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from rasa.core.domain import Domain
    from rasa.core.trackers import DialogueStateTracker
    from rasa.core.training.structures import StoryGraph
    from rasa.importers.importer import TrainingDataImporter


async def extract_rule_data(
    resource_name: Text,
    domain: "Domain",
    use_e2e: bool = False,
    exclusion_percentage: int = None,
) -> "StoryGraph":
    from rasa.core.training import loading
    from rasa.core.training.structures import StoryGraph

    story_steps = await loading.load_data_from_resource(
        resource_name,
        domain,
        use_e2e=use_e2e,
        exclusion_percentage=exclusion_percentage,
    )
    return StoryGraph(story_steps)


async def extract_story_graph(
    resource_name: Text,
    domain: "Domain",
    use_e2e: bool = False,
    exclusion_percentage: Optional[int] = None,
) -> "StoryGraph":
    from rasa.core.training.structures import StoryGraph
    import rasa.core.training.loading as core_loading

    story_steps = await core_loading.load_data_from_resource(
        resource_name,
        domain,
        use_e2e=use_e2e,
        exclusion_percentage=exclusion_percentage,
    )
    return StoryGraph(story_steps)


async def load_data(
    resource_name: Union[Text, "TrainingDataImporter"],
    domain: "Domain",
    remove_duplicates: bool = True,
    unique_last_num_states: Optional[int] = None,
    augmentation_factor: int = 50,
    tracker_limit: Optional[int] = None,
    use_story_concatenation: bool = True,
    debug_plots: bool = False,
    exclusion_percentage: Optional[int] = None,
) -> List["DialogueStateTracker"]:
    """
    Load training data from a resource.

    Args:
        resource_name: resource to load the data from. either a path or an importer
        domain: domain used for loading
        remove_duplicates: should duplicated training examples be removed?
        unique_last_num_states: number of states in a conversation that make the
            a tracker unique (this is used to identify duplicates)
        augmentation_factor:
            by how much should the story training data be augmented
        tracker_limit:
            maximum number of trackers to generate during augmentation
        use_story_concatenation:
            should stories be concatenated when doing data augmentation
        debug_plots:
            generate debug plots during loading
        exclusion_percentage:
            how much data to exclude

    Returns:
        list of loaded trackers
    """
    from rasa.core.training.generator import TrainingDataGenerator
    from rasa.importers.importer import TrainingDataImporter

    if resource_name:
        if isinstance(resource_name, TrainingDataImporter):
            graph = await resource_name.get_stories(
                exclusion_percentage=exclusion_percentage
            )
        else:
            graph = await extract_story_graph(
                resource_name, domain, exclusion_percentage=exclusion_percentage
            )

        g = TrainingDataGenerator(
            graph,
            domain,
            remove_duplicates,
            unique_last_num_states,
            augmentation_factor,
            tracker_limit,
            use_story_concatenation,
            debug_plots,
        )
        return g.generate()
    else:
        return []


def persist_data(trackers: List["DialogueStateTracker"], path: Text) -> None:
    """Dump a list of dialogue trackers in the story format to disk."""

    for t in trackers:
        t.export_stories_to_file(path)
