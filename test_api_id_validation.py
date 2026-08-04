import subprocess
import os
import sys

def run_info_with_env(env_updates):
    # Clone current environment and update it
    env = os.environ.copy()
    env.update(env_updates)

    # Run a python command that imports info
    # We must set PYTHONPATH to include current directory
    env["PYTHONPATH"] = os.getcwd()

    # We run 'python -c "import info"'
    result = subprocess.run(
        [sys.executable, "-c", "import info"],
        env=env,
        capture_output=True,
        text=True
    )
    return result

def test_valid_api_id():
    # A valid environment with valid API_ID should import cleanly
    env = {
        "API_ID": "123456",
        "API_HASH": "dummyhash",
        "BOT_TOKEN": "12345:dummytoken",
        "ADMINS": "123456",
        "LOG_CHANNEL": "-100123",
        "FILES_DATABASE_URL": "mongodb://localhost:27017/dummy",
        "BIN_CHANNEL": "-100123",
        "URL": "http://localhost:8080/"
    }
    result = run_info_with_env(env)
    output = result.stdout + result.stderr
    assert "API_ID is invalid" not in output

def test_invalid_api_id_non_numeric():
    env = {
        "API_ID": "abc",
        "API_HASH": "dummyhash",
        "BOT_TOKEN": "12345:dummytoken",
        "ADMINS": "123456",
        "LOG_CHANNEL": "-100123",
        "FILES_DATABASE_URL": "mongodb://localhost:27017/dummy",
        "BIN_CHANNEL": "-100123",
        "URL": "http://localhost:8080/"
    }
    result = run_info_with_env(env)
    output = result.stdout + result.stderr
    assert "API_ID is invalid" in output
    assert result.returncode != 0

def test_invalid_api_id_overflow():
    # Value > 2147483647
    env = {
        "API_ID": "6718325900",
        "API_HASH": "dummyhash",
        "BOT_TOKEN": "12345:dummytoken",
        "ADMINS": "123456",
        "LOG_CHANNEL": "-100123",
        "FILES_DATABASE_URL": "mongodb://localhost:27017/dummy",
        "BIN_CHANNEL": "-100123",
        "URL": "http://localhost:8080/"
    }
    result = run_info_with_env(env)
    output = result.stdout + result.stderr
    assert "API_ID is invalid" in output
    assert "32-bit signed integer range" in output
    assert result.returncode != 0

def test_invalid_api_id_negative_or_zero():
    # Value <= 0
    env = {
        "API_ID": "0",
        "API_HASH": "dummyhash",
        "BOT_TOKEN": "12345:dummytoken",
        "ADMINS": "123456",
        "LOG_CHANNEL": "-100123",
        "FILES_DATABASE_URL": "mongodb://localhost:27017/dummy",
        "BIN_CHANNEL": "-100123",
        "URL": "http://localhost:8080/"
    }
    result = run_info_with_env(env)
    output = result.stdout + result.stderr
    assert "API_ID is invalid" in output
    assert result.returncode != 0
