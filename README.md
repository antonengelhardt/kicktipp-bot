# kicktipp-bot

This script can automatically enter tips into Kicktipp based on the quotes of the bookmakers. It is written in Python and uses Selenium to interact with the website.

## Run

Copy the contents of the `.env.example` file into a new file called `.env` and fill in the values.

### Python

If you use the [fish shell](https://fishshell.com/), you can use the `envsource .env` command, from [this GitHub Gist](https://gist.github.com/nikoheikkila/dd4357a178c8679411566ba2ca280fcc) to load the environment variables.

```bash
# Install dependencies
pip install -r requirements.txt

# Run the script
python main.py

# Headless mode
python main.py --headless
```

### Docker

Install Docker and run the following commands.

```bash
# Get Image
docker pull ghcr.io/antonengelhardt/kicktipp-bot:amd64

# Run Container and set your env variables
docker run \
-it \
--name kicktipp-bot \
--platform linux/amd64 \
--env-file .env \
ghcr.io/antonengelhardt/kicktipp-bot:amd64
```

or deploy with Kubernetes.

## Environment Variables

| Variable | Description | Example | Required |
| --- | --- | --- | --- |
| `KICKTIPP_EMAIL` | Your Kicktipp email | `email@example.com` | Yes |
| `KICKTIPP_PASSWORD` | Your Kicktipp password | `password` | Yes |
| `KICKTIPP_NAME_OF_COMPETITION` | The name of the competition you want to tip for | `mycoolfriendgroup` | Yes |
| `KICKTIPP_HOURS_UNTIL_GAME` | The script will tip games which start in the next x hours | `24` | No |
| `KICKTIPP_RUN_EVERY_X_MINUTES` | The script will run every x minutes | `60` | No |
| `CHROMEDRIVER_PATH` | The path to the chromedriver binary | `/usr/bin/chromedriver` | No |
| `ZAPIER_URL` | The URL of your Zapier Webhook | `https://hooks.zapier.com/hooks/catch/123456/abcdef/` | No |
| `NTFY_URL` | The URL of your NTFY Webhook | `https://ntfy.your-domain.com` | No |
| `NTFY_USERNAME` | The username for your NTFY Webhook | `username` | No |
| `NTFY_PASSWORD` | The password for your NTFY Webhook | `password` | No |

## Notifications

If you want to receive a notification when the script tips for a match, you can use the Zapier or NTFY integration.

### Zapier

Please create a Zapier Account and set up the following Trigger: Custom Webhook. Please also make sure you set the ENV Variable `ZAPIER_URL` to the URL of your custom webhook. Then you can set up actions like sending an email or a push notification.

### NTFY

Set up your [ntfy](https://github.com/binwiederhier/ntfy?tab=readme-ov-file) server and set the ENV Variables `NTFY_URL`, `NTFY_USERNAME` and `NTFY_PASSWORD` to the values of your server. Create the topic `kicktipp-bot` and subscribe to it. Then you will receive a notification when the script tips for a match.

## Related projects

- [kicktipp-bot-serverless](https://github.com/tbrodbeck/kicktipp-bot-serverless) (written by [tbrodbeck](https://github.com/tbrodbeck)) uses Playwright instead of Selenium and runs as a one time job, so that it can be scheduled by other tools like Cron
