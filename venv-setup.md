Use the following to set up a python virtual environment for Timelord.
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install slack_bolt

export SLACK_APP_TOKEN=<your slack app token>
export SLACK_BOT_TOKEN=<your slack bot token>
```