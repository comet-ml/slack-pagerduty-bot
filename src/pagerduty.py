import logging
import pagerduty
from config import PAGERDUTY_INTEGRATION_KEY

logger = logging.getLogger(__name__)


class PagerDutyClient:
    """Client for interacting with PagerDuty API."""

    def __init__(self, service_id=None):
        """
        Initialize PagerDuty client.
        
        Args:
            service_id: PagerDuty Integration Key (defaults to config)
        """
        self.service_id = service_id or PAGERDUTY_INTEGRATION_KEY
        self.events_client = pagerduty.EventsApiV2Client(self.service_id)

    def trigger_incident(self, summary, user_info, details=None):
        """
        Trigger an incident in PagerDuty.
        
        Args:
            summary: Brief description of the incident
            user_info: Information about the user who triggered the incident
            details: Additional details about the incident
            
        Returns:
            dict: The created incident data or None if failed
        """
        if not self.service_id:
            logger.error("PagerDuty Integration Key not configured")
            return None

        if details is None:
            details = {}

        # Add user information to details
        details["triggered_by_user"] = user_info
        
        try:
            source = "Slack Bot"
            dedup_key = self.events_client.trigger(
                summary, 
                source=source,
                custom_details=details
            )
            
            logger.info(f"Triggered PagerDuty incident: {dedup_key}")
            return {"id": dedup_key, "status": "triggered"}
                
        except Exception as e:
            logger.error(f"Error triggering PagerDuty incident: {str(e)}")
            return None 