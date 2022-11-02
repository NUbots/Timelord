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

## Autostart
Change the paths in `timelord.service` to match where you have put it, then copy `timelord.serivce` into
`/etc/systemd/system` and finally run `sudo systemctl enable timelord` and `sudo systemctl start timelord`.
Use `sudo systemctl status timelord` to view the program's status.
