import pytest
from starlette.testclient import TestClient
from cyber_platform.main import app

# We need to mock the Celery task calls so we don't actually run system commands
@pytest.fixture(autouse=True)
def mock_celery_tasks(mocker):
    # نحدد قيمة ليرجعها الكائن المُحاكاة، مع توفير خاصية 'id' كما هو متوقع في main.py
    MockTask = mocker.Mock()
    MockTask.id = "mock-task-id-123"

    mocker.patch('cyber_platform.main.task_run_ping.delay', return_value=MockTask)
    mocker.patch('cyber_platform.main.task_run_nmap.delay', return_value=MockTask)
# FIXTURE: Defines the HTTP client (Synchronous TestClient)
@pytest.fixture
def client():

    return TestClient(app)

# ----------------------------------------------------------------------
# TESTS START HERE
# ----------------------------------------------------------------------
 
def test_read_root(client: TestClient):
    response = client.get("/") 
    assert response.status_code == 200
    assert "Welcome" in response.json()['message']


def test_post_ping_task(client: TestClient):
    response = client.post("/ping/test.com")
    assert response.status_code == 200
    assert "task_id" in response.json()
    assert "queued" in response.json()['status']


def test_post_nmap_task(client: TestClient):
    response = client.post("/scan/nmap/test.com")
    assert response.status_code == 200
    assert "task_id" in response.json()
    assert "queued" in response.json()['status']
