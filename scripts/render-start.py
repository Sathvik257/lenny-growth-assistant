"""Single-container Render startup with failure propagation and signal cleanup."""
import os
import signal
import subprocess
import sys
import time
import urllib.request


def main():
    port = int(os.environ.get('PORT', '10000'))
    if not 1024 <= port <= 65535:
        raise SystemExit('PORT must be between 1024 and 65535.')
    children = []
    stopping = False

    def stop(signum, frame):
        nonlocal stopping
        stopping = True
        for child in children:
            if child.poll() is None:
                child.terminate()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        # Free services have no preDeployCommand; import before API startup.
        ingest = subprocess.Popen([sys.executable, '-m', 'backend.ingest'])
        children.append(ingest)
        if ingest.wait(timeout=600) != 0:
            return 1
        if stopping:
            return 0
        agent = subprocess.Popen(['node', 'agent/server.mjs'])
        children.append(agent)
        deadline = time.monotonic() + 120
        while not stopping:
            if agent.poll() is not None:
                return 1
            try:
                with urllib.request.urlopen(os.environ.get('AGENT_URL', 'http://127.0.0.1:8788') + '/health', timeout=2) as response:
                    if response.status == 200:
                        break
            except OSError:
                pass
            if time.monotonic() >= deadline:
                raise TimeoutError('Agent startup deadline exceeded.')
            time.sleep(0.5)
        if stopping:
            return 0
        api = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'backend.main:app',
                                '--host', '0.0.0.0', '--port', str(port), '--workers', '1'])
        children.append(api)
        while not stopping:
            if agent.poll() is not None or api.poll() is not None:
                print('A required service exited; stopping the container.', flush=True)
                return 1
            time.sleep(0.5)
        return 0
    except (OSError, subprocess.TimeoutExpired, TimeoutError) as error:
        print(f'Container startup failed: {type(error).__name__}', flush=True)
        return 1
    finally:
        stop(None, None)
        for child in children:
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


if __name__ == '__main__':
    sys.exit(main())
