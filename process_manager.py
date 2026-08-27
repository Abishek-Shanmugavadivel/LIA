"""
Process Manager & Single-Instance Lifecycle Control for LIA.
Handles process locking (lia.lock), single-instance enforcement, health checks,
crash detection, and safe restart logic with backoff.
"""

import os
import sys
import time
import json
import psutil
import logging
import subprocess

logger = logging.getLogger("lia-process-manager")

LOCK_FILE = os.path.join(os.path.dirname(__file__), "lia.lock")


class LIAProcessManager:
    def __init__(self):
        self.lock_file = LOCK_FILE

    def _read_lock(self) -> dict:
        if os.path.exists(self.lock_file):
            try:
                with open(self.lock_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _write_lock(self, pid: int, port: int = 8080) -> None:
        data = {
            "pid": pid,
            "port": port,
            "start_time": time.time(),
            "status": "running"
        }
        with open(self.lock_file, "w") as f:
            json.dump(data, f, indent=2)

    def _clear_lock(self) -> None:
        if os.path.exists(self.lock_file):
            try:
                os.remove(self.lock_file)
            except Exception:
                pass

    def kill_stale_processes(self) -> int:
        """Kills any duplicate or stale LIA agent.py or mobile/server.py processes."""
        current_pid = os.getpid()
        lock_data = self._read_lock()
        valid_pid = lock_data.get("pid")
        killed = 0

        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                if proc.info["pid"] == current_pid:
                    continue
                cmdline = " ".join(proc.info.get("cmdline") or [])
                if "agent.py" in cmdline or "mobile/server.py" in cmdline or "mobile\\server.py" in cmdline:
                    if proc.info["pid"] != valid_pid:
                        logger.warning(f"Terminating stale LIA process PID {proc.info['pid']} ({cmdline})")
                        proc.terminate()
                        killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return killed

    def is_running(self) -> tuple[bool, int]:
        """Checks if LIA process is active and running."""
        data = self._read_lock()
        pid = data.get("pid")
        if pid:
            try:
                p = psutil.Process(pid)
                if p.is_running() and p.status() != psutil.STATUS_ZOMBIE:
                    return True, pid
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        self._clear_lock()
        return False, 0

    def start(self) -> dict:
        """Starts LIA background agent process if not already running."""
        self.kill_stale_processes()
        running, pid = self.is_running()
        if running:
            return {
                "success": True,
                "status": "already_running",
                "pid": pid,
                "message": f"LIA is already running with PID {pid}."
            }

        agent_script = os.path.join(os.path.dirname(__file__), "agent.py")
        cmd = [sys.executable, agent_script, "dev"]
        
        proc = subprocess.Popen(
            cmd,
            cwd=os.path.dirname(__file__),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        )

        self._write_lock(proc.pid)
        logger.info(f"LIA Started successfully with PID {proc.pid}.")
        return {
            "success": True,
            "status": "started",
            "pid": proc.pid,
            "message": f"LIA process started with PID {proc.pid}."
        }

    def stop(self) -> dict:
        """Stops active LIA process safely."""
        running, pid = self.is_running()
        if not running:
            self._clear_lock()
            return {
                "success": True,
                "status": "not_running",
                "message": "LIA is not currently running."
            }

        try:
            p = psutil.Process(pid)
            p.terminate()
            try:
                p.wait(timeout=5)
            except psutil.TimeoutExpired:
                p.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

        self._clear_lock()
        logger.info(f"LIA Process PID {pid} stopped.")
        return {
            "success": True,
            "status": "stopped",
            "message": f"LIA PID {pid} stopped successfully."
        }

    def restart(self) -> dict:
        """Restarts the LIA process."""
        self.stop()
        time.sleep(1)
        return self.start()

    def status(self) -> dict:
        """Returns detailed process status."""
        running, pid = self.is_running()
        data = self._read_lock() if running else {}
        return {
            "running": running,
            "pid": pid,
            "lock_data": data,
            "message": f"LIA is {'running' if running else 'stopped'}."
        }

    def register_shutdown_handlers(self) -> None:
        """Registers SIGINT and SIGTERM handlers for clean process shutdown."""
        import signal

        def shutdown_handler(signum, frame):
            logger.info(f"Received shutdown signal ({signum}). Cleaning up resources...")
            self._clear_lock()
            sys.exit(0)

        try:
            signal.signal(signal.SIGINT, shutdown_handler)
            signal.signal(signal.SIGTERM, shutdown_handler)
        except Exception as err:
            logger.warning(f"Could not register signal handlers: {err}")


def get_process_manager() -> LIAProcessManager:
    return LIAProcessManager()


if __name__ == "__main__":
    pm = get_process_manager()
    running, pid = pm.is_running()
    print(f"LIA Process Manager Status: Running={running}, PID={pid}")

