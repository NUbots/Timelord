# Slack block kit - https://api.slack.com/block-kit

from datetime import datetime

# Get current date for time logging form
def currentDate():
    return datetime.now()

# Time logging form blocks
def log_form():
    output = [
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
    return output

# User selection form for hour sum

def time_range_selection(output_func):
    output = [
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "Choose a date range"
			},
			"accessory": {
				"type": "static_select",
				"placeholder": {
					"type": "plain_text",
					"text": "Select an item"
				},
				"options": [
					{
						"text": {
							"type": "plain_text",
							"text": "This Week"
						},
						"value": "weekly"
					},
					{
						"text": {
							"type": "plain_text",
							"text": "This month"
						},
						"value": "month"
					},
					{
						"text": {
							"type": "plain_text",
							"text": "all"
						},
						"value": "all"
					}
				],
				"action_id": "picked_time_range"
			}
		},
		{
			"type": "actions",
			"elements": [
				{
					"type": "button",
					"text": {
						"type": "plain_text",
						"text": "Confirm Selection"
					},
                    # This needs to be changed to use the values from the block input in the request
                    "value": output_func,
					"action_id": "time_range_submit"
				}
			]
		}
    ]
    return output

def user_hours_selection():
    output = [
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
    return output

# User selection form for table
def user_table_selection():
    output = [
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
    return output
