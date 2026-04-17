import gc
import os
import re
import time
import sys
from typing import Optional, Dict, List

import psutil
import threading
import subprocess
from fixlib.logger import log
from fixlib.event import dispatch_event, Event, EventType
from signal import signal, Signals, SIGTERM, SIGINT

from fixlib.utils import iec_size_format

try:
    import resource
    import fcntl
except ImportError:
    pass

try:
    from psutil import cpu_count
except ImportError:
    from os import cpu_count


parent_pid: Optional[int] = None
initial_dir: str = os.getcwd()


def restart() -> None:
    python_args = []
    if not getattr(sys, "frozen", False):
        python_args = subprocess._args_from_interpreter_flags()
    args = python_args + sys.argv

    path_prefix = "." + os.pathsep
    python_path = os.environ.get("PYTHONPATH", "")
    if sys.path[0] == "" and not python_path.startswith(path_prefix):
        os.environ["PYTHONPATH"] = path_prefix + python_path

    try:
        close_fds()
    except Exception:
        log.exception("Failed to FD_CLOEXEC all file descriptors")

    kill_children(SIGTERM, ensure_death=True)

    os.chdir(initial_dir)
    os.execv(sys.executable, [sys.executable] + args)
    log.fatal("Failed to restart - exiting")
    os._exit(1)


def delayed_exit(delay: int = 3) -> None:
    pass


def close_fds(safety_margin: int = 1024) -> None:
    """Set FD_CLOEXEC on all file descriptors except stdin, stdout, stderr

    Since there is a race between determining the max number of fds to close
    and actually closing them we are adding a safety margin.
    """
    if sys.platform == "win32":
        return

    open_fds = [f.fd for f in psutil.Process().open_files()]
    if len(open_fds) == 0:
        return

    num_open = max(open_fds)

    try:
        sc_open_max = os.sysconf("SC_OPEN_MAX")
    except AttributeError:
        sc_open_max = 1024

    num_close = min(num_open + safety_margin, sc_open_max)

    for fd in range(3, num_close):
        fd_cloexec(fd)


def fd_cloexec(fd: int) -> None:
    try:
        flags = fcntl.fcntl(fd, fcntl.F_GETFD)
    except IOError:
        return
    fcntl.fcntl(fd, fcntl.F_SETFD, flags | fcntl.FD_CLOEXEC)


def handler(sig, frame) -> None:
    """Handles Ctrl+c by letting the Collector() know to shut down"""
    current_pid = os.getpid()
    if current_pid == parent_pid:
        reason = f"Received shutdown signal {sig}"
        log.debug(f"Parent caught signal {sig} - dispatching shutdown event")
        # Dispatch shutdown event in parent process which also causes SIGTERM to be sent
        # to the process group and in turn causes the shutdown event in all child
        # processes.
        dispatch_event(Event(EventType.SHUTDOWN, {"reason": reason, "emergency": False}))
    else:
        reason = f"Received shutdown signal {sig} from parent process"
        log.debug(
            f"Child with PID {current_pid} shutting down" " - you might see exceptions from interrupted worker threads"
        )
        # Child's threads have 3s to shut down before the following thread will
        # shut them down hard.
        kt = threading.Thread(target=delayed_exit, name="shutdown")
        kt.start()
        # Dispatch shutdown event in child process
        dispatch_event(
            Event(EventType.SHUTDOWN, {"reason": reason, "emergency": False}),
            blocking=False,
        )
        sys.exit(0)


def initializer() -> None:
    pass


def collector_initializer(nice_level: int = 5) -> None:
    pass


def set_thread_name(thread_name: str = "fix") -> None:
    pass


def emergency_shutdown(reason: str = "") -> None:
    pass


def kill_children(
    signal: Signals = SIGTERM, ensure_death: bool = False, timeout: int = 3, process_pid: Optional[int] = None
) -> None:
    procs = psutil.Process(process_pid).children(recursive=True)
    num_children = len(procs)
    if num_children == 0:
        return
    elif num_children == 1:
        log_suffix = ""
    else:
        log_suffix = "ren"

    log.debug(f"Sending {signal.name} to {num_children} child{log_suffix}.")
    for p in procs:
        try:
            if signal == SIGTERM:
                p.terminate()
            else:
                p.send_signal(signal)
        except psutil.NoSuchProcess:
            pass

    if ensure_death:
        _, alive = psutil.wait_procs(procs, timeout=timeout)
        for p in alive:
            log.debug(f"Child with PID {p.pid} is still alive, sending SIGKILL")
            try:
                p.kill()
            except psutil.NoSuchProcess:
                pass


def increase_limits() -> None:
    pass


def num_default_threads(num_min_threads: int = 2) -> int:
    pass


def get_process_info(pid: int = None, proc: str = "/proc") -> Dict:
    pass


def get_file_descriptor_info(pid: int = None, proc: str = "/proc") -> Dict:
    pass


def get_pid_list(proc: str = "/proc") -> List:
    pass


def get_all_process_info(pid: int = None, proc: str = "/proc") -> Dict:
    pass


def get_child_process_info(pid: int = None, proc: str = "/proc") -> Dict:
    pass


def get_stats() -> Dict:
    pass


def log_stats(graph=None, garbage_collector_stats: bool = False) -> None:
    pass
