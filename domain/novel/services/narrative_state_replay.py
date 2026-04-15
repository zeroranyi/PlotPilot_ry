"""Narrative state replay service - pure functions for event replay."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def replay_entity_state(base_attrs: dict[str, Any], events: list[dict]) -> dict[str, Any]:
    """
    Replay events to compute entity dynamic attributes.

    This is a pure function that applies a sequence of events to a base attribute
    dictionary, returning the final state after all mutations are applied.

    Args:
        base_attrs: Base attributes dictionary (not modified)
        events: List of event dictionaries, each containing a "mutations" list

    Returns:
        New dictionary with final state after applying all mutations

    Mutation actions:
        - "add": Set attribute to value (overwrites existing)
        - "remove": Delete attribute (if exists)
        - Unknown actions are logged and ignored
    """
    # Create a copy to avoid mutating the input
    state = base_attrs.copy()

    for event in events:
        mutations = event.get("mutations", [])
        for mutation in mutations:
            attribute = mutation.get("attribute")
            action = mutation.get("action")
            value = mutation.get("value")

            if action == "add":
                state[attribute] = value
            elif action == "remove":
                # Remove attribute if it exists, no error if not
                state.pop(attribute, None)
            else:
                # Log unknown actions at debug level and ignore
                logger.debug(
                    f"Unknown mutation action '{action}' for attribute '{attribute}', ignoring"
                )

    return state
