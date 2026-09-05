"""Helpers for leftover child processes (e.g. Chromium after Selenium quit)."""

import logging
import os

logger = logging.getLogger(__name__)


def reap_zombie_children() -> int:
    """Collect exited children so they do not stay as zombies.

    Selenium's driver.quit() stops Chrome but often leaves helper processes
    (crashpad, zygote) as zombies when this app is PID 1 in a container.
    """
    reaped = 0
    while True:
        try:
            pid, _status = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            break
        except InterruptedError:
            continue
        if pid == 0:
            break
        reaped += 1
    if reaped:
        logger.info("Reaped %s leftover child process(es)", reaped)
    return reaped
