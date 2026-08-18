from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_execute_command():
    response = client.post('/exec', json={'cmd': 'ls'})
    assert response.status_code == 200
    assert 'output' in response.json()