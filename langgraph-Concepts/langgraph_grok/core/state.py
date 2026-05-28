"""Reusable state schemas and reducers.

Factoring state out of individual graphs is good practice: the schema is the
contract for your whole application, and several graphs often share one.
"""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class ChatState(TypedDict):
    """Standard conversational state.

    The `add_messages` reducer appends new messages to the history (and
    de-duplicates by message id) instead of overwriting it. This is the same
    shape as LangGraph's built-in MessagesState.
    """

    messages: Annotated[list, add_messages]


class AccumulatingState(TypedDict):
    """A state whose `items` list grows across nodes (and across parallel
    branches) thanks to the operator.add reducer. Useful for map-reduce style
    graphs where several nodes each contribute to a shared list.
    """

    items: Annotated[list[str], operator.add]
