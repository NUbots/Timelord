# Slack block kit - https://api.slack.com/block-kit

from datetime import datetime

# Get current date for time logging form
def currentDate():
    return datetime.now()

# Time logging form blocks
log_form = [
    {
        # Horizontal line
        "type": "divider"
    },
    {
        # Date picker
        "type": "input",
        "block_id": "date_input",
        "element": {
            "type": "datepicker",
            # YYYY-MM-DD format needs to be used here because SQL doesn't have a date data type so these are stored as strings - in this format lexicographical order is identical to chronological order.
            "initial_date": currentDate().strftime("%Y-%m-%d"),
            "placeholder": {
                "type": "plain_text",
                "text": "Select a date",
            },
            "action_id": "select_date"
        },
        "label": {
            "type": "plain_text",
            "text": "Date to log",
        }
    },
    {
        # Hours input
        "type": "input",
        "block_id": "hours_input",
        "element": {
            "type": "plain_text_input",
            "action_id": "select_hours"
        },
        "label": {
            "type": "plain_text",
            "text": "Time logged (e.g. 2h, 25m)",
        }
    },
    {
        # Submit button
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "Click to submit and log hours"
        },
        "accessory": {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "Submit",
            },
            "value": "placeholder",
            "action_id": "timelog_submit"
        }
    }
]

# User selection form for hour sum
user_hours_selection = [
		{
			"type": "input",
            "block_id": "user_input",
			"element": {
				"type": "multi_users_select",
				"placeholder": {
					"type": "plain_text",
					"text": "Select users",
				},
				"action_id": "user_added"
			},
			"label": {
				"type": "plain_text",
				"text": "Select users to view their total time logged",
			}
		},
		{
			"type": "actions",
			"elements": [
				{
					"type": "button",
					"text": {
						"type": "plain_text",
						"text": "Confirm Selection",
					},
					"action_id": "get_user_hours"
				}
			]
		}
]

# User selection form for table
user_table_selection = [
		{
			"type": "input",
            "block_id": "user_input",
			"element": {
				"type": "multi_users_select",
				"placeholder": {
					"type": "plain_text",
					"text": "Select users",
				},
				"action_id": "user_added"
			},
			"label": {
				"type": "plain_text",
				"text": "Select users to their last n entries as a table",
			}
		},
        {
            # Number of entries
            "type": "input",
            "block_id": "num_entries",
            "element": {
                "type": "plain_text_input",
                "action_id": "select_num_entries"
            },
            "label": {
                "type": "plain_text",
                "text": "Number of entries to return for each user",
            }
        },
		{
			"type": "actions",
			"elements": [
				{
					"type": "button",
					"text": {
						"type": "plain_text",
						"text": "Confirm Selection",
					},
					"action_id": "get_user_table"
				},
			]
		}
]
