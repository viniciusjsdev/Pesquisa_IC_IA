"""Interactive loopback HTTP smoke for the two registered researchers.

Passwords and bearer tokens remain in process memory and are never printed.
"""
import json
from getpass import getpass
from http.server import ThreadingHTTPServer
from pathlib import Path
import sys
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from inference_api.server import Handler  # noqa: E402


class QuietHandler(Handler):
    def log_message(self, *_args) -> None:
        pass


def request(base: str, path: str, token: str = "", body: dict | None = None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = Request(base + path, headers=headers,
                  data=json.dumps(body).encode() if body is not None else None,
                  method="POST" if body is not None else "GET")
    try:
        with urlopen(req, timeout=5) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, json.load(error)


def main() -> int:
    server = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        sessions = {}
        for username in ("Nicoli", "Vinicius"):
            password = getpass(f"{username} password: ")
            status, result = request(base, "/api/login", body={
                "username": username, "password": password})
            password = ""
            if status != 200 or not isinstance(result.get("token"), str):
                print(f"{username}: login failed")
                return 1
            sessions[username] = result["token"]
        for username, token in sessions.items():
            status, result = request(base, "/api/me", token)
            if status != 200 or result.get("username") != username:
                print(f"{username}: session check failed")
                return 1
        for username, token in sessions.items():
            status, _ = request(base, "/api/logout", token, {})
            revoked, _ = request(base, "/api/me", token)
            if status != 200 or revoked != 401:
                print(f"{username}: logout check failed")
                return 1
        print("PASS: both logins coexisted and both sessions were revoked")
        return 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
