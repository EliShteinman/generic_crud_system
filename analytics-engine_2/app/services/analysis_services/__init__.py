from .sales_by_region import SalesByRegionService
from .user_activity_summary import UserActivitySummaryService

# רישום כל השירותים הזמינים
AVAILABLE_SERVICES = {
    "sales_by_region": SalesByRegionService,
    "user_activity_summary": UserActivitySummaryService
}

def get_service(service_name: str):
    """קבלת שירות לפי שם"""
    service_class = AVAILABLE_SERVICES.get(service_name)
    if service_class:
        return service_class()
    return None