"""
Multiple image layers with Legend Overlay
===================================

Display an image in napari and add a bounding box overlay (a border) at the edges of the layer.

The bounding box overlay is a visual representation of the extents of a layer.
This example demonstrates visualization of many bounding box overlay properties,
including line color, line thickness, point size, opacity.
In addition, this viewer shows how layer overlays interact when draw on top of each other (at the intersection of the grid).
Use `viewer.layers[0].bounding_box` to view all modifiable attributes of the overlay.

For an example showing how bounding box extents are visualized, see
:ref:`sphx_glr_gallery_layer_bounding_box.py`.

.. tags:: visualization-advanced
"""

from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QSpinBox,
    QWidget,
)
from skimage import data

import napari


class LegendControls(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.align_combo = QComboBox()
        self.align_combo.addItems(
            ['row', 'column', 'row_split', 'column_split']
        )
        self.align_combo.setCurrentText(viewer.legend_overlay.align.value)
        self.align_combo.currentTextChanged.connect(self.on_align_change)

        self.position_combo = QComboBox()
        self.position_combo.addItems(
            [
                'top_left',
                'top_center',
                'top_right',
                'bottom_left',
                'bottom_center',
                'bottom_right',
            ]
        )
        self.position_combo.setCurrentText(
            viewer.legend_overlay.position.value
        )
        self.position_combo.currentTextChanged.connect(self.on_position_change)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(1, 100)
        self.font_size_spin.setValue(int(viewer.legend_overlay.font_size))
        self.font_size_spin.setSingleStep(1)
        self.font_size_spin.valueChanged.connect(self.on_font_size_change)

        self.box_check = QCheckBox()
        self.box_check.setChecked(viewer.legend_overlay.box)
        self.box_check.stateChanged.connect(self.on_box_changed)

        self.layout = QFormLayout(self)
        self.layout.addRow('Align', self.align_combo)
        self.layout.addRow('Position', self.position_combo)
        self.layout.addRow('Font Size', self.font_size_spin)
        self.layout.addRow('Box', self.box_check)

    def on_align_change(self, text):
        """Update the legend overlay align."""
        viewer.legend_overlay.align = text

    def on_position_change(self, text):
        """Update the legend overlay position."""
        viewer.legend_overlay.position = text

    def on_font_size_change(self, text):
        """Update the legend overlay font size."""
        viewer.legend_overlay.font_size = text

    def on_box_changed(self, state):
        """Update the legend overlay box visibility."""
        viewer.legend_overlay.box = state == 2


viewer = napari.view_image(data.astronaut(), rgb=True)

# Create a napari viewer with a 3D, 2 channel image, with the `view_image` convenience function.
# viewer = napari.view_image(
#     data.cells3d(), channel_axis=1, name=['membrane', 'nuclei']
# )

viewer.legend_overlay.visible = True
viewer.legend_overlay.font_size = 24
viewer.legend_overlay.position = 'bottom_center'
viewer.legend_overlay.align = 'row'
viewer.legend_overlay.box = True
viewer.legend_overlay.box_color = 'yellow'
viewer.legend_overlay.add('Red 1', 'red')
viewer.legend_overlay.add('Green 1', 'green')
viewer.legend_overlay.add('Blue 1', 'blue')
viewer.legend_overlay.add('A much longer label', 'magenta')
# viewer.legend_overlay.add('Red 2', 'red')
# viewer.legend_overlay.add('Green 2', 'green')
# viewer.legend_overlay.add('Blue 2', 'blue')
# viewer.legend_overlay.add('Red 3', 'red')
# viewer.legend_overlay.add('Green 3', 'green')
# viewer.legend_overlay.add('Blue 3', 'blue')
# viewer.legend_overlay.add('Red 4', 'red')
# viewer.legend_overlay.add('Green 4', 'green')
# viewer.legend_overlay.add('Blue 4', 'blue')

# create widget
widget = LegendControls()
viewer.window.add_dock_widget(widget, area='right')

if __name__ == '__main__':
    napari.run()
