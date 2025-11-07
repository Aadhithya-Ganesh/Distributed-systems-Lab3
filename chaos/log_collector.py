import subprocess
import datetime
import sys
from pathlib import Path

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')

def main():
    phase = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    folder = Path(f"chaos-logs/{phase}-{timestamp}")
    folder.mkdir(parents=True, exist_ok=True)

    print(f"Collecting logs for phase: {phase}")

    client_res = run("kubectl get pods -l app=client -o jsonpath={.items[0].metadata.name}")
    backend_res = run("kubectl get pods -l app=backend -o jsonpath={.items[0].metadata.name}")
    client_pod = client_res.stdout.strip() if client_res.returncode == 0 else ""
    backend_pod = backend_res.stdout.strip() if backend_res.returncode == 0 else ""

    (folder / "pods.txt").write_text(f"client: {client_pod}\nbackend: {backend_pod}\n", encoding="utf-8")

    if client_pod:
        # container stdout logs
        r = run(f"kubectl logs {client_pod}")
        (folder / "client-pod.log").write_text(r.stdout if r.returncode == 0 else r.stderr, encoding="utf-8")
        # app file log
        r = run(f"kubectl exec {client_pod} -- sh -c \"test -f /app/logs/app.log && tail -n 500 /app/logs/app.log || echo 'NO_APP_LOG'\"")
        (folder / "app.log").write_text(r.stdout, encoding="utf-8")

    if backend_pod:
        r = run(f"kubectl logs {backend_pod}")
        (folder / "backend-pod.log").write_text(r.stdout if r.returncode == 0 else r.stderr, encoding="utf-8")

    # cluster context (optional but helpful)
    (folder / "pods-status.txt").write_text(run("kubectl get pods -o wide").stdout, encoding="utf-8")
    (folder / "services.txt").write_text(run("kubectl get svc -o wide").stdout, encoding="utf-8")

    print("Log collection done:", folder)

if __name__ == "__main__":
    main()
