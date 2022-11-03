# Timelord
A time management and reminder bot for slack to help with project management and team progress


## Installation
Use the following to set up a python virtual environment for Timelord.
```bash
touch .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Add the following environment variables to the `.env` file

`SLACK_APP_TOKEN=<your slack app token>`

`SLACK_BOT_TOKEN=<your slack bot token>`

## Usage
Run app.py to launch Timelord

### Slash Commands

#### User Commands:
- `/help` Get this list of commands
- `/timelog` Opens a time logging form
- `/deletelast` Delete your last entry
- `/myentries n` Get a table with your last n entries (defaults to 5)

#### Admin Commands:
- `/gethours` Select users and get their total hours logged
- `/allusersums` Get the total hours logged by all users
- `/getusertables` Select users to see their last few entries
- `/allusertable` Responds with the last 30 entries from all users
- `/leaderboard n` Responds with the top n contributors and their total time logged (defaults to 10)
