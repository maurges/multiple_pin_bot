# Multiple Pin Bot

Telegram bot to
enable pinning multiple messages at once
in telegram groups.
It does so by creating a supermessage of all pins.

## Usage

When the bot is set up and ready,
just pin a message and it will add it to the pinned list.
You can then remove a message just by pressing button.
There also is a button to delete every message except for
the recently pinned one.
This is useful when you want to reset the pinned messages.

## Setup

First you need to obtain the token from BotFather,
the process is described
[here](https://core.telegram.org/bots#6-botfather).
Then you put this token into `token.txt` file in the root directory of this project.
Then you run `python3 main.py`, and your bot is up and operating.

Add the bot to supergroup and make him an admin to see him work.
