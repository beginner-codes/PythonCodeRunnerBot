import bot.bootstrap


logger = bot.bootstrap.setup_logger()
client = bot.bootstrap.create_bot(logger)
bot.bootstrap.load_cogs(client, logger)
bot.bootstrap.run(client, logger)
