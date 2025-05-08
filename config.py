import os
from dotenv import load_dotenv

# Load environment variables from .env file if present (development environment)
load_dotenv()

def get_secret(secret_name, default=None):
    """
    Get a secret from the Kubernetes secrets mount path or environment variable.
    
    In Kubernetes, secrets are mounted as files.
    For local development, secrets are provided via environment variables.
    """
    # Path where Kubernetes would mount secrets
    secret_path = f"/etc/secrets/{secret_name}"
    
    # Check if running in Kubernetes with mounted secrets
    if os.path.exists(secret_path):
        with open(secret_path, "r") as f:
            return f.read().strip()
    
    # Fallback to environment variables (for development)
    return os.environ.get(secret_name, default)

# Slack configuration
SLACK_BOT_TOKEN = get_secret("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = get_secret("SLACK_APP_TOKEN")

# PagerDuty configuration
PAGERDUTY_INTEGRATION_KEY = get_secret("PAGERDUTY_INTEGRATION_KEY")

# General configuration
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
ALLOWED_CHANNELS = os.environ.get("ALLOWED_CHANNELS", "").split(",")
