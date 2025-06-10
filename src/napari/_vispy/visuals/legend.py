"""Legend visual."""

import numpy as np
from vispy.scene.visuals import Compound, Rectangle, Text


class Legend(Compound):
    def __init__(self) -> None:
        # order matters (last is drawn on top)
        super().__init__(
            [
                Rectangle(center=[0.5, 0.5], width=1.1, height=36),
                Text(
                    text='1px',
                    pos=[0.5, 0.5],
                    anchor_x='center',
                    anchor_y='top',
                    font_size=10,
                ),
            ]
        )

    @property
    def box(self):
        return self._subvisuals[0]

    @property
    def text(self):
        return self._subvisuals[1]

    def set_data(self, text: list[str], color: list[np.ndarray]) -> None:
        self.text.text = text
        self.text.color = color
