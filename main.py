import os
import time
from slackclient import SlackClient


BOT_NAME = 'librarian'

# Instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

# Get the bot's ID
BOT_ID = os.environ.get("BOT_ID")

VALID_COMMANDS = set(['search'])

AT_BOT = "<@" + BOT_ID + ">"

def get_bot_id():
    api_call = slack_client.api_call("users.list")
    if api_call.get('ok'):
        # Get all the users in the team
        users = api_call.get('members')
        for user in users:
            if 'name' in user and user.get('name') == BOT_NAME:
                print "Bot ID for {} is {}".format(user['name'], user.get('id'))
                return user.get('id')
    else:
        print "Did not find bot user with the name {}".format(BOT_NAME)


def handle_command(command, channel):
    """Receives commands directed at the bot and determines
    if the commands are valid. If so, acts on the command.
    If not, returns help text.
    """
    help_text = "Only accepting search commands for now..."
    if command in VALID_COMMANDS:
        help_text = "Searching..."
    slack_client.api_call("chat.postMessage", channel=channel,
                          text=help_text, as_user=True)


def parse_slack_output(slack_rtm_output):
    """Parse Slack RTM API events firehouse to return None
    unless a message is directed at the bot bases on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                return output['text'].split(AT_BOT)[1].strip().lower(), output['channel']

    return None, None


if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1  # 1-second delay between reading from firehose
    if slack_client.rtm_connect():
        print "Librarian connected and running!"
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print "Connection failed. Invalid Slack token or bot ID?"
