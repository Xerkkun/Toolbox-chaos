from __future__ import annotations

import ctypes
import os
import subprocess
import sys
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class MemorySnapshot:
    rss_bytes: int | None
    peak_rss_bytes: int | None

    def as_dict(self) -> dict[str, int | None]:
        return asdict(self)


def total_physical_memory_bytes() -> int | None:
    if sys.platform.startswith("win"):
        from ctypes import wintypes

        class MemoryStatusEx(ctypes.Structure):
            _fields_ = [
                ("dwLength", wintypes.DWORD),
                ("dwMemoryLoad", wintypes.DWORD),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatusEx()
        status.dwLength = ctypes.sizeof(status)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        if kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return int(status.ullTotalPhys)
        return None

    try:
        page_size = int(os.sysconf("SC_PAGE_SIZE"))
        physical_pages = int(os.sysconf("SC_PHYS_PAGES"))
        return page_size * physical_pages
    except (AttributeError, OSError, ValueError):
        return None


def power_status() -> dict[str, object]:
    if sys.platform.startswith("win"):
        from ctypes import wintypes

        class SystemPowerStatus(ctypes.Structure):
            _fields_ = [
                ("ACLineStatus", ctypes.c_ubyte),
                ("BatteryFlag", ctypes.c_ubyte),
                ("BatteryLifePercent", ctypes.c_ubyte),
                ("SystemStatusFlag", ctypes.c_ubyte),
                ("BatteryLifeTime", wintypes.DWORD),
                ("BatteryFullLifeTime", wintypes.DWORD),
            ]

        status = SystemPowerStatus()
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        if kernel32.GetSystemPowerStatus(ctypes.byref(status)):
            ac_mapping = {0: "offline", 1: "online", 255: "unknown"}
            return {
                "ac_line": ac_mapping.get(int(status.ACLineStatus), "unknown"),
                "battery_percent": (
                    int(status.BatteryLifePercent)
                    if status.BatteryLifePercent != 255
                    else None
                ),
            }
    return {"ac_line": "not_detected", "battery_percent": None}


def _windows_memory_snapshot(pid: int) -> MemorySnapshot:
    from ctypes import wintypes

    class ProcessMemoryCounters(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(ProcessMemoryCounters),
        wintypes.DWORD,
    ]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    close_handle = False
    if pid == os.getpid():
        handle = kernel32.GetCurrentProcess()
    else:
        process_query_information = 0x0400
        process_vm_read = 0x0010
        handle = kernel32.OpenProcess(
            process_query_information | process_vm_read, False, int(pid)
        )
        close_handle = True
    if not handle:
        return MemorySnapshot(None, None)

    counters = ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    try:
        ok = psapi.GetProcessMemoryInfo(
            handle, ctypes.byref(counters), counters.cb
        )
        if not ok:
            return MemorySnapshot(None, None)
        return MemorySnapshot(
            int(counters.WorkingSetSize),
            int(counters.PeakWorkingSetSize),
        )
    finally:
        if close_handle:
            kernel32.CloseHandle(handle)


def _linux_memory_snapshot(pid: int) -> MemorySnapshot:
    status_path = f"/proc/{int(pid)}/status"
    try:
        with open(status_path, encoding="utf-8") as stream:
            lines = stream.read().splitlines()
    except OSError:
        return MemorySnapshot(None, None)

    values: dict[str, int] = {}
    for line in lines:
        if line.startswith(("VmRSS:", "VmHWM:")):
            key, raw = line.split(":", 1)
            parts = raw.strip().split()
            if parts:
                values[key] = int(parts[0]) * 1024
    return MemorySnapshot(values.get("VmRSS"), values.get("VmHWM"))


def _posix_memory_snapshot(pid: int) -> MemorySnapshot:
    try:
        output = subprocess.check_output(
            ["ps", "-o", "rss=", "-p", str(int(pid))],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        rss_bytes = int(output) * 1024 if output else None
    except (OSError, subprocess.SubprocessError, ValueError):
        rss_bytes = None

    peak_rss_bytes = None
    if pid == os.getpid():
        try:
            import resource

            raw_peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
            peak_rss_bytes = raw_peak if sys.platform == "darwin" else raw_peak * 1024
        except (ImportError, ValueError):
            pass
    return MemorySnapshot(rss_bytes, peak_rss_bytes)


def process_memory_snapshot(pid: int | None = None) -> MemorySnapshot:
    target_pid = int(pid or os.getpid())
    if sys.platform.startswith("win"):
        return _windows_memory_snapshot(target_pid)
    if sys.platform.startswith("linux"):
        return _linux_memory_snapshot(target_pid)
    return _posix_memory_snapshot(target_pid)
