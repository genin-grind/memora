import os
import json
from pathlib import Path
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_TOKEN")
DEFAULT_CHANNEL_NAME = os.getenv("SLACK_CHANNEL", "all-memora-labs")

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
SYNC_STATE_PATH = BASE_DIR / "data" / "sync_state.json"


def _get_client() -> WebClient:
    if not SLACK_BOT_TOKEN:
        raise ValueError("Missing SLACK_TOKEN in .env")
    return WebClient(token=SLACK_BOT_TOKEN)


def load_sync_state():
    if not SYNC_STATE_PATH.exists():
        return {"slack": {"last_ts": "0"}, "gmail": {"last_fetch_epoch": 0}}
    with open(SYNC_STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_sync_state(state):
    SYNC_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SYNC_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)


def load_existing_messages():
    path = RAW_DIR / "slack_messages.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_messages(messages):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / "slack_messages.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=4, ensure_ascii=False)


def save_users(users_map):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / "slack_users.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(users_map, f, indent=4, ensure_ascii=False)


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
    for channel in get_all_channels(client):
        if channel.get("name") == channel_name:
            return channel.get("id")
    return None


def fetch_users_map(client: WebClient) -> dict:
    users_map = {}
    cursor = None

    while True:
        response = client.users_list(limit=200, cursor=cursor)
        for member in response.get("members", []):
            user_id = member.get("id")
            profile = member.get("profile", {}) or {}
            display_name = profile.get("display_name")
            real_name = profile.get("real_name")
            name = member.get("name")
            users_map[user_id] = display_name or real_name or name or user_id

        cursor = response.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break

    return users_map


def fetch_channel_messages_incremental(channel_name: str | None = None, limit: int = 200) -> list:
    client = _get_client()
    channel_name = channel_name or DEFAULT_CHANNEL_NAME

    try:
        channel_id = get_channel_id(client, channel_name)
        if not channel_id:
            raise ValueError(f"Channel '{channel_name}' not found")

        state = load_sync_state()
        last_ts = state.get("slack", {}).get("last_ts", "0")

        users_map = fetch_users_map(client)
        existing_messages = load_existing_messages()
        existing_ts = {msg.get("ts") for msg in existing_messages}

        response = client.conversations_history(
            channel=channel_id,
            limit=limit,
            oldest=last_ts,
            inclusive=False,
        )

        messages = response.get("messages", [])
        new_messages = []

        for msg in messages:
            ts = msg.get("ts", "")
            if not ts or ts in existing_ts:
                continue

            user_id = msg.get("user", "unknown")
            item = {
                "source": "slack",
                "channel": channel_name,
                "channel_id": channel_id,
                "user": user_id,
                "user_name": users_map.get(user_id, user_id),
                "text": msg.get("text", ""),
                "ts": ts,
                "thread_ts": msg.get("thread_ts", ts),
                "type": msg.get("type", ""),
            }
            new_messages.append(item)

        merged_messages = existing_messages + new_messages
        merged_messages.sort(key=lambda x: float(x.get("ts", "0")))

        save_messages(merged_messages)
        save_users(users_map)

        if merged_messages:
            newest_ts = max((msg.get("ts", "0") for msg in merged_messages), key=float)
            state["slack"]["last_ts"] = newest_ts
            save_sync_state(state)

        print(f"Slack incremental sync complete. New messages: {len(new_messages)}")
        return new_messages

    except SlackApiError as e:
        raise RuntimeError(f"Slack API Error: {e.response['error']}") from e


if __name__ == "__main__":
    fetch_channel_messages_incremental()