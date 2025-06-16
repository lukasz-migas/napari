from napari.utils.compat import StrEnum


class CanvasPosition(StrEnum):
    """Canvas overlay position.

    Sets the position of an object in the canvas
            * top_left: Top left of the canvas
            * top_right: Top right of the canvas
            * top_center: Top center of the canvas
            * bottom_right: Bottom right of the canvas
            * bottom_left: Bottom left of the canvas
            * bottom_center: Bottom center of the canvas
    """

    TOP_LEFT = 'top_left'
    TOP_CENTER = 'top_center'
    TOP_RIGHT = 'top_right'
    BOTTOM_RIGHT = 'bottom_right'
    BOTTOM_CENTER = 'bottom_center'
    BOTTOM_LEFT = 'bottom_left'


class LegendAlignment(StrEnum):
    """Alignment of text in legend.

    Sets the alignment of text labels in the legend overlay.
        * row: All text labels are in a single row.
        * column: All text labels are in a single column.
        * row_split: Text labels are in a single row, but can wrap to multiple lines.
        * column_split: Text labels are in a single column, but can wrap to multiple lines.
    """

    ROW = 'row'
    COLUMN = 'column'
    ROW_SPLIT = 'row_split'
    COLUMN_SPLIT = 'column_split'


class CursorStyle(StrEnum):
    """CursorStyle: Style on the cursor.

    Sets the style of the cursor
            * square: A square
            * circle: A circle
            * circle_frozen:
                A brush circle with a frozen position along with the standard cursor.
                It is used to show the brush size change while using Ctrl+Alt + mouse move.
            * cross: A cross
            * forbidden: A forbidden symbol
            * pointing: A finger for pointing
            * standard: The standard cursor
            # crosshair: A crosshair
    """

    SQUARE = 'square'
    CIRCLE = 'circle'
    CIRCLE_FROZEN = 'circle_frozen'
    CROSS = 'cross'
    FORBIDDEN = 'forbidden'
    POINTING = 'pointing'
    STANDARD = 'standard'
    CROSSHAIR = 'crosshair'
