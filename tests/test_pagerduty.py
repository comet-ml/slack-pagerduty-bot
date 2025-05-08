import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import the src module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pagerduty import PagerDutyClient


class TestPagerDutyClient(unittest.TestCase):
    
    @patch('pagerduty.EventsApiV2Client')
    def test_init(self, mock_events_client):
        # Test initialization with default values
        client = PagerDutyClient(service_id='test_key')
        mock_events_client.assert_called_once_with('test_key')
        
    @patch('pagerduty.EventsApiV2Client')
    def test_trigger_incident_success(self, mock_events_client):
        # Setup
        mock_client = MagicMock()
        mock_client.trigger.return_value = 'dedup-key-123'
        mock_events_client.return_value = mock_client
        
        # Execute
        client = PagerDutyClient(service_id='test_key')
        result = client.trigger_incident(
            summary="Test incident",
            user_info={"name": "Test User", "id": "U123"},
            details={"priority": "high"}
        )
        
        # Assert
        self.assertEqual(result['id'], 'dedup-key-123')
        self.assertEqual(result['status'], 'triggered')
        mock_client.trigger.assert_called_once_with(
            "Test incident", 
            source="Slack Bot",
            custom_details={
                'priority': 'high',
                'triggered_by_user': {"name": "Test User", "id": "U123"}
            }
        )
        
    @patch('pagerduty.EventsApiV2Client')
    def test_trigger_incident_failure(self, mock_events_client):
        # Setup
        mock_client = MagicMock()
        mock_client.trigger.side_effect = Exception("API Error")
        mock_events_client.return_value = mock_client
        
        # Execute
        client = PagerDutyClient(service_id='test_key')
        result = client.trigger_incident(
            summary="Test incident",
            user_info={"name": "Test User", "id": "U123"}
        )
        
        # Assert
        self.assertIsNone(result)
        
    def test_trigger_incident_missing_credentials(self):
        # Test that incident creation fails without credentials
        client = PagerDutyClient(service_id=None)
        result = client.trigger_incident(
            summary="Test incident",
            user_info={"name": "Test User", "id": "U123"}
        )
        
        # Assert
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main() 