# Standard library imports
from typing import Optional, Callable

# Local application imports
from utils.mask import Mask


class Variable:
    """
    A number that is generated according to CRNG function then pasted over different masks given.
    """

    def __init__(
            self,
            variable_name: str,
            masks: Optional[list[Mask]] = None
    ) -> None:
        """
        Initialize a new Variable instance.

        Args:
            variable_name (str): A reference name for the variable in ResLang.
            masks (Optional[list[Mask]]): A list of Mask objects specifying where numbers can be placed on the image.
                If not provided, defaults to an empty list.
        """

        # Private parameter attributes
        self._variable_name: str = variable_name

        # Public parameter attributes
        self.masks: Optional[list[Mask]] = masks if masks is not None else []

    @property
    def variable_name(self):
        return self._variable_name

    @variable_name.setter
    def variable_name(self, variable_name):
        self.variable_name = variable_name

    @property
    def crng_function(self):
        return self._crng_function

    @crng_function.setter
    def crng_function(self, crng_function):
        self._crng_function = crng_function

    @property
    def masks(self):
        return self._masks

    @masks.setter
    def masks(self, masks: list[Mask,...]):
        self._masks = masks

    def add_mask(self, mask: Mask) -> None:
        """
        Assign a new mask to the variable

        Args:
            mask (Mask): A Mask to assign.
        """

        self._masks.append(mask)

    def remove_mask(self, mask: Mask):
        """
        Remove a mask from the variable

        Args:
            mask (Mask): A Mask to remove.
        """

        self._masks.remove(mask)
