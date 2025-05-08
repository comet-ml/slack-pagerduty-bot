import logging
import re
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from config import SLACK_BOT_TOKEN, SLACK_APP_TOKEN, ALLOWED_CHANNELS
from src.pagerduty import PagerDutyClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class SlackPagerDutyBot:
    """Slack bot that integrates with PagerDuty for incident management."""

    def __init__(self):
        """Initialize the Slack bot with PagerDuty integration."""
        self.app = App(token=SLACK_BOT_TOKEN)
        self.pd_client = PagerDutyClient()
        # Initialize allowed channels mapping
        self.allowed_channel_ids = set()
        self._initialize_allowed_channels()
        self._register_handlers()

    def _initialize_allowed_channels(self):
        """
        Process ALLOWED_CHANNELS config to resolve channel names to IDs.
        Allows specifying channel IDs or names in the config.
        """
        if not ALLOWED_CHANNELS or \
           (len(ALLOWED_CHANNELS) == 1 and not ALLOWED_CHANNELS[0]):
            logger.info("No channel restrictions configured")
            return

        logger.info(f"Resolving allowed channels: {ALLOWED_CHANNELS}")
        
        # Add any channel IDs (starting with C)
        for channel in ALLOWED_CHANNELS:
            if channel.startswith('C'):
                self.allowed_channel_ids.add(channel)
                continue
                
            # For channel names, we need to look them up
            if channel:
                try:
                    # Try to find the channel by name
                    response = self.app.client.conversations_list()
                    for ch in response['channels']:
                        if ch['name'] == channel:
                            self.allowed_channel_ids.add(ch['id'])
                            logger.info(
                                f"Resolved '{channel}' to ID: {ch['id']}"
                            )
                            break
                    else:
                        logger.warning(
                            f"Could not find channel with name: {channel}"
                        )
                except Exception as e:
                    logger.error(
                        f"Error looking up channel '{channel}': {str(e)}"
                    )

        logger.info(f"Allowed channel IDs: {self.allowed_channel_ids}")

    def _is_channel_allowed(self, channel_id):
        """
        Check if a channel is in the allowed list.
        
        Args:
            channel_id: The channel ID to check
            
        Returns:
            bool: True if the channel is allowed, False otherwise
        """
        # If no channels are specified, all are allowed
        if not self.allowed_channel_ids:
            return True
            
        return channel_id in self.allowed_channel_ids

    def _register_handlers(self):
        """Register all message and action handlers."""
        # Listen for messages that mention the bot
        keywords = re.compile(r"alert|trigger|escalate|page", re.IGNORECASE)
        self.app.message(keywords)(self._handle_alert_message)

        # Register command handler for /escalate command
        self.app.command("/escalate")(self._handle_escalate_command)
        
        # Register action handlers
        self.app.action("trigger_alert")(self._handle_trigger_action)
        self.app.action("cancel_alert")(self._handle_cancel_action)

        # Error handler
        self.app.error(self._handle_error)

    def _handle_alert_message(self, message, say):
        """
        Handle messages that might be requesting an alert.
        
        Args:
            message: Message data from Slack
            say: Function to send a response
        """
        logger.info("_handle_alert_message triggered.")
        logger.debug(f"Raw message data: {message}")

        user_id = message.get("user")
        channel_id = message.get("channel")
        text = message.get("text", "")

        logger.debug(f"Extracted UID: {user_id}, CID: {channel_id}")

        if not channel_id:
            logger.warning("Channel ID is None, cannot proceed.")
            return

        if not user_id:
            logger.warning("User ID is None, cannot post ephemeral message.")
            return

        is_allowed = self._is_channel_allowed(channel_id)
        logger.debug(f"Channel {channel_id} allowed: {is_allowed}")

        # Check if in allowed channels
        if not is_allowed:
            logger.info(
                f"Ignoring message from non-allowed channel {channel_id}"
            )
            return

        # User info fetch was here, but removed as it's unused here.

        # Ask for confirmation before triggering alert
        try:
            logger.debug(f"Attempting ephemeral to u:{user_id} c:{channel_id}")
            self.app.client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text="Do you want to trigger a PagerDuty alert?",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": (
                                "Do you want to trigger a PagerDuty alert? "
                                "This will page the on-call team."
                            )
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "alert_details",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "alert_summary",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Describe the issue..."
                            },
                            "multiline": True
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Issue details"
                        }
                    },
                    {
                        "type": "actions",
                        "block_id": "alert_actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Trigger Alert"
                                },
                                "style": "danger",
                                "value": text,
                                "action_id": "trigger_alert"
                            },
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Cancel"
                                },
                                "value": "cancel",
                                "action_id": "cancel_alert"
                            }
                        ]
                    }
                ]
            )
            logger.debug(f"Ephemeral sent to u:{user_id} c:{channel_id}")
        except Exception as e:
            logger.error(f"Error sending ephemeral: {str(e)}", exc_info=True)

    def _handle_escalate_command(self, ack, command, respond):
        """
        Handle the /escalate slash command.
        
        Args:
            ack: Function to acknowledge the command
            command: Command data from Slack
            respond: Function to send a response
        """
        ack()
        user_id = command.get("user_id")
        channel_id = command.get("channel_id")
        text = command.get("text", "")

        # Check if in allowed channels
        if not self._is_channel_allowed(channel_id):
            respond("Sorry, this command is not available in this channel.")
            return

        # Get user info
        try:
            user_info_data = self.app.client.users_info(user=user_id)["user"]
            user_name = user_info_data.get(
                "real_name", user_info_data.get("name", "Unknown")
            )
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            user_name = "Unknown User"

        # If there's text, treat it as the alert summary
        if text:
            incident = self._trigger_pagerduty_alert(
                summary=text,
                user_info={
                    "name": user_name,
                    "id": user_id,
                    "channel": channel_id
                }
            )
            
            if incident:
                respond(
                    f"🚨 PagerDuty alert triggered by {user_name}.\n"
                    f"Incident ID: {incident.get('id')}\n"
                    f"Summary: {text}"
                )
            else:
                respond(
                    "Failed to trigger PagerDuty alert. "
                    "Please try again later."
                )
        else:
            # No text provided, prompt for details
            respond(
                "Please provide details with the command, "
                "e.g., `/escalate Database is down`"
            )

    def _handle_trigger_action(self, ack, body, respond):
        """
        Handle the button click to trigger an alert.
        
        Args:
            ack: Function to acknowledge the action
            body: Action data from Slack
            respond: Function to send a response
        """
        ack()
        user_id = body.get("user", {}).get("id")
        
        # Get input values
        values = body.get("state", {}).get("values", {})
        alert_details = values.get("alert_details", {})
        summary_field = alert_details.get("alert_summary", {})
        alert_summary = summary_field.get("value", "No details provided")
        
        # Get user info
        try:
            user_info_data = self.app.client.users_info(user=user_id)["user"]
            user_name = user_info_data.get(
                "real_name", user_info_data.get("name", "Unknown")
            )
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            user_name = "Unknown User"

        # Trigger PagerDuty alert
        incident = self._trigger_pagerduty_alert(
            summary=alert_summary,
            user_info={
                "name": user_name,
                "id": user_id,
                "channel": body.get("channel", {}).get("id")
            }
        )
        
        if incident:
            respond(
                f"🚨 PagerDuty alert triggered by {user_name}.\n"
                f"Incident ID: {incident.get('id')}\n"
                f"Summary: {alert_summary}"
            )
        else:
            respond(
                "Failed to trigger PagerDuty alert. "
                "Please try again later."
            )

    def _handle_cancel_action(self, ack, respond):
        """
        Handle the button click to cancel an alert.
        
        Args:
            ack: Function to acknowledge the action
            respond: Function to send a response
        """
        ack()
        respond("Alert canceled.")

    def _trigger_pagerduty_alert(self, summary, user_info, details=None):
        """
        Trigger a PagerDuty alert.
        
        Args:
            summary: Brief description of the incident
            user_info: Information about the user who triggered the incident
            details: Additional details about the incident
            
        Returns:
            dict: The created incident data or None if failed
        """
        return self.pd_client.trigger_incident(
            summary=summary,
            user_info=user_info,
            details=details
        )

    def _handle_error(self, error, body):
        """
        Global error handler for the Slack app.
        
        Args:
            error: Error object
            body: Request body
        """
        logger.error(f"Error: {error}")
        logger.debug(f"Request body: {body}")

    def start(self):
        """Start the Slack bot in Socket Mode."""
        if not SLACK_APP_TOKEN or not SLACK_BOT_TOKEN:
            raise ValueError(
                "SLACK_APP_TOKEN and SLACK_BOT_TOKEN must be provided"
            )
            
        logger.info("Starting Slack bot in Socket Mode...")
        handler = SocketModeHandler(self.app, SLACK_APP_TOKEN)
        handler.start() 