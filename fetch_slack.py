import os
import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_TOKEN")
DEFAULT_CHANNEL_NAME = os.getenv("SLACK_CHANNEL", "all-memora-labs")


def _get_client() -> WebClient:
    if not SLACK_BOT_TOKEN:
        raise ValueError("Missing SLACK_TOKEN in .env")
    return WebClient(token=SLACK_BOT_TOKEN)


def get_all_channels(client: WebClient) -> list:
    channels = []
    cursor = None

    while True:
        response = client.conversations_list(
            types="public_channel,private_channel",
            limit=200,
            cursor=cursor,
        )
        channels.extend(response.get("channels", []))
        cursor = response.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break

    return channels


def get_channel_id(client: WebClient, channel_name: str) -> str | None:
    channels = get_all_channels(client)
    for channel in channels:
        if channel.get("name") == channel_name:
            return channel.get("id")
    return None


def fetch_channel_messages(channel_name: str | None = None, limit: int = 100) -> list:
    client = _get_client()
    channel_name = channel_name or DEFAULT_CHANNEL_NAME

    try:
        channel_id = get_channel_id(client, channel_name)
        if not channel_id:
            raise ValueError(f"Channel '{channel_name}' not found")

        response = client.conversations_history(
            channel=channel_id,
            limit=limit,
        )

        messages = response.get("messages", [])
        structured_messages = []

        for msg in messages:
            item = {
                "source": "slack",
                "channel": channel_name,
                "channel_id": channel_id,
                "user": msg.get("user", "unknown"),
                "text": msg.get("text", ""),
                "ts": msg.get("ts", ""),
                "thread_ts": msg.get("thread_ts", msg.get("ts", "")),
                "type": msg.get("type", ""),
            }
            structured_messages.append(item)

        output_dir = os.path.join("data", "raw")
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, "slack_messages.json")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(structured_messages, f, indent=4, ensure_ascii=False)

        print(f"Saved {len(structured_messages)} Slack messages to {file_path}")
        return structured_messages

    except SlackApiError as e:
        raise RuntimeError(f"Slack API Error: {e.response['error']}") from e


if __name__ == "__main__":
    fetch_channel_messages()