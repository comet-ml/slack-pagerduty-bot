#!/usr/bin/env python3
import logging
from src.slack_bot import SlackPagerDutyBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the Slack PagerDuty Bot."""
    try:
        # Create and start the bot
        bot = SlackPagerDutyBot()
        bot.start()
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
