from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path

from PySide6.QtWidgets import QFileDialog


def _is_wsl() -> bool:
    return "microsoft" in platform.uname().release.lower()


def _extensions_from_filter(file_filter: str) -> list[str]:
    extensions: list[str] = []
    for part in file_filter.split(";;"):
        if "(" not in part or ")" not in part:
            continue
        patterns = part.split("(", 1)[1].split(")", 1)[0].split()
        extensions.extend(pattern[1:].lower() for pattern in patterns if pattern.startswith("*."))
    return extensions


def _windows_filter_from_qt_filter(file_filter: str) -> str:
    filters: list[str] = []
    for part in file_filter.split(";;"):
        part = part.strip()
        if not part:
            continue
        if "(" not in part or ")" not in part:
            filters.extend([part, "*.*"])
            continue
        label = part.split("(", 1)[0].strip()
        patterns = part.split("(", 1)[1].split(")", 1)[0].strip()
        filters.extend([f"{label} ({patterns})", patterns])
    return "|".join(filters or ["Todos os arquivos (*.*)", "*.*"])


def _initial_paths(directory: str) -> tuple[Path, str]:
    if not directory:
        return Path.cwd(), ""

    path = Path(directory).expanduser()
    if path.is_dir():
        return path, ""
    return path.parent if path.parent != Path("") else Path.cwd(), path.name


def _convert_path(command: str, path: str) -> str:
    if not path or shutil.which("wslpath") is None:
        return path

    try:
        result = subprocess.run(["wslpath", command, path], check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError):
        return path
    return result.stdout.strip() or path


def _to_windows_path(path: str) -> str:
    return _convert_path("-w", path)


def _to_wsl_path(path: str) -> str:
    return _convert_path("-u", path)


def _windows_native_file_name(caption: str, file_filter: str, directory: str, *, save_mode: bool) -> str:
    initial_dir, initial_name = _initial_paths(directory)
    extensions = _extensions_from_filter(file_filter)
    dialog_type = "SaveFileDialog" if save_mode else "OpenFileDialog"
    script = rf"""
Add-Type -AssemblyName System.Windows.Forms
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$dialog = New-Object System.Windows.Forms.{dialog_type}
$dialog.Title = $env:PDF_MAPPER_DIALOG_TITLE
$dialog.Filter = $env:PDF_MAPPER_DIALOG_FILTER
$dialog.InitialDirectory = $env:PDF_MAPPER_DIALOG_INITIAL_DIR
$dialog.FileName = $env:PDF_MAPPER_DIALOG_FILE_NAME
if ($env:PDF_MAPPER_DIALOG_DEFAULT_EXT) {{
    $dialog.DefaultExt = $env:PDF_MAPPER_DIALOG_DEFAULT_EXT
    $dialog.AddExtension = $true
}}
if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {{
    Write-Output $dialog.FileName
}}
"""
    env = os.environ.copy()
    env.update(
        {
            "PDF_MAPPER_DIALOG_TITLE": caption,
            "PDF_MAPPER_DIALOG_FILTER": _windows_filter_from_qt_filter(file_filter),
            "PDF_MAPPER_DIALOG_INITIAL_DIR": _to_windows_path(str(initial_dir)),
            "PDF_MAPPER_DIALOG_FILE_NAME": initial_name,
            "PDF_MAPPER_DIALOG_DEFAULT_EXT": extensions[0].lstrip(".") if extensions else "",
        }
    )

    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-STA", "-ExecutionPolicy", "Bypass", "-Command", script],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
    except OSError:
        return ""

    if result.returncode != 0:
        return ""

    selected = result.stdout.strip()
    return _to_wsl_path(selected) if selected else ""


def get_open_file_name(parent, caption: str, file_filter: str, directory: str = "") -> tuple[str, str]:
    if _is_wsl() and shutil.which("powershell.exe") is not None:
        selected = _windows_native_file_name(caption, file_filter, directory, save_mode=False)
        return (selected, file_filter) if selected else ("", "")

    return QFileDialog.getOpenFileName(parent, caption, directory, file_filter)


def get_save_file_name(parent, caption: str, file_filter: str, directory: str = "") -> tuple[str, str]:
    if _is_wsl() and shutil.which("powershell.exe") is not None:
        selected = _windows_native_file_name(caption, file_filter, directory, save_mode=True)
        return (selected, file_filter) if selected else ("", "")

    return QFileDialog.getSaveFileName(parent, caption, directory, file_filter)
