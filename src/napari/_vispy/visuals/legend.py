"""Legend visual."""

from vispy.scene.visuals import Compound, Rectangle, Text


class Legend(Compound):
    """Legend visual."""

    def __init__(self) -> None:
        # order matters (last is drawn on top)
        super().__init__(
            [
                Rectangle(center=[0, 0], width=1.1, height=36),
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
        """Box visual."""
        return self._subvisuals[0]

    @property
    def text(self):
        """Text visual."""
        return self._subvisuals[1]
