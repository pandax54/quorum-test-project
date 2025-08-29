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

    @property
    @lru_cache(maxsize=1)
    def complete_data(self):
        return self.legislators.merge(self.vote_results.merge(self.votes.merge(self.bills, left_on='bill_id', right_on='id', how='left', suffixes=('', '_bill')), left_on='vote_id', right_on='id', how='left', suffixes=(
            '', '_vr')), left_on='id', right_on='legislator_id', how='left', suffixes=('', '_votes'))

    @lru_cache(maxsize=1)
    def get_complete_legislators_data(self) -> pd.DataFrame:
        all_legislators = self.legislators.copy()

        vote_counts = self.complete_data.groupby('legislator_id').agg({
            'vote_type': ['count', lambda x: (x == 1).sum(), lambda x: (x == 2).sum()],
        })
        vote_counts.columns = ['total_votes', 'yes_votes', 'no_votes']
        vote_counts = vote_counts.reset_index()

        bills_sponsored = self.bills.groupby('sponsor_id').size().reset_index()
        bills_sponsored.columns = ['legislator_id', 'bills_sponsored']

        result_data = all_legislators.merge(
            vote_counts,
            left_on='id',
            right_on='legislator_id',
            how='left'
        )

        result_data = result_data.merge(
            bills_sponsored,
            left_on='id',
            right_on='legislator_id',
            how='left'
        )

        # Fill missing values with 0
        result_data[['total_votes', 'yes_votes', 'no_votes', 'bills_sponsored']] = result_data[
            ['total_votes', 'yes_votes', 'no_votes', 'bills_sponsored']
        ].fillna(0).astype(int)

        result_data['name'] = result_data.apply(
            lambda row: f'<a href="/legislators/{row["id"]}/" class="legislator-link">{row["name"]}</a>'
            if row["name"] != "Unknown Sponsor" else row["name"],
            axis=1
        )

        result = pd.DataFrame({
            'legislator': result_data['name'],
            'total_votes': result_data['total_votes'],
            'yes_votes': result_data['yes_votes'],
            'no_votes': result_data['no_votes'],
            'bills_sponsored': result_data['bills_sponsored']
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
        """
        Get bills data as structured data (works for both CSV and DB versions).
        Returns list of dictionaries.
        """
        voting_data_for_counts = (self.vote_results
                                  .merge(self.votes, left_on='vote_id', right_on='id'))

        vote_counts = voting_data_for_counts.groupby('bill_id').agg({
            'vote_type': ['count', lambda x: (x == 1).sum(), lambda x: (x == 2).sum()]
        }).reset_index()

        vote_counts.columns = ['bill_id',
                               'total_votes', 'yea_votes', 'nay_votes']

        complete_data = (self.bills
                         .merge(self.legislators, left_on='sponsor_id', right_on='id',
                                suffixes=('', '_sponsor'), how='left')
                         .merge(vote_counts, left_on='id', right_on='bill_id', how='left')
                         .fillna({
                             'total_votes': 0,
                             'yea_votes': 0,
                             'nay_votes': 0,
                             'name': 'Unknown Sponsor'
                         }))

        complete_data['title'] = complete_data.apply(
            lambda row: f'<a href="/bills/{row["id"]}/" class="bill-link">{row["title"]}</a>',
            axis=1
        )
        complete_data['name'] = complete_data.apply(
            lambda row: f'<a href="/legislators/{row["sponsor_id"]}/" class="legislator-link">{row["name"]}</a>'
            if row["name"] != "Unknown Sponsor" else row["name"],
            axis=1
        )

        result = pd.DataFrame({
            'id': complete_data['id'],
            'title': complete_data['title'],
            'sponsor': complete_data['name'],
            'total_votes': complete_data['total_votes'].astype(int),
            'yea_votes': complete_data['yea_votes'].astype(int),
            'nay_votes': complete_data['nay_votes'].astype(int)
        })

        return result.to_dict('records')

    def render_table(self, data: pd.DataFrame) -> str:
        df = pd.DataFrame(data)
        return df.to_html(
            classes='table table-striped table-hover',
            justify='left',
            escape=False,
            index=False,
            border=0
        )

    def get_bill_by_id(self, bill_id):
        """
        Returns detailed bill information with sponsor name, vote counts, and voting breakdown.
        """

        bill_with_sponsor = self.bills[self.bills['id'] == bill_id].merge(
            self.legislators[['id', 'name']],
            left_on='sponsor_id',
            right_on='id',
            how='left',
            suffixes=('', '_legislator')
        )

        if bill_with_sponsor.empty:
            return None

        bill_info = bill_with_sponsor.iloc[0]

        sponsor_name = bill_info['name'] if pd.notna(
            bill_info['name']) else 'Unknown Sponsor'
        sponsor_id = bill_info['sponsor_id']

        bill_votes_query = self.votes[self.votes['bill_id'] == bill_id]

        if bill_votes_query.empty:
            return {
                'id': bill_info['id'],
                'title': bill_info['title'],
                'sponsor_name': sponsor_name,
                'sponsor_id': sponsor_id,
                'total_votes': 0,
                'supporters': 0,
                'opposers': 0,
                'vote_details': []
            }

        vote_id = bill_votes_query.iloc[0]['id']

        vote_results = self.vote_results[self.vote_results['vote_id'] == vote_id]

        supporters = len(vote_results[vote_results['vote_type'] == 1])
        opposers = len(vote_results[vote_results['vote_type'] == 2])
        total_votes = len(vote_results)

        vote_details = vote_results.merge(
            self.legislators,
            left_on='legislator_id',
            right_on='id',
            how='left'
        )

        styled_vote_details = []
        for _, row in vote_details.iterrows():
            legislator_name = row['name'] if pd.notna(
                row['name']) else f"Unknown Legislator ({row['legislator_id']})"
            vote_badge = '<span class="badge bg-success">Yes</span>' if row[
                'vote_type'] == 1 else '<span class="badge bg-danger">No</span>'

            if pd.notna(row['name']):
                legislator_link = f'<a href="/legislators/{row["legislator_id"]}/" class="legislator-link">{legislator_name}</a>'
            else:
                legislator_link = legislator_name

            styled_vote_details.append({
                'legislator_id': row['legislator_id'],
                'legislator_name': legislator_link,
                'legislator_name_plain': legislator_name,
                'vote': vote_badge,
                'vote_raw': 'Yes' if row['vote_type'] == 1 else 'No'
            })

        styled_vote_details.sort(key=lambda x: (
            x['vote_raw'] == 'No', x['legislator_name_plain']))

        return {
            'id': bill_info['id'],
            'title': bill_info['title'],
            'sponsor_name': sponsor_name,
            'sponsor_id': sponsor_id,
            'total_votes': total_votes,
            'supporters': supporters,
            'opposers': opposers,
            'vote_details': styled_vote_details
        }

    def get_legislator_by_id(self, legislator_id):
        """
        Returns detailed legislator information with vote counts, bills voted on, and bills sponsored.
        """
        legislator = self.legislators[self.legislators['id'] == legislator_id]
        if legislator.empty:
            return None

        legislator_info = legislator.iloc[0]

        legislator_votes = self.vote_results[self.vote_results['legislator_id']
                                             == legislator_id]
        supporters = len(legislator_votes[legislator_votes['vote_type'] == 1])
        opposers = len(legislator_votes[legislator_votes['vote_type'] == 2])
        total_votes = len(legislator_votes)

        bills_voted_on = (legislator_votes
                          .merge(self.votes, left_on='vote_id', right_on='id', suffixes=('', '_vote'))
                          .merge(self.bills, left_on='bill_id', right_on='id', suffixes=('', '_bill')))

        bills_voted_details = []
        for _, row in bills_voted_on.iterrows():
            vote_badge = '<span class="badge bg-success">Yes</span>' if row[
                'vote_type'] == 1 else '<span class="badge bg-danger">No</span>'
            bill_link = f'<a href="/bills/{row["bill_id"]}/" class="bill-link">{row["title"]}</a>'

            bills_voted_details.append({
                'bill_id': row['bill_id'],
                'bill_title': bill_link,
                'bill_title_plain': row['title'],
                'vote': vote_badge,
                'vote_raw': 'Yes' if row['vote_type'] == 1 else 'No'
            })

        bills_voted_details.sort(key=lambda x: (
            x['vote_raw'] == 'No', x['bill_title_plain']))

        sponsored_bills = self.bills[self.bills['sponsor_id'] == legislator_id]
        sponsored_bills_details = []

        for _, bill in sponsored_bills.iterrows():
            bill_vote_query = self.votes[self.votes['bill_id'] == bill['id']]
            if not bill_vote_query.empty:
                vote_id = bill_vote_query.iloc[0]['id']
                bill_votes = self.vote_results[self.vote_results['vote_id'] == vote_id]
                bill_supporters = len(bill_votes[bill_votes['vote_type'] == 1])
                bill_opposers = len(bill_votes[bill_votes['vote_type'] == 2])
                bill_total = len(bill_votes)
            else:
                bill_supporters = bill_opposers = bill_total = 0

            bill_link = f'<a href="/bills/{bill["id"]}/" class="bill-link">{bill["title"]}</a>'

            sponsored_bills_details.append({
                'bill_id': bill['id'],
                'bill_title': bill_link,
                'bill_title_plain': bill['title'],
                'supporters': bill_supporters,
                'opposers': bill_opposers,
                'total_votes': bill_total
            })

        sponsored_bills_details.sort(key=lambda x: x['bill_title_plain'])

        return {
            'id': legislator_info['id'],
            'name': legislator_info['name'],
            'total_votes': total_votes,
            'supporters': supporters,
            'opposers': opposers,
            'bills_voted_on_count': len(bills_voted_details),
            'bills_sponsored_count': len(sponsored_bills_details),
            'bills_voted_on_details': bills_voted_details,
            'sponsored_bills_details': sponsored_bills_details
        }
