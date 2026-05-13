import subprocess
import time
import traceback
from dataclasses import replace
from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import QThread, pyqtSignal

from core.constants import (
    MIN_OUTPUT_FILE_SIZE, TERMINATE_WAIT_TIME, STOP_CHECK_INTERVAL
)
from core.job import Job
from core.ffmpeg.probe import probe_video_info, get_video_duration
from core.ffmpeg.builder import build_cmd
from core.ffmpeg.utils import get_subprocess_flags, parse_time_str

class FFmpegWorker(QThread):
    log_line = pyqtSignal(str)
    job_started = pyqtSignal(Path)
    job_finished = pyqtSignal(Path, bool)
    progress = pyqtSignal(int)
    gpu_fallback_activated = pyqtSignal(str)

    def __init__(self, jobs: List[Job], probe: bool = True):
        super().__init__()
        self.jobs = jobs
        self.proc: Optional[subprocess.Popen] = None
        self.probe = probe
        self._current_job: Optional[Job] = None
        self._current_job_pre_existing = False
        self._queue_cpu_fallback_active = False
        self._queue_cpu_fallback_reason: Optional[str] = None
        self._queue_cpu_notice_emitted = False

    def _enforce_queue_fallback_mode(self, job: Job) -> None:
        if not self._queue_cpu_fallback_active:
            return
        job.use_gpu = False
        job.gpu_encoder = None
        if not self._queue_cpu_notice_emitted:
            self.log_line.emit("[INFO] GPU fallback active. Processing remaining jobs with CPU.")
            self._queue_cpu_notice_emitted = True

    def _activate_queue_cpu_fallback(self, reason: str) -> None:
        if self._queue_cpu_fallback_active:
            return
        self._queue_cpu_fallback_active = True
        self._queue_cpu_fallback_reason = reason
        self.log_line.emit(f"[INFO] {reason}")
        self.gpu_fallback_activated.emit(reason)

    @staticmethod
    def _build_cpu_retry_job(job: Job) -> Job:
        return replace(job, use_gpu=False, gpu_encoder=None)

    def run(self):
        """
        Process all jobs in the queue with retry mechanism.
        
        Each job will be retried up to max_retries times if it fails.
        """
        for job in self.jobs:
            if self.isInterruptionRequested():
                if self._current_job and self._current_job.out.exists() and not self._current_job_pre_existing:
                    try:
                        self._current_job.out.unlink()
                        print(f"[CLEANUP] Deleted partial file: {self._current_job.out}")
                    except Exception as e:
                        print(f"[CLEANUP ERROR] Failed to delete {self._current_job.out}: {e}")
                self.job_finished.emit(self._current_job.out if self._current_job else job.out, False)
                break
            
            self._current_job = job
            self._enforce_queue_fallback_mode(job)
            self._current_job_pre_existing = job.out.exists()
            ok = False
            
            attempt = 0
            while attempt <= job.max_retries:
                if self.isInterruptionRequested():
                    break

                if attempt > 0:
                    print(f"[RETRY] Attempting retry {attempt}/{job.max_retries} for {job.src.name}")
                    if job.out.exists() and not self._current_job_pre_existing:
                        try:
                            job.out.unlink()
                        except Exception:
                            pass
                    wait_time = min(2 ** attempt, 10)
                    print(f"[RETRY] Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)

                ok = self._process_job(job)

                if ok or self.isInterruptionRequested():
                    break

                attempt += 1
                if attempt > job.max_retries:
                    print(f"[ERROR] Max retries ({job.max_retries}) reached for {job.src.name}")
                    break
            
            self.job_finished.emit(job.out, ok)
            self._current_job = None

    def stop(self):
        """Request stop of encoding process using Qt's thread-safe mechanism."""
        self.requestInterruption()
        if self.proc:
            try:
                self.proc.terminate()
                time.sleep(TERMINATE_WAIT_TIME)
                if self.proc.poll() is None:
                    self.proc.kill()
            except Exception:
                pass

    def _process_job(self, job: Job) -> bool:
        """
        Process a single encoding job.
        
        This method:
        1. Builds the FFmpeg command
        2. Starts the FFmpeg process
        3. Monitors progress and parses output
        4. Handles errors and cleanup
        5. Emits progress signals for UI updates
        
        Args:
            job: Job to process
        
        Returns:
            True if encoding succeeded, False otherwise
        """
        self.job_started.emit(job.src)
        
        print(f"\n[FFMPEG] Starting encoding: {job.src.name}")
        print(f"[FFMPEG] Output: {job.out}")
        
        w: Optional[int] = None
        h: Optional[int] = None
        fps = 30.0
        rotation = 0
        is_file = job.src.exists()
        if is_file and self.probe:
            fps, resolution, _, _, rotation = probe_video_info(job.src)
            if resolution:
                w, h = resolution
                print(f"[FFMPEG] Source probe: {w}x{h} @ {fps:.2f} fps (rotation={rotation}°)")
            else:
                print(f"[FFMPEG] Source probe: unknown size @ {fps:.2f} fps")

        was_gpu_job = bool(job.use_gpu and job.gpu_encoder)

        cmd, used_cuda = build_cmd(job, w, h, fps, rotation=rotation, prefer_cuda_hwaccel=True)
        print(f"[FFMPEG] Command: {' '.join(cmd)}")
        print(f"[FFMPEG] {'='*60}\n")

        ok = self._run_ffmpeg_encode(job, cmd)
        if not ok and used_cuda:
            print(
                "[FFMPEG] CUDA hwaccel path failed; retrying with CPU decode/filters"
            )
            if job.out.exists() and not self._current_job_pre_existing:
                try:
                    job.out.unlink()
                except OSError:
                    pass
            cmd_cpu, _ = build_cmd(
                job, w, h, fps, prefer_cuda_hwaccel=False
            )
            print(f"[FFMPEG] Command: {' '.join(cmd_cpu)}")
            print(f"[FFMPEG] {'='*60}\n")
            ok = self._run_ffmpeg_encode(job, cmd_cpu)

        if not ok and was_gpu_job:
            reason = "GPU encode failed at runtime. Switched to CPU for this and remaining jobs."
            self._activate_queue_cpu_fallback(reason)
            if job.out.exists() and not self._current_job_pre_existing:
                try:
                    job.out.unlink()
                except OSError:
                    pass
            cpu_job = self._build_cpu_retry_job(job)
            cmd_cpu_fallback, _ = build_cmd(
                cpu_job, w, h, fps, prefer_cuda_hwaccel=False
            )
            print(f"[FFMPEG] Command: {' '.join(cmd_cpu_fallback)}")
            print(f"[FFMPEG] {'='*60}\n")
            ok = self._run_ffmpeg_encode(cpu_job, cmd_cpu_fallback)
        return ok

    def _run_ffmpeg_encode(self, job: Job, cmd: List[str]) -> bool:
        """Run one FFmpeg encode; returns True on exit code 0."""
        try:
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=get_subprocess_flags()
            )
        except Exception as e:
            error_msg = f"[ERROR] FFmpeg start failed: {e}"
            print(error_msg)
            self.log_line.emit(error_msg)
            self.proc = None
            return False

        duration_sec = get_video_duration(job.src)

        all_output = []
        last_progress = 0
        last_elapsed = 0.0

        try:
            while True:
                if self.isInterruptionRequested():
                    print(f"\n[FFMPEG] Stopping encoding...")
                    if self.proc and self.proc.poll() is None:
                        try:
                            self.proc.terminate()
                            time.sleep(0.5)
                            if self.proc.poll() is None:
                                self.proc.kill()
                                print(f"[FFMPEG] Process killed")
                        except Exception as e:
                            print(f"[FFMPEG] Error stopping process: {e}")
                    if job.out.exists() and not self._current_job_pre_existing:
                        try:
                            job.out.unlink()
                            print(f"[CLEANUP] Deleted partial file: {job.out}")
                        except Exception as e:
                            print(f"[CLEANUP ERROR] Failed to delete {job.out}: {e}")
                    return False

                line = self.proc.stdout.readline()
                if line == "" and self.proc.poll() is not None:
                    break
                if not line:
                    time.sleep(STOP_CHECK_INTERVAL)
                    continue

                line = line.rstrip()
                all_output.append(line)

                print(line)

                line_lower = line.lower()
                is_error = (
                    "error" in line_lower or
                    "failed" in line_lower or
                    "cannot" in line_lower or
                    "invalid" in line_lower or
                    "not found" in line_lower or
                    "unable" in line_lower or
                    "failed to" in line_lower
                )

                if is_error:
                    error_msg = f"[ERROR] {line}"
                    print(f"\n{error_msg}")
                    self.log_line.emit(error_msg)

                if "time=" in line:
                    try:
                        parts = [p for p in line.split() if p.startswith("time=")]
                        if parts:
                            elapsed = parse_time_str(parts[0])
                            if duration_sec and duration_sec > 0:
                                pct = int(min(100, (elapsed / duration_sec) * 100))
                                if pct != last_progress or abs(elapsed - last_elapsed) > 0.5:
                                    self.progress.emit(pct)
                                    last_progress = pct
                                    last_elapsed = elapsed
                    except Exception:
                        pass

            rc = self.proc.wait()
            self.proc = None

            print(f"\n[FFMPEG] Process exited with code: {rc}")
            print(f"[FFMPEG] {'='*60}\n")

            success = (rc == 0)

            if not success:
                error_summary = f"[ERROR] FFmpeg process failed with exit code {rc}"
                print(error_summary)

                error_lines = [l for l in all_output[-20:] if any(
                    word in l.lower() for word in ["error", "failed", "cannot", "invalid"]
                )]
                if error_lines:
                    print(f"[ERROR] Last error lines:")
                    for err_line in error_lines[-5:]:
                        print(f"  {err_line}")
                        error_summary += f"\n{err_line}"

                self.log_line.emit(error_summary)

                if job.out.exists() and not self._current_job_pre_existing:
                    try:
                        file_size = job.out.stat().st_size
                        if file_size < MIN_OUTPUT_FILE_SIZE:
                            job.out.unlink()
                            print(f"[CLEANUP] Deleted corrupt file (too small: {file_size} bytes): {job.out}")
                    except Exception as e:
                        print(f"[CLEANUP ERROR] Failed to delete {job.out}: {e}")
            else:
                print(f"[FFMPEG] ✓ Encoding completed successfully!")
                if job.out.exists():
                    file_size = job.out.stat().st_size / (1024 * 1024)
                    print(f"[FFMPEG] Output file size: {file_size:.2f} MB")

            self.progress.emit(100 if success else 0)
            return success
        except Exception as e:
            error_msg = f"[ERROR] Worker error: {e}"
            print(f"\n{error_msg}")
            traceback.print_exc()
            self.log_line.emit(error_msg)
            try:
                if self.proc:
                    self.proc.kill()
            except Exception:
                pass
            self.proc = None
            if job.out.exists() and not self._current_job_pre_existing:
                try:
                    job.out.unlink()
                    print(f"[CLEANUP] Deleted partial file after exception: {job.out}")
                except Exception:
                    pass
            return False
