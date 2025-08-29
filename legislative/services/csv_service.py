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
    def vote_results(self):
        return pd.read_csv(os.path.join(self.data_folder, 'vote_results.csv'))

    @lru_cache(maxsize=1)
    def get_complete_legislators_data(self) -> pd.DataFrame:
        complete_data = self.legislators.merge(self.vote_results.merge(self.votes.merge(self.bills, left_on='bill_id', right_on='id', suffixes=('', '_bill')), left_on='vote_id', right_on='id', suffixes=(
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

    @lru_cache(maxsize=1)
    def get_stats(self):
        return {
            'legislators_count': len(self.legislators),
            'bills_count': len(self.bills),
            'votes_count': len(self.vote_results)
        }

    @lru_cache(maxsize=1)
    def get_complete_bills_data(self) -> pd.DataFrame:
        complete_data = self.legislators.merge(self.vote_results.merge(self.votes.merge(self.bills, left_on='bill_id', right_on='id', suffixes=('', '_bill')), left_on='vote_id', right_on='id', suffixes=(
            '', '_vr')), left_on='id', right_on='legislator_id', how='left', suffixes=('', '_votes'))

        count_votes = complete_data.groupby('bill_id').agg({
            'title': 'first',
            'name': 'first',
            'vote_type': ['count', lambda x: (x == 1).sum(), lambda x: (x == 2).sum()]
        })

        count_votes.columns = ['title', 'name',
                               'total_votes', 'yes_votes', 'no_votes']

        count_votes = count_votes.reset_index(drop=True)

        result = pd.DataFrame({
            'Bill': count_votes['title'],
            'Sponsor': count_votes['name'],
            'total_votes': count_votes['total_votes'],
            'yes_votes': count_votes['yes_votes'],
            'no_votes': count_votes['no_votes']
        })
        return result

    def render_table(self, data: pd.DataFrame) -> str:
        df = pd.DataFrame(data)
        return df.to_html(
            classes='table table-striped table-hover',
            justify='left',
            escape=False,
            index=False,
            border=0
        )
