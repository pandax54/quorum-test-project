from abc import abstractmethod
from typing import Callable, List, Optional, TypedDict

import pandas as pd


class BillsDataDict(TypedDict, total=True):
    id: int
    title: str
    sponsor_id: int
    sponsor: str
    total_votes: int
    yea_votes: int
    nay_votes: int


class LinkableColumnsList(TypedDict, total=False):
    id: int
    column_name: str
    url_pattern: str
    item_id: str
    name: str
    css_class: str
    """ Function to determine if row should be linked"""
    should_link: Optional[Callable[[dict], bool]]


class LegislativeDataServiceInterface:
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
    def get_complete_bills_data(self) -> List[BillsDataDict]:
        pass

    @abstractmethod
    def render_table(
        self, data: pd.DataFrame, linkable_list: Optional[List[LinkableColumnsList]]
    ) -> pd.DataFrame:
        """
        Convert structured data to HTML table.
        Works with data from any source (CSV, DB, etc.)
        """
        pass

    @abstractmethod
    def get_bill_by_id(self):
        pass

    @abstractmethod
    def get_legislator_by_id(self):
        pass
