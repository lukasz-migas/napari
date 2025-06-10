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

from skimage import data

import napari

viewer = napari.view_image(data.astronaut(), rgb=True)
# Create a napari viewer with a 3D, 2 channel image, with the `view_image` convenience function.
# viewer = napari.view_image(
#     data.cells3d(), channel_axis=1, name=['membrane', 'nuclei']
# )

viewer.legend_overlay.visible = True
viewer.legend_overlay.font_size = 48
viewer.legend_overlay.position = 'bottom_left'
viewer.legend_overlay.align = 'column_split'
for index in range(25):
    viewer.legend_overlay.add(f'Label {index} ', 'red')
# viewer.legend_overlay.add('Red', 'red')
# viewer.legend_overlay.add('Green', 'green')
# viewer.legend_overlay.add('Blue', 'blue')

if __name__ == '__main__':
    napari.run()
