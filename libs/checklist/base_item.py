from abc import abstractmethod


class BaseItem:
    def __init__(self):
        self._name = "BaseItem"
        self._description = "Base item for checklist framework. If you see this, it means the item is not properly defined."
        self._category = "Other"

    @abstractmethod
    def sample(self, *args, **kwargs):
        """Sample from the given item."""
        pass

    @abstractmethod
    def test(self):
        """Test the given item."""
        pass

    @abstractmethod
    def persist(self, *args, **kwargs):
        """Persist the given item."""
        pass

    @abstractmethod
    def load(self, *args, **kwargs):
        """Load the given item."""
        pass

    @property
    def name(self):
        return self._name
    
    @property
    def description(self):
        return self._description
    
    @property
    def category(self):
        return self._category