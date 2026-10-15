"""Local API operations; passwords are accepted only from a hidden prompt."""
import argparse
from datetime import datetime
from getpass import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from inference_api import auth, storage  # noqa: E402
from inference_api.server import serve  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("init-db", "migrate-db", "configure-users",
                                           "set-password",
                                           "revoke", "serve"))
    parser.add_argument("--username", choices=sorted(auth.ALLOWED_USERS))
    parser.add_argument("--pg-dump", default="pg_dump")
    args = parser.parse_args()
    if args.action == "init-db":
        storage.initialize()
        print("db_inference_app schema ready")
    elif args.action == "migrate-db":
        backup = Path(__file__).resolve().parent / ".local" / (
            "identity-backup-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".dump")
        storage.migrate_identity(backup, args.pg_dump)
        print(f"Identity schema ready; logical backup: {backup}")
    elif args.action == "configure-users":
        supplied = {}
        for username in ("Nicoli", "Vinicius"):
            password = getpass(f"{username} password: ")
            confirmation = getpass(f"{username} confirm password: ")
            if password != confirmation:
                parser.error(f"{username} passwords do not match")
            supplied[username] = password
        for username, password in supplied.items():
            auth.set_password(username, password)
        print("Two approved researchers registered; previous sessions revoked")
    elif args.action == "set-password":
        if not args.username:
            parser.error("--username is required")
        password = getpass("Password: ")
        confirmation = getpass("Confirm password: ")
        if password != confirmation:
            parser.error("Passwords do not match")
        auth.set_password(args.username, password)
        print(f"Researcher {args.username} registered; previous sessions revoked")
    elif args.action == "revoke":
        if not args.username:
            parser.error("--username is required")
        auth.revoke(args.username)
        print(f"Researcher {args.username} revoked")
    else:
        serve()


if __name__ == "__main__":
    main()
