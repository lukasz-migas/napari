"""Legend overlay for napari."""

import numpy as np

from napari._vispy.overlays.base import ViewerOverlayMixin, VispyCanvasOverlay
from napari._vispy.visuals.legend import Legend
from napari.components._viewer_constants import (
    Alignment as A,
    CanvasPosition as CP,
)
from napari.components.overlays import LegendOverlay


class VispyLegendOverlay(ViewerOverlayMixin, VispyCanvasOverlay):
    """Scale bar in world coordinates."""

    def __init__(self, *, viewer, overlay: LegendOverlay, parent=None) -> None:
        super().__init__(
            node=Legend(), viewer=viewer, overlay=overlay, parent=parent
        )
        self.overlay.events.box.connect(self._on_box_change)
        self.overlay.events.box_color.connect(self._on_box_change)
        self.overlay.events.font_size.connect(self._on_text_change)
        self.overlay.events.position.connect(self._on_text_change)
        self.overlay.events.align.connect(self._on_text_change)
        self.overlay.events.items.connect(self._on_text_change)
        self.node.canvas.events.resize.connect(self._on_text_change)

        self.reset()

    def _on_box_change(self):
        self.node.box.visible = self.overlay.box
        self.node.box.color = self.overlay.box_color

    def _on_position_change(self, event=None):
        """Update position of the overlay."""
        if self.node.canvas is None:
            return
        # always in the top-left corner of the canvas, the rest is handled by the _on_text_change
        self.node.transform.translate = [0, 0, 0, 0]
        scale = abs(self.node.transform.scale[0])
        self.node.transform.scale = [scale, 1, 1, 1]
        self._on_text_change()

    def _on_text_change(self, event=None):
        """Update text information"""
        # update the dpi scale factor to account for screen dpi
        # because vispy scales pixel height of text by screen dpi
        dpi_scale_factor = 96 / 72
        if self.node.text.transforms.dpi:
            # use 96 as the napari reference dpi for historical reasons
            dpi_scale_factor = 96 / self.node.text.transforms.dpi

        self.node.text.font_size = text_factor = (
            self.overlay.font_size * dpi_scale_factor
        )
        # positioning in the box uses the center of the box
        # need to adjust the y_size to be half the size of the current box height
        self.y_size = self.node.box.height / 2
        center, width, height = update_text(self, text_factor)
        if width is not None and height is not None:
            self.node.box.center = center
            self.node.box.width = width
            self.node.box.height = height

    def reset(self):
        """Reset the overlay to its initial state."""
        super().reset()
        self._on_box_change()
        self._on_text_change()
        self._on_position_change()


ANCHOR_X_MAP = {
    CP.TOP_LEFT: 'left',
    CP.TOP_CENTER: 'center',
    CP.TOP_RIGHT: 'right',
    CP.BOTTOM_LEFT: 'left',
    CP.BOTTOM_CENTER: 'center',
    CP.BOTTOM_RIGHT: 'right',
}
ANCHOR_Y_MAP = {
    CP.TOP_LEFT: 'top',
    CP.TOP_CENTER: 'top',
    CP.TOP_RIGHT: 'top',
    CP.BOTTOM_LEFT: 'bottom',
    CP.BOTTOM_CENTER: 'bottom',
    CP.BOTTOM_RIGHT: 'bottom',
}
OFFSET_X_MAP = {
    CP.TOP_LEFT: 20,
    CP.TOP_CENTER: 0,
    CP.TOP_RIGHT: 20,
    CP.BOTTOM_LEFT: 20,
    CP.BOTTOM_CENTER: 0,
    CP.BOTTOM_RIGHT: 20,
}
OFFSET_Y_MAP = {
    CP.TOP_LEFT: 20,
    CP.TOP_CENTER: 20,
    CP.TOP_RIGHT: 20,
    CP.BOTTOM_LEFT: 20,
    CP.BOTTOM_CENTER: 20,
    CP.BOTTOM_RIGHT: 20,
}


