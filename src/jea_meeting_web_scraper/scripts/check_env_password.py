"""Check what password is actually being read from .env"""

import os

from jea_meeting_web_scraper.config.settings import settings


def check_password():
    print("🔍 Checking password from environment...\n")

    # Check raw environment variable
    raw_env = os.getenv("APP_PASSWORD")
    print("📋 Raw os.getenv('APP_PASSWORD'):")
    print(f"   Value: {repr(raw_env)}")
    print(f"   Type: {type(raw_env)}")

    # Check pydantic settings
    print("\n📋 From settings.app_password:")
    print(f"   Value: {repr(settings.app_password)}")
    print(f"   Type: {type(settings.app_password)}")
    print(f"   Length: {len(settings.app_password)}")

    # Check if .env file exists
    from pathlib import Path

    env_file = Path(".env")
    print("\n📁 .env file:")
    print(f"   Exists: {env_file.exists()}")
    if env_file.exists():
        print(f"   Path: {env_file.absolute()}")

        # Try to read it (carefully, without exposing full password)
        with open(env_file) as f:
            lines = f.readlines()

        app_password_line = [line for line in lines if line.startswith("APP_PASSWORD")]
        if app_password_line:
            line = app_password_line[0].strip()
            # Show structure without showing full password
            if "=" in line:
                key, value = line.split("=", 1)
                print(f"   Line found: {key}=...")
                print(f"   Value length: {len(value)}")
                print(f"   First 5 chars: {repr(value[:5])}")
                print(
                    f"   Has quotes: {value.startswith('"') or value.startswith("'")}"
                )
        else:
            print("   ⚠️  APP_PASSWORD not found in .env file!")

    if raw_env != settings.app_password:
        print("\n⚠️  WARNING: os.getenv != settings.app_password")
        print("   This suggests pydantic is using a default value")


if __name__ == "__main__":
    check_password()
