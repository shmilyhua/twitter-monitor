# Twitter Monitor

Monitor the `tweet` and `profile` updates of an X (formerly Twitter) user and send real-time alerts to a Telegram channel.

Data is crawled directly from the X Web GraphQL API.

## Deployed channel sample

https://t.me/twitter_monitor_menu

## Usage

### Setup

(Requires **uv**)

Clone the repository and install dependencies using `uv` to automatically manage the virtual environment and `pyproject.toml` packages.

```bash
git clone https://github.com/shmilyhua/twitter-monitor.git
cd twitter-monitor
uv venv --python 3.13
uv sync
```

### Prepare required tokens

* Create a Telegram bot and get its token:

  https://t.me/BotFather

* Unofficial Twitter account auth:

  You must extract auth cookies from a logged-in browser session using an extension (e.g., Get cookies.txt LOCALLY). Modify the yourusername.json with what you found in the cookies.txt.

### Fill in config

* First, make a copy from the config templates:

  ```bash
  cp ./config/token.json.template ./config/token.json
  cp ./config/monitoring.json.template ./config/monitoring.json
  ```

* Edit `config/token.json`:

  1. Fill in `telegram_bot_token`.
  2. Fill in `twitter_auth_username_list` according to your prepared Twitter account auth.
  3. Verify whether the tokens can be used by running:

  ```bash
  uv run main.py check-tokens
  ```

\* Edit `config/monitoring.json`:

* Edit `config/monitoring.json`:

  *(You need to fill in Telegram chat IDs here. You can retrieve them from https://t.me/userinfobot and https://t.me/myidbot)*

  1. If you need to view monitor health information (starting summary, daily summary, alerts), fill in `maintainer_chat_id`.
  2. Fill in one or more users to `monitoring_user_list`, along with their notification Telegram chat ID, weight, and which monitors to enable. The greater the weight, the higher the query frequency. The **profile monitor** is forced to enable (because it triggers the tweet monitor), and the tweet monitor can be optionally enabled.
  3. Verify if your Telegram token and chat ID are correct by running:

  ```bash
  uv run main.py check-tokens --telegram_chat_id {your_chat_id}
  ```

### Run

Start the monitoring process:

```bash

uv run main.py run

 ```

|Flag|Default|Description|
|:-:|:-:|:-:|
|--interval|15|Monitor run interval|
|--confirm|False|Confirm with the maintainer during initialization|
|--listen_exit_command|False|Listen for the "exit" command from telegram maintainer chat id|
|--send_daily_summary|False|Send daily summary to telegram maintainer|

## Contact me

Telegram: [@ionic_bond](https://t.me/ionic_bond)

## Donate

[PayPal Donate](https://www.paypal.com/donate/?hosted_button_id=D5DRBK9BL6DUA) or [PayPal](https://paypal.me/ionicbond3)


