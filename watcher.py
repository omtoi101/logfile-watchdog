from discord_webhook import DiscordWebhook, DiscordEmbed
from dotenv import load_dotenv
import traceback, json, os

class WebhookBuilder:
		def __init__(self, url) -> None:
			self.url = url
			self.webhook = DiscordWebhook(url=self.url, username="Notification bot", avatar_url="https://omtoi101.com/resources/notification2.jpg",  rate_limit_retry=True)
			self.embed = DiscordEmbed(color="EE4B2B")
			self.embed.set_author(name="Alert!", icon_url="https://omtoi101.com/resources/notification.jpg")
		def msg(self, msg, script):
			self.__init__(self.url)
			self.embed.set_title(script)
			self.embed.set_description(msg)
			self.webhook.add_embed(self.embed)
			self.webhook.execute()


load_dotenv()
url = os.getenv('URL')




webhook = WebhookBuilder(url)




try:
    os.makedirs(os.path.join(os.path.dirname(__file__), "watched_logs/"), exist_ok=True)
    with open(os.path.join(os.path.dirname(__file__), "logfiles.json"), "r") as r:
        logs = json.load(r)

    for log in logs:
        logpath = os.path.join(os.path.dirname(__file__), f"watched_logs/{log}.log")
        if not os.path.exists(logpath):
            open(logpath, "x")
    while True:
        with open(os.path.join(os.path.dirname(__file__), "logfiles.json"), "r") as r:
            logs = json.load(r)
        for val in logs:
            with open(os.path.join(os.path.dirname(__file__), f"watched_logs/{val}.log"), "r") as c_log_r:
                c_log = c_log_r.read()
            with open(logs[val], "r") as n_log_r:
                n_log = n_log_r.read()
            if n_log != c_log:
                error = n_log.replace(c_log, "")
                webhook.msg(f"```py\n{error}```", val + " failed!")
                with open(os.path.join(os.path.dirname(__file__), f"watched_logs/{val}.log"), "w") as c_log_w:
                    c_log_w.write(n_log)
except Exception as e:
    traceback_str = ''.join(traceback.format_tb(e.__traceback__)).replace("__", "_")
    webhook.msg(f"`{str(type(e).__name__)}`: {str(e)}\n```py\n{traceback_str}```", "ME :(")