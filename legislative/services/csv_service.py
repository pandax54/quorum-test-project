import os
import pandas as pd
from functools import lru_cache
from django.conf import settings
from .base import LegislativeDataServiceInterface


class CSVLegislativeDataService(LegislativeDataServiceInterface):
    """CSV-based implementation with simple dynamic column support"""

    def __init__(self):
        self.data_folder = os.path.join(settings.BASE_DIR, 'data')

    # Data loading properties
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

    # Helper methods
    def make_link(self, url_pattern, item_id, text, css_class=""):
        """Create HTML link"""
        class_attr = f' class="{css_class}"' if css_class else ""
        return f'<a href="{url_pattern.format(id=item_id)}"{class_attr}>{text}</a>'

    def format_date(self, date_str):
        """Format date string"""
        if pd.isna(date_str) or date_str == "":
            return "N/A"
        try:
            return pd.to_datetime(date_str).strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            return str(date_str)

    @lru_cache(maxsize=1)
    def get_complete_bills_data(self):

        vote_counts = (self.vote_results
                       .merge(self.votes, left_on='vote_id', right_on='id')
                       .groupby('bill_id')
                       .agg({'vote_type': ['count', lambda x: (x == 1).sum(), lambda x: (x == 2).sum()]})
                       .reset_index())
        vote_counts.columns = ['bill_id',
                               'total_votes', 'yea_votes', 'nay_votes']

        result = (self.bills
                  .merge(self.legislators, left_on='sponsor_id', right_on='id',
                         suffixes=('', '_sponsor'), how='left')
                  .merge(vote_counts, left_on='id', right_on='bill_id', how='left')
                  .fillna({'total_votes': 0, 'yea_votes': 0, 'nay_votes': 0, 'name': 'Unknown Sponsor'}))

        # Convert vote counts to int otherwise they will show up as float
        result[['total_votes', 'yea_votes', 'nay_votes']] = result[[
            'total_votes', 'yea_votes', 'nay_votes']].astype(int)

        result['title_formatted'] = result.apply(
            lambda row: self.make_link('/bills/{id}/', row['id'], row['title'], 'bill-link'), axis=1
        )
        result['sponsor_formatted'] = result.apply(
            lambda row: self.make_link(
                '/legislators/{id}/', row['sponsor_id'], row['name'], 'legislator-link')
            if row['name'] != 'Unknown Sponsor' else row['name'], axis=1
        )

        base_output = {
            'id': result['id'],
            'title': result['title_formatted'],
            'sponsor': result['sponsor_formatted'],
            'total_votes': result['total_votes'],
            'yea_votes': result['yea_votes'],
            'nay_votes': result['nay_votes'],
        }

        return pd.DataFrame(base_output).to_dict('records')

    @lru_cache(maxsize=1)
    def get_complete_legislators_data(self):

        complete_data = (self.legislators
                         .merge(self.vote_results
                                .merge(self.votes
                                       .merge(self.bills, left_on='bill_id', right_on='id', how='left', suffixes=('', '_bill')),
                                       left_on='vote_id', right_on='id', how='left', suffixes=('', '_vr')),
                                left_on='id', right_on='legislator_id', how='left', suffixes=('', '_votes')))

        vote_counts = complete_data.groupby('legislator_id').agg({
            'vote_type': ['count', lambda x: (x == 1).sum(), lambda x: (x == 2).sum()],
        }).reset_index()
        vote_counts.columns = ['legislator_id',
                               'total_votes', 'yes_votes', 'no_votes']

        bills_sponsored = self.bills.groupby(
            'sponsor_id').size().reset_index(name='bills_sponsored')

        result = (self.legislators
                  .merge(vote_counts, left_on='id', right_on='legislator_id', how='left')
                  .merge(bills_sponsored, left_on='id', right_on='sponsor_id', how='left')
                  .fillna({'total_votes': 0, 'yes_votes': 0, 'no_votes': 0, 'bills_sponsored': 0}))

        result[['total_votes', 'yes_votes', 'no_votes', 'bills_sponsored']] = result[[
            'total_votes', 'yes_votes', 'no_votes', 'bills_sponsored']].astype(int)

        result['name_formatted'] = result.apply(
            lambda row: self.make_link('/legislators/{id}/', row['id'], row['name'], 'legislator-link'), axis=1
        )

        base_output = {
            'legislator': result['name_formatted'],
            'total_votes': result['total_votes'],
            'yes_votes': result['yes_votes'],
            'no_votes': result['no_votes'],
            'bills_sponsored': result['bills_sponsored']
        }

        return pd.DataFrame(base_output)

    def render_table(self, data):
        """Render DataFrame as HTML table"""
        return pd.DataFrame(data).to_html(
            classes='table table-striped table-hover',
            justify='left',
            escape=False,
            index=False,
            border=0
        )

    @lru_cache(maxsize=1)
    def get_stats(self):
        return {
            'legislators_count': len(self.legislators),
            'bills_count': len(self.bills),
            'votes_count': len(self.vote_results)
        }

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
                'vote_details': [],
                **{col: bill_info.get(col, None) for col in self.bills.columns if col not in ['id', 'title', 'sponsor_id']}
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
                legislator_link = self.make_link(
                    '/legislators/{id}/', row['legislator_id'], legislator_name, 'legislator-link')
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
            'vote_details': styled_vote_details,
            **{col: bill_info.get(col, None) for col in self.bills.columns if col not in ['id', 'title', 'sponsor_id']}
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
            bill_link = self.make_link(
                '/bills/{id}/', row['bill_id'], row['title'], 'bill-link')

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

            bill_link = self.make_link(
                '/bills/{id}/', bill['id'], bill['title'], 'bill-link')

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
            'sponsored_bills_details': sponsored_bills_details,
            **{col: legislator_info.get(col, None) for col in self.legislators.columns if col not in ['id', 'name']}
        }
