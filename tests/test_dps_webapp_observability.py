from fastapi.testclient import TestClient
import sys
import os

# Ensure the project root is in the path
sys.path.insert(0, os.path.abspath(os.getcwd()))

from exporter.webapp.main_ru import app


def test_ru_metrics_endpoint():
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    # Use more basic python/prometheus metrics that should be present on all systems
    assert "python_gc_objects_collected_total" in response.text
    assert "http_request_duration_seconds" in response.text
    print("PASS: /metrics endpoint in Ru app is live and returning system stats.")


def test_ru_status_endpoint():
    client = TestClient(app)
    response = client.get("/status")
    assert response.status_code == 200
    assert "PID" in response.text
    assert "Версия Python" in response.text
    assert "использование памяти" in response.text.lower() or "App Memory Usage" in response.text
    assert "Нагрузка на сервер" in response.text or "Server Load & Performance" in response.text
    print("PASS: /status endpoint in Ru app is functional.")


def test_ru_home_page():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    print("PASS: Ru Home page is functional.")


if __name__ == "__main__":
    try:
        test_ru_metrics_endpoint()
        test_ru_status_endpoint()
        test_ru_home_page()
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)
