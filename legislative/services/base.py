from abc import ABC, abstractmethod


class LegislativeDataServiceInterface():
    """Abstract interface for legislative data services"""

    @property
    @abstractmethod
    def legislators(self):
        pass

    @property
    @abstractmethod
    def bills(self):
        pass

    @property
    @abstractmethod
    def votes(self):
        pass

    @property
    @abstractmethod
    def votes_results(self):
        pass
