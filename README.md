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
- `/timelog` Open a time logging form
- `/deletelast` Delete your last entry
- `/myentries n` Get your last n entries (defaults to 5)"""

#### Admin Commands:
- `/timelog` Open a time logging form
- `/deletelast` Delete your last entry
- `/myentries n` Get your last n entries (defaults to 30)"""
- `/gethours` Select users and see their total hours logged
- `/getentries` Select users and see their most recent entries
- `/lastentries n` See the last n entries from all users in one list (defaults to 30)
- `/leaderboard` Select a date range and rank all users by hours logged in that range
- `/dateoverview` See all entries for a given date"""

## Autostart
Change the paths in `timelord.service` to match where you have put it, then copy `timelord.serivce` into
`/etc/systemd/system` and finally run `sudo systemctl enable timelord` and `sudo systemctl start timelord`.
Use `sudo systemctl status timelord` to view the program's status.

