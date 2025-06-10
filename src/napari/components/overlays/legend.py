"""Legend overlay for napari."""

import numpy as np

from napari._pydantic_compat import Field
from napari.components._viewer_constants import Alignment
from napari.components.overlays.base import CanvasOverlay
from napari.utils.color import ColorValue
from napari.utils.events import EventedModel


class LegendItem(EventedModel):
    """Legend item.

    Attributes
    ----------
    text : str
        The text to be displayed in the legend item.
    color : ColorValue | Colormap
        Color of the legend item.
    """

    text: str = ''
    color: ColorValue = Field(
        default_factory=lambda: ColorValue((0.5, 0.5, 0.5, 1.0))
    )


class LegendOverlay(CanvasOverlay):
    """Label model to display arbitrary text in the canvas

    Attributes
    ----------
    align: Alignment
        Determines how the legend items are displayed.
    font_size : float
        The font size (in points) of the text.
    items : list[LegendItem]
        List of items in the legend. Each item has a text and a color.
    box : bool
        If background box is visible or not.
    box_color : Optional[str | array-like]
        Background box color.
        See ``ColorValue.validate`` for supported values.
    position : CanvasPosition
        The position of the overlay in the canvas.
    visible : bool
        If the overlay is visible or not.
    opacity : float
        The opacity of the overlay. 0 is fully transparent.
    order : int
        The rendering order of the overlay: lower numbers get rendered first.
    """

    align: Alignment = Alignment.ROW
    font_size: float = 10
    items: list[LegendItem] = Field(default_factory=list)
    box: bool = False
    box_color: ColorValue = Field(
        default_factory=lambda: ColorValue([0, 0, 0, 0.6])
    )

    def text(self, reverse: bool = False) -> np.ndarray:
        """Get the text of the legend items."""
        if not self.items:
            return ''
        array = np.array([item.text for item in self.items])
        return array if not reverse else array[::-1]

    def color(self, reverse=True) -> None | np.ndarray:
        """Get the color of the legend items."""
        if not self.items:
            return None
        array = np.array([item.color for item in self.items], dtype=np.float32)
        return array if not reverse else array[::-1]

    def add(self, text: str, color: ColorValue):
        """Add a legend item to the overlay.

        Parameters
        ----------
        text : str
            The text to be displayed in the legend item.
        color : ColorValue
            The color of the legend item.
        """
        item = LegendItem(text=text, color=color)
        self.items.append(item)
        self.events.items()

    def insert(self, index: int, text: str, color: ColorValue):
        """Insert a legend item at a specific index in the overlay.

        Parameters
        ----------
        index : int
            The index at which to insert the legend item.
        text : str
            The text to be displayed in the legend item.
        color : ColorValue
            The color of the legend item.
        """
        item = LegendItem(text=text, color=color)
        self.items.insert(index, item)
        self.events.items()

    def remove(self, item: str | LegendItem):
        """Remove a legend item from the overlay.

        Parameters
        ----------
        item : str | LegendItem
            The legend item to be removed. Can be either the text of the item
            or the item itself.
        """
        if isinstance(item, str):
            item = next((i for i in self.items if i.text == item), None)
        if item in self.items:
            self.items.remove(item)
            self.events.items()

    def clear(self):
        """Clear all legend items from the overlay."""
        self.items.clear()
        self.events.items()
