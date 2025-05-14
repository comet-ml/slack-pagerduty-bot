# Slack PagerDuty Bot

A Slack bot that integrates with PagerDuty to trigger incidents/escalations from Slack channels. This bot is designed to run in shared Slack channels with customers, allowing them to trigger alerts to on-call personnel.

## Features

- Trigger PagerDuty alerts directly from Slack using a slash command (`/escalate`)
- Trigger alerts by mentioning keywords like "alert", "trigger", "escalate", or "page" in a message
- Interactive UI for providing incident details
- Secure deployment on Kubernetes with secrets management
- Socket Mode integration (no need for public webhooks)

## Setup

### Prerequisites

- Python 3.9+
- Slack workspace with admin permissions to create apps
- PagerDuty account with API access
- Kubernetes cluster (for production deployment)

### Slack App Configuration

1. Create a new Slack app at https://api.slack.com/apps
2. Add the following Bot Token Scopes under "OAuth & Permissions":
   - `chat:write`
   - `chat:write.public`
   - `commands`
   - `users:read`
   - `users:read.email`
   - `channels:read` (for channel name resolution)

3. Enable Socket Mode under "Socket Mode" section
4. Create a slash command `/escalate` with the description "Trigger a PagerDuty incident"
5. Install the app to your workspace

### PagerDuty Configuration

This bot uses PagerDuty's Events API v2

1. Create a service in PagerDuty or use an existing one
2. Add an "Events API v2" integration to the service
3. Get the "Integration Key" provided by PagerDuty
4. Use this Integration Key as your `PAGERDUTY_SERVICE_ID` in your configuration


### Local Development

1. Clone this repository
2. Create a `.env` file based on the provided `sample-env`
3. Install dependencies: `pip install -r requirements.txt`
4. Run the bot: `python app.py`

### Docker Deployment

```bash
docker build -t slack-pagerduty-bot .
docker run -p 3000:3000 --env-file .env slack-pagerduty-bot
```

### Kubernetes Deployment

Deploy using Helm:

```bash
helm upgrade --install slack-pagerduty-bot ./helm-chart -f values.yaml
```

See the `helm-chart` directory for Helm chart details and configuration options.

## Usage

### Slash Command

Use the `/escalate` command followed by a description of the issue:

```
/escalate Database servers are not responding
```

### Keyword Mention

Mention one of the trigger keywords in a message:

```
We need to alert the on-call team that the API is down
```

This will prompt an interactive dialog to confirm and provide more details.

## Configuration

Configuration is done through environment variables or Kubernetes secrets:

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| SLACK_BOT_TOKEN | Slack Bot Token (xoxb-) | Yes | - |
| SLACK_APP_TOKEN | Slack App-Level Token (xapp-) | Yes | - |
| PAGERDUTY_INTEGRATION_KEY | PagerDuty Integration Key | Yes | - |
| DEBUG | Enable debug logging | No | False |
| ALLOWED_CHANNELS | Comma-separated list of allowed channel IDs or names | No | All channels |

The `ALLOWED_CHANNELS` setting supports both channel IDs (starting with 'C') and human-readable channel names (like 'general'). Channel names will be automatically resolved to IDs at startup.


## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
