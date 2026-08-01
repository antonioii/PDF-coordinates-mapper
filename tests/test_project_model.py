import pytest

from app.models.project import Point, Project


def make_project() -> Project:
    return Project.new("teste", "form.pdf", "form.json")


def test_add_point_does_not_overwrite_duplicate_by_default() -> None:
    project = make_project()
    project.add_point("nome", Point(page=0, page_label=1, x=10, y=20))

    with pytest.raises(ValueError):
        project.add_point("nome", Point(page=0, page_label=1, x=30, y=40))

    assert project.points["nome"].x == 10


def test_add_point_overwrites_when_explicitly_allowed() -> None:
    project = make_project()
    project.add_point("nome", Point(page=0, page_label=1, x=10, y=20))
    project.add_point("nome", Point(page=0, page_label=1, x=30, y=40), overwrite=True)

    assert project.points["nome"].x == 30
    assert project.points["nome"].y == 40


def test_remove_point() -> None:
    project = make_project()
    project.add_point("nome", Point(page=0, page_label=1, x=10, y=20))

    project.remove_point("nome")

    assert project.points == {}


def test_update_point_replaces_coordinates_without_changing_its_name() -> None:
    project = make_project()
    project.add_point("nome", Point(page=0, page_label=1, x=10, y=20))

    project.update_point("nome", Point(page=0, page_label=1, x=30, y=40))

    assert project.points["nome"].to_dict() == {"page": 0, "page_label": 1, "x": 30.0, "y": 40.0}


def test_rename_point() -> None:
    project = make_project()
    project.add_point("nome", Point(page=0, page_label=1, x=10, y=20))

    project.rename_point("nome", "nome_completo")

    assert "nome" not in project.points
    assert "nome_completo" in project.points
