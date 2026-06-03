from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from app.models.project import Project
from app.utils.time_utils import timestamp_for_filename


class JsonStore:
    def create_empty(self, project: Project) -> None:
        self.save(project, create_backup=False)

    def load(self, json_path: str | Path) -> Project:
        path = Path(json_path)
        with path.open("r", encoding="utf-8") as file:
            data: dict[str, Any] = json.load(file)
        return Project.from_dict(data, path)

    def save(self, project: Project, create_backup: bool = True) -> None:
        path = Path(project.json_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if create_backup and path.exists():
            self.backup(path)
        project.touch()
        with path.open("w", encoding="utf-8") as file:
            json.dump(project.to_dict(), file, ensure_ascii=False, indent=2)
            file.write("\n")

    def backup(self, json_path: str | Path) -> Path:
        source = Path(json_path)
        backup_dir = source.parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"{source.stem}_{timestamp_for_filename()}.json"
        shutil.copy2(source, backup_path)
        return backup_path
