from enum import Enum
from typing import Any, Optional
from dataclasses import dataclass


class EventType(Enum):
    """Standard event types emitted by visualizer plugins."""
    
    NODE_HOVER = "node-hover"
    NODE_HOVER_END = "node-hover-end"
    NODE_SELECT = "node-select"
    VIEWPORT_CHANGE = "viewport-change"
    LAYOUT_COMPLETE = "layout-complete"


@dataclass
class VisualizerEvent:
    """
    Base class for events emitted by visualizer plugins.
    
    Attributes:
        type: The type of event (from EventType enum)
        data: Event-specific payload
    """
    type: EventType
    data: dict[str, Any]
    
    def to_dict(self) -> dict:
        """Convert event to dictionary for serialization."""
        return {
            "type": self.type.value,
            "data": self.data
        }


@dataclass
class NodeEvent(VisualizerEvent):
    """Event related to node interaction (hover, select, etc.)."""
    
    @classmethod
    def hover(cls, node_id: str) -> "NodeEvent":
        return cls(
            type=EventType.NODE_HOVER,
            data={"nodeId": node_id}
        )
    
    @classmethod
    def hover_end(cls, node_id: str) -> "NodeEvent":
        return cls(
            type=EventType.NODE_HOVER_END,
            data={"nodeId": node_id}
        )
    
    @classmethod
    def select(cls, node_id: str) -> "NodeEvent":
        return cls(
            type=EventType.NODE_SELECT,
            data={"nodeId": node_id}
        )


@dataclass
class ViewportEvent(VisualizerEvent):
    """Event related to viewport changes (zoom, pan)."""
    
    @classmethod
    def change(cls, x: float, y: float, scale: float, 
               width: Optional[int] = None, height: Optional[int] = None) -> "ViewportEvent":
        data = {
            "transform": {"x": x, "y": y, "k": scale}
        }
        if width is not None:
            data["width"] = width
        if height is not None:
            data["height"] = height
        return cls(
            type=EventType.VIEWPORT_CHANGE,
            data=data
        )