def update_text(
    visual: VispyLegendOverlay, text_factor: float
) -> tuple[tuple[int, int], int, int] | None:
    """Get position of the legend overlay."""
    from operator import add, sub

    ovr: LegendOverlay = visual.overlay
    if ovr.visible_count() == 0:
        visual.node.text.text = ovr.text()
        visual.node.text.color = ovr.color()
        visual.node.text.pos = np.array([[0, 0]], dtype=np.float32)
        return None, None, None

    anchor_x = ANCHOR_X_MAP[ovr.position]
    anchor_y = ANCHOR_Y_MAP[ovr.position]
    offset_x = OFFSET_X_MAP[ovr.position]
    offset_y = OFFSET_Y_MAP[ovr.position]

    max_width, max_height = visual.node.canvas.size
    width = text_factor * 1.01
    height = text_factor * 1.75

    # let's calculate any offsets and anchors
    start_x, start_y, x_operator, y_operator = offset_x, offset_y, add, add
    is_row = ovr.align in [A.ROW, A.ROW_SPLIT]
    is_col = ovr.align in [A.COLUMN, A.COLUMN_SPLIT]

    # handle column alignment
    if is_col and ovr.position == CP.TOP_LEFT:
        start_x, start_y = offset_x, offset_y
        x_operator = y_operator = add
    elif is_col and ovr.position == CP.TOP_RIGHT:
        start_x, start_y = max_width, offset_y
        x_operator, y_operator = sub, add
    elif is_col and ovr.position == CP.TOP_CENTER:
        start_x = max_width / 2
        start_y = offset_y
        x_operator, y_operator = sub, add
    elif is_col and ovr.position == CP.BOTTOM_LEFT:
        start_x, start_y = offset_x, max_height - offset_y
        x_operator, y_operator = add, sub
    elif is_col and ovr.position == CP.BOTTOM_RIGHT:
        start_x, start_y = max_width, max_height - offset_y
        x_operator, y_operator = sub, sub
    elif is_col and ovr.position == CP.BOTTOM_CENTER:
        start_x = max_width / 2
        start_y = max_height - offset_y
        x_operator, y_operator = sub, sub
    # handle row alignment
    elif is_row and ovr.position == CP.TOP_LEFT:
        start_x, start_y = offset_x, offset_y + height
        x_operator = y_operator = add
    elif is_row and ovr.position == CP.TOP_RIGHT:
        start_x, start_y = max_width - offset_x, offset_y + height
        x_operator, y_operator = sub, add
    elif is_row and ovr.position == CP.TOP_CENTER:
        estimate_width, _ = _estimate_width_and_height(
            ovr.align, ovr.text(), width, height, max_width
        )
        start_x = max_width / 2 - estimate_width / 2
        start_y = offset_y + height
        x_operator, y_operator = sub, add
    elif is_row and ovr.position == CP.BOTTOM_LEFT:
        start_x, start_y = offset_x, max_height - offset_y - height
        x_operator, y_operator = add, sub
    elif is_row and ovr.position == CP.BOTTOM_RIGHT:
        start_x, start_y = max_width, max_height - offset_y - height
        x_operator, y_operator = sub, sub
    elif is_row and ovr.position == CP.BOTTOM_CENTER:
        estimate_width, estimate_height = _estimate_width_and_height(
            ovr.align, ovr.text(), width, height, max_width
        )
        start_x = max_width / 2 - estimate_width / 2

        start_y = max_height - offset_y - estimate_height
        x_operator, y_operator = add, sub

    # let's keep the original start_x and start_y for the next row
    start_x_ = start_x
    start_y_ = start_y

    # some padding and height calculations
    max_text_width, max_text_height, previous = 0, height, 0

    # calculate the positions of the text
    texts = list(ovr.text())
    positions = np.empty((len(texts), 2), dtype=np.float32)
    previous, padding = 0.0, 0
    for i, text in enumerate(texts):
        n = len(text)  # number of characters in the text
        padding = calculate_padding(text)
        max_text_width = max(max_text_height, n * width)

        # single row of legend items
        if ovr.align == A.ROW:
            start_x = x_operator(start_x, previous)
            previous = _estimate_text_width(text, padding, width)
        # potentially multiple row of legend items
        elif ovr.align == A.ROW_SPLIT:
            start_x = x_operator(start_x, previous)
            if (
                x_operator(start_x, previous) > max_width
                or x_operator(start_x, previous) < 0
            ):
                start_x = x_operator(start_x_, 0)
                start_y = y_operator(start_y, height)
            previous = _estimate_text_width(text, padding, width)

        # single column of legend items
        elif ovr.align == A.COLUMN:
            start_y = y_operator(start_y, height)
        # potentially multiple column of legend items
        elif ovr.align == A.COLUMN_SPLIT:
            start_y = y_operator(start_y, height)
            if start_y < 0 or start_y + height > max_height:
                start_y = y_operator(start_y_, height)
                start_x = x_operator(
                    x_operator(start_x, max_text_width), width
                )
        else:
            raise ValueError(
                f'Unknown alignment {ovr.align} for legend overlay.'
            )
        positions[i] = (start_x, start_y)

    # actually update the text visual
    visual.node.text.text = np.array(texts)
    visual.node.text.color = ovr.color()
    visual.node.text.pos = np.array(positions, dtype=np.float32)
    visual.node.text.anchors = (anchor_x, anchor_y)

    if ovr.box:
        positions = np.abs(positions)
        mins = positions.min(axis=0)
        maxs = positions.max(axis=0)
        box_width, box_height = maxs - mins
        # if splitting across row(s), center(x) should be (min + max) / 2 and center(y) should be
        if ovr.align == A.ROW:
            box_center_x = (
                x_operator((mins[0] + maxs[0] - padding), previous) / 2
            )
            box_center_y = y_operator(
                start_y_, (-height / 1.5 if anchor_y == 'top' else -height / 2)
            )
        elif ovr.align == A.COLUMN:
            box_center_x = x_operator(start_x_, max_text_width / 2)
            box_center_y = (
                mins[1]
                + maxs[1]
                + (-height / 1.5 if anchor_y == 'top' else -height / 2)
            ) / 2
            box_height = box_height + height
            box_width = max_text_width

        box_center = (box_center_x, box_center_y)
        box_width = box_width + previous or max_text_width
        box_height = box_height or height
        # print(positions, max_text_width)
        # print('??', box_center, width, height)
        return box_center, box_width, box_height
    return (0, 0), 1, 1


def _estimate_text_width(text: str, padding: int, text_width: float) -> float:
    """Estimate the width of the text."""
    # This is a very rough estimate, as we don't have access to the actual font metrics.
    # We assume an average character width of 7 pixels for normal characters,
    # and 4 pixels for 'i' and 'l', and 10 pixels for 'm', 'w', and 'g'.
    return len(text) * text_width + padding


def _estimate_width_and_height(
    alignment: A,
    texts: list[str],
    width: float,
    height: float,
    max_width: float,
) -> tuple[float, float]:
    """Estimate the width of the text based on the characters."""
    if len(texts) == 0:
        return 0, height
    estimated_width = sum(
        _estimate_text_width(text, calculate_padding(text), width)
        for text in texts
    )
    if alignment == A.ROW:
        return estimated_width, height
    if alignment == A.ROW_SPLIT and estimated_width > max_width:
        ratio = np.ceil(estimated_width / width)
        return max_width, height * ratio
    return 0, height


def calculate_padding(text: str) -> int:
    """Calculate padding for particular text.

    Certain characters are wider than others, so we need to
    calculate the padding based on the text length.
    """
    padding = 0
    for char in text.lower():
        if char in 'il':
            padding += 1
        elif char in 'gmw':
            padding += 3
    return padding
