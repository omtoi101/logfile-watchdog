from discord_webhook import DiscordWebhook, DiscordEmbed
from dotenv import load_dotenv
import traceback
import json
import os
import time

class WebhookBuilder:
    def __init__(self, url, username, avatar_url):
        self.url = url
        self.webhook = DiscordWebhook(
            url=self.url,
            username=username,
            avatar_url=avatar_url,
            rate_limit_retry=True
        )

    def msg(self, message, title):
        embed = DiscordEmbed(color="EE4B2B")
        embed.set_author(name="Alert!", icon_url=self.webhook.avatar_url)
        embed.set_title(title)
        embed.set_description(message)

        self.webhook.embeds = []
        self.webhook.add_embed(embed)
        self.webhook.execute()

class LogWatcher:
    def __init__(self, log_files_config, webhook_builder, watch_interval=5):
        self.log_files_config = log_files_config
        self.webhook = webhook_builder
        self.watch_interval = watch_interval
        self.file_positions = {}
        self._initialize_log_files()

    def _initialize_log_files(self):
        with open(self.log_files_config, "r") as f:
            self.logs = json.load(f)

        for log_name, log_path in self.logs.items():
            try:
                self.file_positions[log_path] = os.path.getsize(log_path)
            except FileNotFoundError:
                self.file_positions[log_path] = 0

    def check_logs(self):
        try:
            # Configuration can be reloaded on the fly if the file changes.
            with open(self.log_files_config, "r") as f:
                self.logs = json.load(f)

            for log_name, log_path in self.logs.items():
                try:
                    current_size = os.path.getsize(log_path)
                    last_size = self.file_positions.get(log_path, 0)

                    if current_size > last_size:
                        with open(log_path, "r") as f:
                            f.seek(last_size)
                            new_content = f.read()
                            if new_content:
                                self.webhook.msg(f"```\n{new_content}```", f"New content in {log_name}")
                        self.file_positions[log_path] = current_size
                    elif current_size < last_size:
                        # Log file has been truncated or rotated
                        self.webhook.msg(f"Log file `{log_name}` has been truncated or rotated.", "Log file changed")
                        self.file_positions[log_path] = current_size

                except FileNotFoundError:
                    # If the file doesn't exist, just continue.
                    # We keep the old position, so if it reappears, we know where we were.
                    continue
        except Exception as e:
            traceback_str = ''.join(traceback.format_tb(e.__traceback__)).replace("__", "_")
            self.webhook.msg(f"`{str(type(e).__name__)}`: {str(e)}\n```py\n{traceback_str}```", "Log Watcher failed!")

    def watch(self):
        while True:
            self.check_logs()
            time.sleep(self.watch_interval)


if __name__ == "__main__":
    load_dotenv()
    url = os.getenv('URL')
    username = os.getenv('USERNAME', 'Notification bot')
    avatar_url = os.getenv('AVATAR_URL', 'https://omtoi101.com/resources/notification2.jpg')
    watch_interval = int(os.getenv('WATCH_INTERVAL', 5))

    if not url:
        print("Error: Discord webhook URL not found in .env file.")
    else:
        webhook_builder = WebhookBuilder(url, username, avatar_url)
        log_watcher = LogWatcher("logfiles.json", webhook_builder, watch_interval)

        try:
            log_watcher.watch()
        except Exception as e:
            traceback_str = ''.join(traceback.format_tb(e.__traceback__)).replace("__", "_")
            webhook_builder.msg(f"`{str(type(e).__name__)}`: {str(e)}\n```py\n{traceback_str}```", "Log Watcher failed to start!")