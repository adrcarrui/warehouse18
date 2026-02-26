import os
import sys
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# ====== Configuración de TU proyecto ======
ASGI_APP = "warehouse18.presentation.api.main:app"
FRONTEND_DIR = BASE_DIR / "frontend" / "warehouse18-ui"
BACKEND_PORT = "8000"
# ===========================================

def get_python_executable():
    if os.name == "nt":
        python_exec = BASE_DIR / ".venv" / "Scripts" / "python.exe"
    else:
        python_exec = BASE_DIR / ".venv" / "bin" / "python"

    if not python_exec.exists():
        raise SystemExit(f"No encuentro el Python del venv en: {python_exec}")

    return str(python_exec)


def get_npm():
    if os.name == "nt":
        npm = shutil.which("npm.cmd") or shutil.which("npm")
    else:
        npm = shutil.which("npm")

    if not npm:
        raise SystemExit("No encuentro npm en el PATH.")

    return npm


def run_backend():
    python_exec = get_python_executable()

    env = os.environ.copy()
    env["PYTHONPATH"] = str(BASE_DIR / "src")

    cmd = [
        python_exec,
        "-m",
        "uvicorn",
        ASGI_APP,
        "--reload",
        "--app-dir",
        "src",
        "--port",
        BACKEND_PORT,
    ]

    print("🚀 Backend:", " ".join(cmd))
    return subprocess.Popen(cmd, env=env)


def run_frontend():
    npm = get_npm()

    pkg = FRONTEND_DIR / "package.json"
    if not pkg.exists():
        raise SystemExit(f"No existe {pkg}")

    cmd = [npm, "run", "dev"]

    print("🎨 Frontend:", " ".join(cmd), f"(cwd={FRONTEND_DIR})")
    return subprocess.Popen(cmd, cwd=str(FRONTEND_DIR))


def kill_process(proc):
    if not proc:
        return

    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        proc.terminate()


def main():
    if len(sys.argv) < 2:
        print("Uso: python run.py [all|backend|frontend]")
        sys.exit(1)

    mode = sys.argv[1].lower()

    backend_proc = None
    frontend_proc = None

    try:
        if mode == "backend":
            backend_proc = run_backend()
            backend_proc.wait()

        elif mode == "frontend":
            frontend_proc = run_frontend()
            frontend_proc.wait()

        elif mode == "all":
            backend_proc = run_backend()
            frontend_proc = run_frontend()

            backend_proc.wait()
            frontend_proc.wait()

        else:
            print("Modo inválido. Usa: all | backend | frontend")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n🛑 Deteniendo procesos...")
        kill_process(backend_proc)
        kill_process(frontend_proc)
        sys.exit(0)


if __name__ == "__main__":
    main()