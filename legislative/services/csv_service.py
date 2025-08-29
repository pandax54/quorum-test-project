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

    @lru_cache(maxsize=1)
    def get_complete_legislators_data(self):
        complete_data = self.legislators.merge(self.votes_results.merge(self.votes.merge(self.bills, left_on='bill_id', right_on='id', suffixes=('', '_bill')), left_on='vote_id', right_on='id', suffixes=(
            '', 'vr')), left_on='id', right_on='legislator_id', suffixes=('', '_votes'))

        vote_counts = complete_data.groupby('legislator_id').agg({
            'name': 'first',
            'vote_type': ['count', lambda x: (x == 1).sum(), lambda x: (x == 2).sum()],
        }).rename(columns={'vote_type': 'total_votes'})

        vote_counts.columns = ['name', 'total_votes', 'yes_votes', 'no_votes']
        vote_counts = vote_counts.reset_index(drop=True)

        result = pd.DataFrame({
            'Legislator': vote_counts['name'],
            'total_votes': vote_counts['total_votes'],
            'yes_votes': vote_counts['yes_votes'],
            'no_votes': vote_counts['no_votes']
        })
        return result
