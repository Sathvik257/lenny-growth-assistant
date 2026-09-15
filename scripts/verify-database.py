"""Run tests against an existing dedicated PostgreSQL test database without exposing its URL."""
import os
import subprocess
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from backend.config import settings


def main():
    cfg = settings()
    with create_engine(cfg.database_url, connect_args={'connect_timeout':5}).connect() as connection:
        names = connection.execute(text("SELECT datname FROM pg_database WHERE datname LIKE '%_test' ORDER BY datname")).scalars().all()
    if not names:
        raise SystemExit('Create a dedicated database ending in _test before running this check.')
    env = os.environ.copy()
    env['TEST_DATABASE_URL'] = cfg.database_url.rsplit('/', 1)[0] + '/' + names[0]
    result = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-o', 'cache_dir=.runtime/final-pytest-cache'],
                            env=env, capture_output=True, text=True, timeout=120)
    output = (result.stdout + result.stderr).replace(str(Path.cwd()), '<project>')
    Path('agent-transcripts/final-backend-tests.txt').write_text(output, encoding='utf-8')
    print(output)
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
