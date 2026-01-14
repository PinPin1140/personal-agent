"""Process sandboxing for isolation and resource limits."""
import os
import signal
import resource
import time
from typing import Optional, Dict, Any
from contextlib import contextmanager


class SandboxError(Exception):
    """Sandbox-related errors."""
    pass


class ProcessSandbox:
    """Userland process sandboxing without kernel modules."""

    def __init__(
        self,
        max_cpu_time: float = 30.0,
        max_memory_mb: int = 1024,
        max_processes: int = 100
    ):
        self.max_cpu_time = max_cpu_time
        self.max_memory_mb = max_memory_mb
        self.max_processes = max_processes
        self._child_processes: dict = {}

    def _limit_child_resources(self):
        """Limit child process resources (runs in child after fork)."""
        # Set nice level to lower priority
        os.nice(5)

        # Limit file descriptors
        try:
            soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
            new_hard = min(hard, 1024)
            resource.setrlimit(
                resource.RLIMIT_NOFILE,
                (soft, new_hard)
            )
        except (ValueError, OSError):
            pass

    @contextmanager
    def run(self, cmd: list, timeout: Optional[float] = None):
        """Run command in sandbox with resource limits."""

        def timeout_handler(signum, frame):
            raise SandboxError(f"Process timed out after {timeout}s")

        try:
            # Set resource limits before spawning
            soft, hard = resource.getrlimit(resource.RLIMIT_CPU)
            new_hard = min(int(hard), int(self.max_cpu_time))

            # Set CPU time limit
            resource.setrlimit(
                resource.RLIMIT_CPU,
                (self.max_cpu_time, new_hard)
            )

            # Set address space limit (best-effort, works on Linux)
            try:
                soft, hard = resource.getrlimit(resource.RLIMIT_AS)
                new_soft = min(int(soft), int(self.max_memory_mb * 1024 * 1024))  # MB to bytes
                resource.setrlimit(
                    resource.RLIMIT_AS,
                    (new_soft, int(hard))
                )
            except (ValueError, OSError):
                # AS limit may not be available on all systems
                pass

            # Set max number of processes
            try:
                soft, hard = resource.getrlimit(resource.RLIMIT_NPROC)
                new_soft = min(int(soft), int(self.max_processes))
                resource.setrlimit(
                    resource.RLIMIT_NPROC,
                    (new_soft, int(hard))
                )
            except (ValueError, OSError):
                pass

            # Spawn process with limits
            import subprocess
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=self._limit_child_resources
            )

            timeout = timeout or self.max_cpu_time
            start_time = time.time()

            try:
                returncode, stdout, stderr = proc.communicate(timeout=timeout)
                elapsed = time.time() - start_time

                return {
                    "returncode": returncode,
                    "stdout": stdout.decode('utf-8', errors='replace') if stdout else "",
                    "stderr": stderr.decode('utf-8', errors='replace') if stderr else "",
                    "elapsed": elapsed
                }

            except subprocess.TimeoutExpired:
                proc.kill()
                raise SandboxError(f"Process timed out after {timeout}s")

            except Exception as e:
                proc.kill()
                raise SandboxError(f"Process failed: {str(e)}")

        finally:
            signal.signal(signal.SIGALRM, signal.SIG_DFL)

    def _limit_child_resources(self):
        """Limit child process resources (runs in child after fork)."""
        # This runs in the child process after fork
        # Set nice level to lower priority
        os.nice(5)

        # Limit file descriptors
        try:
                soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
                new_hard = min(hard, 1024)
                resource.setrlimit(
                        resource.RLIMIT_NOFILE,
                        (soft, new_hard)
                )
        except (ValueError, OSError):
                pass

    def get_usage(self) -> dict:
        """Get current resource usage."""
        usage = resource.getrusage(resource.RUSAGE_SELF)

        return {
                "user_time": usage.ru_utime,
                "system_time": usage.ru_stime,
                "max_rss_kb": usage.ru_maxrss,
                "max_rss_mb": usage.ru_maxrss / 1024,
                "major_page_faults": usage.ru_majflt,
                "minor_page_faults": usage.ru_minflt,
                "voluntary_context_switches": usage.ru_nvcsw,
                "involuntary_context_switches": usage.ru_nivcsw
        }
