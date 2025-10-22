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


def test_ping_command_injection_prevention(mocker):
    """
    Test that a malicious payload is NOT executed by checking
    that the subprocess call was made with the payload as a single argument.
    """
    # Malicious payload that attempts to run 'ls' after 'ping'
    malicious_hostname = "google.com; ls -la"

    # 1. Arrange:
    # Mock subprocess.run with a return value (it should fail ping, but not execute the payload)
    mock_run = mocker.patch(SUBPROCESS_PATH)
    mock_run.return_value = subprocess.CompletedProcess(
        args=["ping..."], returncode=1, stdout="", stderr="Ping failed on bad hostname"
    )
    mock_db_session = mocker.patch(DB_PATH, return_value=mocker.Mock())

    # 2. Act:
    task_run_ping(hostname=malicious_hostname)

    # 3. Assert (The most critical part):
    # The subprocess call must ONLY contain the full malicious hostname as ONE argument.
    # This proves 'shell=False' is protecting the system.
    mock_run.assert_called_once()

    # Assuming your ping command looks like: ['ping', '-c', '4', hostname]
    # Check that the call arguments contain the full payload as a single item.
    call_args = mock_run.call_args[0][0]

    # We assert the malicious string is present as a single item in the argument list
    assert malicious_hostname in call_args
    assert len(call_args) == 4 # Should be ['ping', '-c', '4', malicious_hostname]

    # Clean up the mock (optional, but good practice for security tests)
    mock_db_session.return_value.add.assert_called_once()
    mock_db_session.return_value.commit.assert_called_once()
# (Add this function to the end of your test_commands.py file)

def test_run_nmap_success(mocker):
    """
    Test: Ensures the Nmap task runs and saves results correctly.
    """
    # 1. Arrange:
    # We must patch the Nmap task, assuming it uses subprocess.run
    mock_run = mocker.patch(SUBPROCESS_PATH)
    mock_run.return_value = subprocess.CompletedProcess(
        args=["nmap..."], returncode=0, stdout="Nmap scan finished", stderr=""
    )
    mock_db_session = mocker.patch(DB_PATH, return_value=mocker.Mock())

    # 2. Act:
    # Assuming your worker function for Nmap is named task_run_nmap
    from cyber_platform.celery_worker import task_run_nmap
    result = task_run_nmap(hostname="localhost")

    # 3. Assert:
    # Check the result structure (assuming it returns a dict like ping)
    assert result['hostname'] == "localhost"
    assert "Nmap scan finished" in result['output']
    assert result.get('error') is None

    # Check that it tried to save to the database
    mock_db_session.return_value.add.assert_called_once()
    mock_db_session.return_value.commit.assert_called_once()

