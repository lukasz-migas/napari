"""Legend overlay for napari."""

import numpy as np

from napari._vispy.overlays.base import ViewerOverlayMixin, VispyCanvasOverlay
from napari._vispy.visuals.legend import Legend
from napari.components._viewer_constants import (
    CanvasPosition as CP,
    LegendAlignment as LA,
)
from napari.components.overlays import LegendOverlay


class VispyLegendOverlay(ViewerOverlayMixin, VispyCanvasOverlay):
    """Scale bar in world coordinates."""

    def __init__(self, *, viewer, overlay: LegendOverlay, parent=None) -> None:
        super().__init__(
            node=Legend(), viewer=viewer, overlay=overlay, parent=parent
        )
        self.node.canvas.events.resize.connect(self._on_text_change)
        self.overlay.events.box.connect(self._on_box_change)
        self.overlay.events.box_color.connect(self._on_box_change)
        self.overlay.events.font_size.connect(self._on_text_change)
        self.overlay.events.position.connect(self._on_text_change)
        self.overlay.events.align.connect(self._on_text_change)
        self.overlay.events.items.connect(self._on_text_change)

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
        update_text_and_box(self, text_factor)

    def reset(self):
        """Reset the overlay to its initial state."""
        super().reset()
        self._on_box_change()
        self._on_text_change()
        self._on_position_change()


