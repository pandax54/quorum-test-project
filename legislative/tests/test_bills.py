from legislative.services import legislative_service


class TestCSVService:
    """
    Test class for CSV service functionality.

    This class contains test methods to verify the behavior of legislative-related operations,
    including data retrieval and sponsor information handling.
    """

    def test_get_complete_bills_data_handles_missing_sponsor(self):
        bills = legislative_service.get_complete_bills_data()

        without_sponsor = list(
            filter(lambda item: item["id"] == 2900994, bills))[0]

        print(bills)
        assert len(bills) == 2
        assert without_sponsor["sponsor"] == "Unknown Sponsor"

    def test_test_get_complete_legislators_data(self):
        legislators = legislative_service.get_complete_legislators_data()

        len_without_votes = list(
            filter(lambda item: item["id"] == 412211, legislators)
        )[0]

        # do not exclude the legislator without any votes in the join
        assert len(legislators) == 20
        assert len_without_votes["legislator"] == "Rep. John Yarmuth (D-KY-3)"
        assert len_without_votes["total_votes"] == 0
