from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.utils.time_utils import now_iso


COORDINATE_SYSTEM = "PyMuPDF PDF points"
PAGE_INDEX_BASE = 0


@dataclass(slots=True)
class Point:
    page: int
    page_label: int
    x: float
    y: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "page": self.page,
            "page_label": self.page_label,
            "x": round(float(self.x), 2),
            "y": round(float(self.y), 2),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Point":
        return cls(
            page=int(data["page"]),
            page_label=int(data.get("page_label", int(data["page"]) + 1)),
            x=float(data["x"]),
            y=float(data["y"]),
        )


@dataclass(slots=True)
class PdfPageSize:
    page: int
    width: float
    height: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "page": self.page,
            "width": round(float(self.width), 2),
            "height": round(float(self.height), 2),
        }


@dataclass(slots=True)
class Project:
    project_name: str
    pdf_path: str
    json_path: str
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)
    points: dict[str, Point] = field(default_factory=dict)
    page_count: int = 0
    page_sizes: list[PdfPageSize] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "pdf_path": self.pdf_path,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "coordinate_system": COORDINATE_SYSTEM,
            "page_index_base": PAGE_INDEX_BASE,
            "points": {name: point.to_dict() for name, point in self.points.items()},
            "pdf_metadata": {
                "page_count": self.page_count,
                "page_sizes": [page_size.to_dict() for page_size in self.page_sizes],
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], json_path: str | Path) -> "Project":
        metadata = data.get("pdf_metadata", {})
        page_sizes = [
            PdfPageSize(
                page=int(item["page"]),
                width=float(item["width"]),
                height=float(item["height"]),
            )
            for item in metadata.get("page_sizes", [])
        ]
        return cls(
            project_name=str(data["project_name"]),
            pdf_path=str(data["pdf_path"]),
            json_path=str(json_path),
            created_at=str(data.get("created_at") or now_iso()),
            updated_at=str(data.get("updated_at") or now_iso()),
            points={
                str(name): Point.from_dict(point)
                for name, point in data.get("points", {}).items()
            },
            page_count=int(metadata.get("page_count", 0)),
            page_sizes=page_sizes,
        )

    @classmethod
    def new(
        cls,
        project_name: str,
        pdf_path: str | Path,
        json_path: str | Path,
        page_count: int = 0,
        page_sizes: list[PdfPageSize] | None = None,
    ) -> "Project":
        return cls(
            project_name=project_name.strip(),
            pdf_path=str(Path(pdf_path)),
            json_path=str(Path(json_path)),
            page_count=page_count,
            page_sizes=page_sizes or [],
        )

    def add_point(self, name: str, point: Point, overwrite: bool = False) -> None:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("O nome do ponto não pode ficar vazio.")
        if clean_name in self.points and not overwrite:
            raise ValueError("Já existe um ponto com esse nome.")
        self.points[clean_name] = point
        self.touch()

    def remove_point(self, name: str) -> None:
        if name not in self.points:
            raise KeyError(name)
        del self.points[name]
        self.touch()

    def update_point(self, name: str, point: Point) -> None:
        if name not in self.points:
            raise KeyError(name)
        self.points[name] = point
        self.touch()

    def rename_point(self, old_name: str, new_name: str, overwrite: bool = False) -> None:
        clean_name = new_name.strip()
        if old_name not in self.points:
            raise KeyError(old_name)
        if not clean_name:
            raise ValueError("O nome do ponto não pode ficar vazio.")
        if clean_name != old_name and clean_name in self.points and not overwrite:
            raise ValueError("Já existe um ponto com esse nome.")
        point = self.points.pop(old_name)
        self.points[clean_name] = point
        self.touch()

    def touch(self) -> None:
        self.updated_at = now_iso()
