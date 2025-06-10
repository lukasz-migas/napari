"""Legend overlay for napari."""

import numpy as np

from napari._vispy.overlays.base import ViewerOverlayMixin, VispyCanvasOverlay
from napari._vispy.visuals.legend import Legend
from napari.components._viewer_constants import Alignment, CanvasPosition
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
        # self.viewer.events.theme.connect(self._on_data_change)

        self.reset()

    def _on_box_change(self):
        self.node.box.visible = self.overlay.box
        self.node.box.color = self.overlay.box_color

    def _on_position_change(self, event=None):
        """Update position of the overlay."""
        if self.node.canvas is None:
            return
        # always in the top-left corner of the canvas, the rest is handled by the _on_text_change
        self.node.transform.translate = [self.x_offset, self.y_offset, 0, 0]
        scale = abs(self.node.transform.scale[0])
        self.node.transform.scale = [scale, 1, 1, 1]
        self._on_text_change()

    def _on_text_change(self, event=None):
        """Update text information"""
        # update the dpi scale factor to account for screen dpi
        # because vispy scales pixel height of text by screen dpi
        dpi_scale_factor = 1
        if self.node.text.transforms.dpi:
            # use 96 as the napari reference dpi for historical reasons
            dpi_scale_factor = 96 / self.node.text.transforms.dpi

        self.node.text.font_size = text_factor = (
            self.overlay.font_size * dpi_scale_factor
        )
        # positioning in the box uses the center of the box
        # need to adjust the y_size to be half the size of the current box height
        self.y_size = self.node.box.height / 2
        update_text(self, text_factor)

    def reset(self):
        """Reset the overlay to its initial state."""
        super().reset()
        self._on_box_change()
        self._on_text_change()
        self._on_position_change()


ANCHOR_X_MAP = {
    CanvasPosition.TOP_LEFT: 'left',
    CanvasPosition.TOP_CENTER: 'center',
    CanvasPosition.TOP_RIGHT: 'right',
    CanvasPosition.BOTTOM_LEFT: 'left',
    CanvasPosition.BOTTOM_CENTER: 'center',
    CanvasPosition.BOTTOM_RIGHT: 'right',
}
ANCHOR_Y_MAP = {
    CanvasPosition.TOP_LEFT: 'top',
    CanvasPosition.TOP_CENTER: 'top',
    CanvasPosition.TOP_RIGHT: 'top',
    CanvasPosition.BOTTOM_LEFT: 'bottom',
    CanvasPosition.BOTTOM_CENTER: 'bottom',
    CanvasPosition.BOTTOM_RIGHT: 'bottom',
}
OFFSET_X_MAP = {
    CanvasPosition.TOP_LEFT: 0,
    CanvasPosition.TOP_CENTER: 0,
    CanvasPosition.TOP_RIGHT: 50,
    CanvasPosition.BOTTOM_LEFT: 0,
    CanvasPosition.BOTTOM_CENTER: 0,
    CanvasPosition.BOTTOM_RIGHT: 50,
}
OFFSET_Y_MAP = {
    CanvasPosition.TOP_LEFT: 20,
    CanvasPosition.TOP_CENTER: 20,
    CanvasPosition.TOP_RIGHT: 20,
    CanvasPosition.BOTTOM_LEFT: 20,
    CanvasPosition.BOTTOM_CENTER: 20,
    CanvasPosition.BOTTOM_RIGHT: 20,
}


def update_text(visual: VispyLegendOverlay, text_factor: float) -> None:
    """Get position of the legend overlay."""
    from operator import add, sub

    overlay = visual.overlay
    if not overlay.items:
        visual.node.text.text = overlay.text()
        visual.node.text.color = overlay.color()
        visual.node.text.pos = np.array([[0, 0]], dtype=np.float32)
        return None

    anchor_x = ANCHOR_X_MAP[overlay.position]
    anchor_y = ANCHOR_Y_MAP[overlay.position]
    offset_x = OFFSET_X_MAP[overlay.position]
    offset_y = OFFSET_Y_MAP[overlay.position]

    max_x, max_y = visual.node.canvas.size

    # let's calculate any offsets and anchors
    reverse = False
    if overlay.position in [
        CanvasPosition.TOP_LEFT,
        CanvasPosition.TOP_CENTER,
        CanvasPosition.TOP_RIGHT,
    ]:
        start_x = offset_x
        start_y = offset_y
        x_operator = y_operator = add
        if overlay.position == CanvasPosition.TOP_RIGHT:
            x_operator = sub
            reverse = overlay.align in [Alignment.ROW, Alignment.ROW_SPLIT]
            start_x = max_x - offset_x

    else:
        start_x = offset_x
        start_y = max_y - offset_y
        x_operator = y_operator = sub
        reverse = overlay.align in [Alignment.COLUMN, Alignment.COLUMN_SPLIT]
        if overlay.position == CanvasPosition.BOTTOM_LEFT:
            x_operator = add
        elif overlay.position == CanvasPosition.BOTTOM_RIGHT:
            start_x = max_x + offset_x

    # let's keep the original start_x and start_y for the next row
    start_x_ = start_x
    start_y_ = start_y

    # some padding and height calculations
    padding = 0  # 1 if len(overlay.text()) > 1 else 0
    width = text_factor * 0.8
    height = text_factor * 1.75
    max_text_width, max_text_height = 0, height

    # calculate the positions of the text
    texts, positions = [], []
    for text in overlay.text(reverse):
        # add text
        texts.append(f'{text}{" " * padding}')
        n = len(texts[-1])  # number of characters in the text
        max_text_width = max(max_text_height, n * width)

        # single row of legend items
        if overlay.align == Alignment.ROW:
            start_x = x_operator(start_x, n * width)
        # potentially multiple row of legend items
        elif overlay.align == Alignment.ROW_SPLIT:
            start_x = x_operator(start_x, n * width)
            if start_x > max_x:
                start_x = x_operator(start_x_, n * width)
                start_y = start_y + height

        # single column of legend items
        elif overlay.align == Alignment.COLUMN:
            start_y = y_operator(start_y, height)
        # potentially multiple column of legend items
        elif overlay.align == Alignment.COLUMN_SPLIT:
            start_y = y_operator(start_y, height)
            if start_y + height > max_y or start_y < 0:
                start_y = y_operator(start_y_, height)
                start_x = x_operator(
                    x_operator(start_x, max_text_width), width
                )
        else:
            raise ValueError(
                f'Unknown alignment {overlay.align} for legend overlay.'
            )
        # print(text, start_x_, start_x, max_x, start_y_, start_y, max_y)
        positions.append((start_x, start_y))
    # print('??', anchor_x, anchor_y, reverse)
    # actually update the text visual
    visual.node.text.text = np.array(texts)
    visual.node.text.color = overlay.color(reverse)
    visual.node.text.pos = np.array(positions, dtype=np.float32)
    visual.node.text.anchors = (anchor_x, anchor_y)
    return positions
