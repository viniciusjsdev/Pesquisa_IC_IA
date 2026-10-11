"""Manage an isolated Windows PostgreSQL cluster; never uses the system service."""
import argparse
import os
from pathlib import Path
import secrets
import subprocess

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / '.local'
DATA = LOCAL / 'postgres'
ENV = ROOT / '.env.local'
PORT = 5544


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['start', 'status', 'stop'])
    parser.add_argument('--pg-bin', type=Path, default=Path(r'C:\Program Files\PostgreSQL\15\bin'))
    args = parser.parse_args()
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

    def run(executable, *params, check=True):
        return subprocess.run([str(args.pg_bin / executable), *map(str, params)],
                              check=check, creationflags=flags)

    if args.action != 'start':
        if not (DATA / 'PG_VERSION').exists():
            raise SystemExit('Local cluster has not been initialized.')
        extra = ['-m', 'fast', '-w'] if args.action == 'stop' else []
        raise SystemExit(run('pg_ctl.exe', '-D', DATA, args.action, *extra, check=False).returncode)

    LOCAL.mkdir(exist_ok=True)
    if not (DATA / 'PG_VERSION').exists():
        if DATA.exists() or ENV.exists():
            raise SystemExit('Existing local files found; refusing to overwrite them.')
        password = secrets.token_urlsafe(32)
        lines = []
        for domain, database in [('INDUSTRIAL', 'db_industrial'),
                                 ('FINANCEIRO', 'db_financeiro')]:
            for key, value in dict(HOST='127.0.0.1', PORT=PORT, NAME=database,
                                   USER='pesquisa_local', PASSWORD=password).items():
                lines.append(f'{domain}_DB_{key}={value}')
        ENV.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        pwfile = LOCAL / 'init-password.tmp'
        try:
            pwfile.write_text(password, encoding='utf-8')
            run('initdb.exe', '-D', DATA, '-U', 'pesquisa_local', '--encoding=UTF8',
                '--locale=C', '--auth=scram-sha-256', f'--pwfile={pwfile}')
        finally:
            pwfile.unlink(missing_ok=True)
        with (DATA / 'postgresql.conf').open('a', encoding='utf-8') as f:
            f.write(f"\nlisten_addresses = '127.0.0.1'\nport = {PORT}\ntimezone = 'UTC'\n")
    if not ENV.exists():
        raise SystemExit('Missing .env.local; refusing to regenerate credentials.')
    if run('pg_ctl.exe', '-D', DATA, 'status', check=False).returncode != 0:
        run('pg_ctl.exe', '-D', DATA, '-l', LOCAL / 'postgres.log', '-w', 'start')
    print(f'Local PostgreSQL: 127.0.0.1:{PORT}; credentials in ignored .env.local')


if __name__ == '__main__':
    main()
