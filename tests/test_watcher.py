import pytest
from unittest.mock import patch, Mock
from watcher import WebhookBuilder

@patch('watcher.DiscordWebhook')
def test_webhook_builder_sends_message(mock_discord_webhook):
    # Arrange
    mock_webhook_instance = Mock()
    mock_discord_webhook.return_value = mock_webhook_instance

    url = "http://fake-webhook-url.com"
    username = "Test Bot"
    avatar_url = "http://fake-avatar-url.com/img.jpg"

    webhook_builder = WebhookBuilder(url, username, avatar_url)

    message = "This is a test message."
    title = "Test Alert"

    # Act
    webhook_builder.msg(message, title)

    # Assert
    mock_discord_webhook.assert_called_once_with(
        url=url,
        username=username,
        avatar_url=avatar_url,
        rate_limit_retry=True
    )

    # Check that add_embed was called, and inspect the embed it was called with.
    mock_webhook_instance.add_embed.assert_called_once()
    added_embed = mock_webhook_instance.add_embed.call_args[0][0]

    assert added_embed.description == message
    assert added_embed.title == title
    assert added_embed.author['name'] == "Alert!"

    mock_webhook_instance.execute.assert_called_once()


from watcher import LogWatcher
import json

def test_log_watcher_detects_new_content(tmp_path):
    # Arrange
    log_file = tmp_path / "test.log"
    log_file.write_text("line 1\n")

    log_config = {"test_log": str(log_file)}
    config_file = tmp_path / "logfiles.json"
    config_file.write_text(json.dumps(log_config))

    mock_webhook = Mock()
    watcher = LogWatcher(str(config_file), mock_webhook, watch_interval=0)

    # Act
    log_file.write_text("line 1\nline 2\n")
    watcher.check_logs()

    # Assert
    mock_webhook.msg.assert_called_once()
    message, title = mock_webhook.msg.call_args[0]
    assert "line 2" in message
    assert "New content in test_log" in title

def test_log_watcher_detects_truncation(tmp_path):
    # Arrange
    log_file = tmp_path / "test.log"
    log_file.write_text("line 1\nline 2\n")

    log_config = {"test_log": str(log_file)}
    config_file = tmp_path / "logfiles.json"
    config_file.write_text(json.dumps(log_config))

    mock_webhook = Mock()
    watcher = LogWatcher(str(config_file), mock_webhook, watch_interval=0)

    # Act
    log_file.write_text("new content\n")
    watcher.check_logs()

    # Assert
    mock_webhook.msg.assert_called_once_with(
        "Log file `test_log` has been truncated or rotated.", "Log file changed"
    )

def test_log_watcher_no_changes(tmp_path):
    # Arrange
    log_file = tmp_path / "test.log"
    log_file.write_text("line 1\n")

    log_config = {"test_log": str(log_file)}
    config_file = tmp_path / "logfiles.json"
    config_file.write_text(json.dumps(log_config))

    mock_webhook = Mock()
    watcher = LogWatcher(str(config_file), mock_webhook, watch_interval=0)

    # Act
    watcher.check_logs()

    # Assert
    mock_webhook.msg.assert_not_called()

def test_log_watcher_file_not_found_then_appears(tmp_path):
    # Arrange
    log_file = tmp_path / "test.log"
    # log_file does not exist yet

    log_config = {"test_log": str(log_file)}
    config_file = tmp_path / "logfiles.json"
    config_file.write_text(json.dumps(log_config))

    mock_webhook = Mock()
    watcher = LogWatcher(str(config_file), mock_webhook, watch_interval=0)

    # Act & Assert (round 1, file not found)
    watcher.check_logs()
    mock_webhook.msg.assert_not_called()
    assert watcher.file_positions[str(log_file)] == 0

    # Act & Assert (round 2, file appears)
    log_file.write_text("new content")
    watcher.check_logs()
    mock_webhook.msg.assert_called_once()
    message, title = mock_webhook.msg.call_args[0]
    assert "new content" in message
