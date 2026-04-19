"""Pytest hooks — keep RSS/network-heavy startup optional in CI."""

import os

os.environ["NEWS_SYNC_ON_STARTUP"] = "false"
