import os
import pandas as pd
from functools import lru_cache
from django.conf import settings
from .base import LegislativeDataServiceInterface


class CSVLegislativeDataService(LegislativeDataServiceInterface):
    """CSV-based implementation of legislative data service"""

    def __init__(self):
        self.data_folder = os.path.join(settings.BASE_DIR, 'data')

    @property
    @lru_cache(maxsize=1)
    def legislators(self):
        return pd.read_csv(os.path.join(self.data_folder, 'legislators.csv'))

    @property
    @lru_cache(maxsize=1)
    def bills(self):
        return pd.read_csv(os.path.join(self.data_folder, 'bills.csv'))

    @property
    @lru_cache(maxsize=1)
    def votes(self):
        return pd.read_csv(os.path.join(self.data_folder, 'votes.csv'))

    @property
    @lru_cache(maxsize=1)
    def votes_results(self):
        return pd.read_csv(os.path.join(self.data_folder, 'vote_results.csv'))