ANCHOR_X_MAP = {
    CP.TOP_LEFT: 'left',
    CP.TOP_CENTER: 'center',
    (CP.TOP_CENTER, LA.ROW): 'left',
    (CP.TOP_CENTER, LA.ROW_SPLIT): 'left',
    CP.TOP_RIGHT: 'right',
    CP.BOTTOM_LEFT: 'left',
    CP.BOTTOM_CENTER: 'center',
    (CP.BOTTOM_CENTER, LA.ROW): 'left',
    (CP.BOTTOM_CENTER, LA.ROW_SPLIT): 'left',
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
OFFSET_X_MAP = {CP.TOP_CENTER: 0, CP.BOTTOM_CENTER: 0}


def update_text_and_box(
    visual: VispyLegendOverlay, text_factor: float
) -> None:
    """Get position of the legend overlay."""
    from operator import add, sub

    ovr: LegendOverlay = visual.overlay
    if ovr.visible_count() == 0:
        visual.node.text.text = ovr.text()
        visual.node.text.color = ovr.color()
        visual.node.text.pos = np.array([[0, 0]], dtype=np.float32)
        return

    # get anchor positions and offsets - first try a complex combination of position and alignment
    # otherwise fall back to the position only
    anchor_x = ANCHOR_X_MAP.get(
        (ovr.position, ovr.align), ANCHOR_X_MAP[ovr.position]
    )
    anchor_y = ANCHOR_Y_MAP[ovr.position]
    offset_x = OFFSET_X_MAP.get(ovr.position, 20)
    offset_y = 20

    max_width, max_height = visual.node.canvas.size
    half_width = max_width / 2
    width = text_factor * 1.01  # 1.01 to account for small amounts of padding
    height = text_factor * 1.75

    # let's calculate any offsets and anchors
    start_x, start_y, x_operator, y_operator = offset_x, offset_y, add, add
    is_row = ovr.align in [LA.ROW, LA.ROW_SPLIT]
    is_col = ovr.align in [LA.COLUMN, LA.COLUMN_SPLIT]

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
        x_operator, y_operator = add, sub

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
        start_x = offset_x + estimate_width * 0.25
        start_y = offset_y + height
        x_operator, y_operator = add, add
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
        start_x = offset_x + estimate_width * 0.25
        start_y = max_height - offset_y - estimate_height
        x_operator, y_operator = add, sub

    # let's keep the original start_x and start_y for the next row
    start_x_ = start_x
    start_y_ = start_y

    # some padding and height calculations
    max_text_width, previous = 0, 0

    # calculate the positions of the text
    texts = list(ovr.text())
    positions = np.empty((len(texts), 2), dtype=np.float32)
    previous, padding, n_row, n_col = 0.0, 0, 1, 1
    for i, text in enumerate(texts):
        padding = calculate_padding(text)
        text_width = _estimate_text_width(text, padding, width)
        max_text_width = max(max_text_width, text_width)

        # single row of legend items
        if ovr.align == LA.ROW:
            start_x = x_operator(start_x, previous)  # add previous text width
            previous = text_width

        # potentially multiple rows of legend items
        elif ovr.align == LA.ROW_SPLIT:
            start_x = x_operator(start_x, previous)  # add previous text width
            if (
                x_operator(start_x, text_width) > max_width
                or x_operator(start_x, text_width) < 0
            ):
                start_x = start_x_
                start_y = y_operator(start_y, height)
                n_row += 1
            previous = text_width

        # single column of legend items
        elif ovr.align == LA.COLUMN:
            start_y = y_operator(start_y, height)
        # potentially multiple columns of legend items
        elif ovr.align == LA.COLUMN_SPLIT:
            start_y = y_operator(start_y, height)
            if start_y < 0 or start_y + height > max_height:
                start_y = y_operator(start_y_, height)
                start_x = x_operator(
                    x_operator(start_x, max_text_width), width
                )
                n_col += 1
        else:
            raise ValueError(
                f'Unknown alignment {ovr.align} for legend overlay.'
            )
        positions[i] = (start_x, start_y)

    # check whether the center of the row is not centered around the middle of the canvas
    if is_row and ovr.position in [CP.TOP_CENTER, CP.BOTTOM_CENTER]:
        abs_positions = np.abs(positions)
        abs_mins = abs_positions.min(axis=0)
        abs_maxs = abs_positions.max(axis=0)
        x_spread = (abs_maxs[0] + previous) - abs_mins[0]
        if abs(half_width - x_spread / 2) > 50:
            positions[:, 0] += abs(x_spread - half_width) / 2

    # for i, t in enumerate(ovr.text()):
    #     print(t, positions[i])

    # actually update the text visuals
    visual.node.text.text = np.array(texts)
    visual.node.text.color = ovr.color()
    visual.node.text.pos = np.array(positions, dtype=np.float32)
    visual.node.text.anchors = (anchor_x, anchor_y)

    # update box visual if it's enabled
    if ovr.box:
        abs_positions = np.abs(positions)
        abs_mins = abs_positions.min(axis=0)
        abs_maxs = abs_positions.max(axis=0)
        box_center_x, box_center_y = 0, 0
        box_width, box_height = abs_maxs - abs_mins

        # if splitting across row(s), center(x) should be (min + max) / 2 and center(y) should be
        if ovr.align in [LA.ROW, LA.ROW_SPLIT]:
            box_center_x = (
                x_operator((abs_mins[0] + abs_maxs[0] - padding), previous) / 2
            )
            box_center_y = y_operator(
                start_y_,
                (
                    -(height * n_row) / 1.5
                    if anchor_y == 'top'
                    else -(height * n_row) / 2
                ),
            )
        elif ovr.align == LA.COLUMN:
            box_center_x = x_operator(start_x_, max_text_width / 2)
            box_center_y = (
                abs_mins[1]
                + abs_maxs[1]
                + (-height / 1.5 if anchor_y == 'top' else -height / 2)
            ) / 2
            box_height = box_height + height
            box_width = max_text_width

        box_center = (box_center_x, box_center_y)
        box_width = box_width + previous or max_text_width
        box_height = box_height or height
        visual.node.box.center = box_center
        visual.node.box.width = box_width
        visual.node.box.height = box_height


def _estimate_text_width(text: str, padding: int, text_width: float) -> float:
    """Estimate the width of the text."""
    # This is a very rough estimate, as we don't have access to the actual font metrics.
    # We assume an average character width of 7 pixels for normal characters,
    # and 4 pixels for 'i' and 'l', and 10 pixels for 'm', 'w', and 'g'.
    return len(text) * text_width + padding


def _estimate_width_and_height(
    alignment: LA,
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
    if alignment == LA.ROW:
        return estimated_width, height
    if alignment == LA.ROW_SPLIT and estimated_width > max_width:
        ratio = round(estimated_width / max_width)
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
