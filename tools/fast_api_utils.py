import subprocess
import urllib.parse
import webbrowser


def start_dpd_server():
    "uvicorn exporter.webapp.main_ru:app --host 127.0.0.1 --port 8080 --reload --reload-dir exporter/webapp"
    command = [
        "uvicorn",
        "exporter.webapp.main_ru:app",
        "--host", "127.0.0.1",
        "--port", "8080",
        "--reload",
        "--reload-dir",
        "exporter/webapp",
    ]
    subprocess.Popen(command)


def request_dpd_server(q: str|int):
    base_url = "http://127.0.0.1:8080/sbs/"
    search_params = {"q": q}
    url = f"{base_url}?{urllib.parse.urlencode(search_params)}"
    webbrowser.open(url)


def request_bold_def_server(search_1: str, search_2: str, option: str):
    base_url = "http://127.0.0.2:8080/search"
    search_params = {"search_1": search_1, "search_2": search_2, "option": option}
    url = f"{base_url}?{urllib.parse.urlencode(search_params)}"
    webbrowser.open(url)


if __name__ == "__main__":
    start_dpd_server()
    # request_dpd_server("katakicca")
