from abc import abstractmethod


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
    def vote_results(self):
        pass

    @abstractmethod
    def get_stats(self):
        pass

    @abstractmethod
    def get_complete_legislators_data(self):
        pass

    @abstractmethod
    def get_complete_bills_data(self):
        pass
