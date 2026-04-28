"""Pytest hooks — keep RSS/network-heavy startup optional in CI."""

import os

os.environ["NEWS_SYNC_ON_STARTUP"] = "false"
os.environ["ASEAN_SYNC_ON_STARTUP"] = "false"
# Tests need a SECRET_KEY (the API hard-fails without one). Use a fixed
# throwaway value — CI doesn't sign real tokens against this.
os.environ.setdefault(
    "SECRET_KEY",
    "test-only-secret-do-not-use-in-prod-1234567890abcdef",
)
os.environ.setdefault("ENVIRONMENT", "development")
