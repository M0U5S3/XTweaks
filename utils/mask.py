class Mask:
    """
    Contains all the data required to replace a number in an image with a new one.
    """

    def __init__(
            self,
            rectangle_id: int
    ) -> None:
        """
        Initialize a new Mask instance.

        Args:
            rectangle_id (int): Identifier for a tk rectangle.
        """

        self.rectangle_id: int = rectangle_id