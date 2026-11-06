from abc import ABC, abstractmethod


class AIProvider(ABC):
    # Shared interface: managers can request completions without knowing the provider.

    @abstractmethod
    def complete(self, messages):
        """Return a provider completion or raise a service error."""

    @abstractmethod
    def close(self):
        """Release resources owned by this provider, leaving borrowed ones open."""

