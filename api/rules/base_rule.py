from abc import ABC, abstractmethod

class BaseRule(ABC):
    """Abstract base class for all rules."""

    @abstractmethod
    def apply(self, data: dict) -> dict:
        """
        Applies the rule to the given data.

        Args:
            data: The input data dictionary.

        Returns:
            The processed data dictionary.
        """
        pass
