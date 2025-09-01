from django.conf import settings
from .csv_service import CSVLegislativeDataService


def get_legislative_service():
    """Factory function to get the appropriate service implementation"""

    service_type = getattr(settings, "LEGISLATIVE_DATA_SERVICE", "csv")

    if service_type == "csv":
        return CSVLegislativeDataService()

    if service_type == "database":
        raise NotImplementedError("Database service not yet implemented")

    raise ValueError(f"Unknown service type: {service_type}")


legislative_service = get_legislative_service()
