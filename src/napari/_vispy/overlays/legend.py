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

    def _on_text_change(self):
        """Update text information"""
        # update the dpi scale factor to account for screen dpi
        # because vispy scales pixel height of text by screen dpi
        if self.node.text.transforms.dpi:
            # use 96 as the napari reference dpi for historical reasons
            dpi_scale_factor = 96 / self.node.text.transforms.dpi
        else:
            dpi_scale_factor = 1

        self.node.text.font_size = text_factor = (
            self.overlay.font_size * dpi_scale_factor
        )
        # changing the fox size changes the box height and positioning in it
        # self.node._update_layout(font_size=self.overlay.font_size)

        # positioning in the box uses the center of the box
        # need to adjust the y_size to be half the size of the current box height
        # self.y_size = self.node.box.height / 2
        update_text(self, text_factor)

    def reset(self):
        """Reset the overlay to its initial state."""
        super().reset()
        self._on_box_change()
        self._on_text_change()
        self._on_position_change()


def update_text(visual: VispyLegendOverlay, text_factor: float) -> None:
    """Get position of the legend overlay."""
    from operator import add, sub

    overlay = visual.overlay
    if not overlay.items:
        visual.node.text.text = overlay.text()
        visual.node.text.color = overlay.color()
        visual.node.text.pos = np.array([[0, 0]], dtype=np.float32)
        return None

    anchor_x, anchor_y = 'center', 'top'
    if overlay.align in [Alignment.ROW, Alignment.ROW_SPLIT]:
        x_offset, y_offset = 0, 50
    else:
        x_offset, y_offset = 50, 0
        anchor_x = (
            'left'
            if overlay.position
            in [CanvasPosition.TOP_LEFT, CanvasPosition.BOTTOM_LEFT]
            else 'right'
        )

    translate_x, translate_y, _, _ = visual.node.transform.translate
    max_x, max_y = visual.node.canvas.size
    translate_x, translate_y = 0, max_y

    # first let's find out what would be the total width of the text, as it will change
    # how much horizontal offset is needed when displaying in the center

    # let's calculate any offsets and anchors
    if overlay.position in [
        CanvasPosition.TOP_LEFT,
        CanvasPosition.TOP_CENTER,
        CanvasPosition.TOP_RIGHT,
    ]:
        reverse = False
        x_operator = add
        y_operator = add
        anchor_y = 'top'
        y_start_ = max_y - translate_y + y_offset
        if overlay.position == CanvasPosition.TOP_LEFT:
            x_start_ = translate_x + x_offset
        elif overlay.position == CanvasPosition.TOP_CENTER:
            x_start_ = max_x / 2 - translate_x / 2 + x_offset
            anchor_x = 'center'
        else:
            x_start_ = max_x - translate_x - x_offset
            x_operator = sub
    else:
        reverse = True
        x_operator = sub
        y_operator = sub
        anchor_y = 'bottom'
        y_start_ = translate_y - y_offset
        if overlay.position == CanvasPosition.BOTTOM_LEFT:
            x_start_ = translate_x + x_offset
            x_operator = add
        elif overlay.position == CanvasPosition.BOTTOM_CENTER:
            x_start_ = max_x / 2 - translate_x / 2 + x_offset
            anchor_x = 'center'
        else:
            x_start_ = max_x - translate_x - x_offset

    padding = 3 if len(overlay.text()) > 1 else 0
    height = text_factor * 0.75
    positions = []
    for text in overlay.text(reverse):
        n = len(text)
        if overlay.align == Alignment.ROW:
            x_start_ = x_operator(x_start_, (n + padding) * text_factor)
        elif overlay.align == Alignment.COLUMN:
            y_start_ = y_operator(y_start_, height + padding * text_factor)
        positions.append((x_start_, y_start_))
    visual.node.text.text = overlay.text(reverse)
    visual.node.text.color = overlay.color(reverse)
    visual.node.text.pos = np.array(positions, dtype=np.float32)
    visual.node.text.anchors = (anchor_x, anchor_y)
    return positions
