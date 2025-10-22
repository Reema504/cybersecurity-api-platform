import pytest
import subprocess
from cyber_platform.celery_worker import task_run_ping

# ==================================================================
# Correct paths to mock
# ==================================================================
SUBPROCESS_PATH = 'cyber_platform.celery_worker.subprocess.run'
DB_PATH = 'cyber_platform.celery_worker.SessionLocal'
# ==================================================================


def test_run_ping_success(mocker):
    """
    Test: What happens if the ping command succeeds?
    (Function returns a dict)
    """
    # 1. Arrange:
    mock_run = mocker.patch(SUBPROCESS_PATH)
    mock_run.return_value = subprocess.CompletedProcess(
        args=["ping..."], returncode=0, stdout="Ping successful", stderr=""
    )
    mock_db_session = mocker.patch(DB_PATH, return_value=mocker.Mock())

    # 2. Act:
    result = task_run_ping(hostname="google.com")

    # 3. Assert:
    # --- FIX: Use .get('key') notation to safely check for keys ---
    assert result['hostname'] == "google.com"
    assert "Ping successful" in result['output']
    assert result.get('error') is None # <-- .get() is safer

    mock_db_session.return_value.add.assert_called_once()
    mock_db_session.return_value.commit.assert_called_once()


def test_run_ping_failure(mocker):
    """
    Test: What happens if the ping command fails?
    (Function returns a dict with error info)
    """
    # 1. Arrange:
    mocker.patch(
        SUBPROCESS_PATH,
        side_effect=subprocess.CalledProcessError(returncode=1, cmd=["ping..."], stderr="Host not found")
    )
    mock_db_session = mocker.patch(DB_PATH, return_value=mocker.Mock())

    # 2. Act:
    result = task_run_ping(hostname="fake.host")

    # 3. Assert:
    # --- FIX: Use .get('key') notation to safely check for keys ---
    assert result['hostname'] == "fake.host"
    assert result.get('output') is None # <-- .get() is safer
    assert "Host not found" in result['error']

    mock_db_session.return_value.add.assert_called_once()
    mock_db_session.return_value.commit.assert_called_once()


def test_run_ping_timeout(mocker):
    """
    Test: What happens if the command takes too long (Timeout)?
    (Function RAISES the TimeoutExpired error)
    """
    # 1. Arrange:
    mocker.patch(
        SUBPROCESS_PATH,
        side_effect=subprocess.TimeoutExpired(cmd=["ping..."], timeout=5, stderr="Timeout")
    )
    mock_db_session = mocker.patch(DB_PATH, return_value=mocker.Mock())

    # 2. Act + Assert:
    # We MUST expect the function to raise this error
    with pytest.raises(subprocess.TimeoutExpired):
        task_run_ping(hostname="slow.host")

    # --- FIX: The function crashes BEFORE saving, so db.add is NOT called. ---
    # We must assert that it was called 0 times (or just remove the check).
    mock_db_session.return_value.add.assert_not_called()
    mock_db_session.return_value.commit.assert_not_called()


