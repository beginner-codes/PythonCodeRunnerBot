# Python Code Runner Discord Bot

This is a simple bot for running Python code through Discord. It was originally developed for the [Beginner.Codes](https://discord.gg/sfHykntuGy) Discord server.

> _**⚠️ USE AT YOUR OWN RISK ⚠️**_
> 
> This bot will allow any user to run Python code on the computer that is running the bot. The bot is designed to do this in as safe a manner as possible. There is no way to be 100% certain that it cannot be hacked.

## Requirements
The bot uses [Poetry](https://python-poetry.org/) for packaging and dependency management. You will need to follow the [installation instructions](https://python-poetry.org/docs/#installation) before you can get started with the bot.

Additionally, you will need a bot token from Discord. You can read about how to get yours [here](https://realpython.com/how-to-make-a-discord-bot-python/#creating-an-application).

## Configuration & Setup
First things first, we need to install the dependencies. To do that install Poetry by running:
```sh
python -m pip install poetry
```
Next run Poetry to install the bot dependencies.
```sh
poetry install
```
Next you need to configure the bot with the local dev settings. To do this copy the `example.yaml` file and name the new copy `production.yaml`. 

Once that’s done open it up and in the `bot` section change the `token` string to your bot token.

## Running
To run the bot you’ll need to be in the directory which you cloned the repo, and run the following command:
```sh
poetry run python -m bot
```
This will create a virtual environment with all the required dependencies and run the bot.
