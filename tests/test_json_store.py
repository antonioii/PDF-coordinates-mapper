import json
from pathlib import Path

import pytest

from app.models.project import COORDINATE_SYSTEM, PAGE_INDEX_BASE, PdfPageSize, Point, Project
from app.services.json_store import JsonStore


def make_project(tmp_path: Path) -> Project:
    return Project.new(
        "ficha_violencia_sinan",
        tmp_path / "violencia.pdf",
        tmp_path / "ficha_violencia_sinan.json",
        page_count=1,
        page_sizes=[PdfPageSize(page=0, width=595, height=842)],
    )


def test_create_new_empty_project_json(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    store = JsonStore()

    store.create_empty(project)

    data = json.loads(Path(project.json_path).read_text(encoding="utf-8"))
    assert data["project_name"] == "ficha_violencia_sinan"
    assert data["points"] == {}
    assert data["coordinate_system"] == COORDINATE_SYSTEM
    assert data["page_index_base"] == PAGE_INDEX_BASE


def test_add_point_preserves_existing_points(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    store = JsonStore()
    project.add_point("campo_1", Point(page=0, page_label=1, x=10, y=20))
    store.create_empty(project)

    loaded = store.load(project.json_path)
    loaded.add_point("campo_2", Point(page=0, page_label=1, x=30, y=40))
    store.save(loaded)

    reloaded = store.load(project.json_path)
    assert set(reloaded.points) == {"campo_1", "campo_2"}


def test_duplicate_name_is_rejected_without_confirmation(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    project.add_point("campo", Point(page=0, page_label=1, x=10, y=20))

    with pytest.raises(ValueError):
        project.add_point("campo", Point(page=0, page_label=1, x=30, y=40))


def test_overwrite_specific_point_when_allowed(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    project.add_point("campo", Point(page=0, page_label=1, x=10, y=20))
    project.add_point("campo", Point(page=0, page_label=1, x=30, y=40), overwrite=True)

    assert project.points["campo"].to_dict() == {"page": 0, "page_label": 1, "x": 30.0, "y": 40.0}


def test_remove_point_from_loaded_project(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    project.add_point("campo", Point(page=0, page_label=1, x=10, y=20))
    store = JsonStore()
    store.create_empty(project)

    loaded = store.load(project.json_path)
    loaded.remove_point("campo")
    store.save(loaded)

    assert store.load(project.json_path).points == {}


def test_rename_point_from_loaded_project(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    project.add_point("campo", Point(page=0, page_label=1, x=10, y=20))
    store = JsonStore()
    store.create_empty(project)

    loaded = store.load(project.json_path)
    loaded.rename_point("campo", "campo_renomeado")
    store.save(loaded)

    assert set(store.load(project.json_path).points) == {"campo_renomeado"}


def test_load_existing_json(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    project.add_point("mãe", Point(page=0, page_label=1, x=312.4, y=248.9))
    store = JsonStore()
    store.create_empty(project)

    loaded = store.load(project.json_path)

    assert loaded.project_name == project.project_name
    assert loaded.points["mãe"].x == 312.4


def test_json_has_expected_basic_structure(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    store = JsonStore()
    store.create_empty(project)

    data = json.loads(Path(project.json_path).read_text(encoding="utf-8"))

    assert set(data) == {
        "project_name",
        "pdf_path",
        "created_at",
        "updated_at",
        "coordinate_system",
        "page_index_base",
        "points",
        "pdf_metadata",
    }
    assert data["pdf_metadata"]["page_count"] == 1
    assert data["pdf_metadata"]["page_sizes"][0]["width"] == 595.0
