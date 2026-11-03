"""La bóveda de memoria local-first: esqueleto canónico y espejo del workspace."""

from __future__ import annotations

from pathlib import Path

from arkhiva.memory_vault import (
    CANONICAL_FILES,
    VAULT_DIRNAME,
    initialize_vault,
    initialize_vault_structure,
    mirror_workspace_memory,
    resolve_vault_dir,
)


class _FakeContext:
    def __init__(self, base: Path | None) -> None:
        self._base = base
        self.calls: list[object] = []

    def getExternalFilesDir(self, kind: object) -> Path | None:  # noqa: N802 - API Android
        self.calls.append(kind)
        return self._base


def test_without_android_context_the_vault_is_not_invented(tmp_path: Path) -> None:
    """En escritorio no hay almacenamiento externo que ofrecer: ``None``."""
    assert resolve_vault_dir(None) is None
    assert initialize_vault(None) is None
    assert not (tmp_path / VAULT_DIRNAME).exists()


def test_context_without_external_storage_disables_the_vault() -> None:
    """Un volumen no montado devuelve ``None`` y no debe levantar."""
    assert resolve_vault_dir(_FakeContext(None)) is None


def test_structure_creates_the_four_canonical_documents(tmp_path: Path) -> None:
    created = initialize_vault_structure(tmp_path)
    assert {p.name for p in created} == set(CANONICAL_FILES)
    for name in CANONICAL_FILES:
        text = (tmp_path / name).read_text(encoding="utf-8")
        assert text.startswith(f"# ARKHIVA Ω · {name}")
        assert "Inicializado:" in text


def test_structure_never_overwrites_existing_content(tmp_path: Path) -> None:
    """Un documento con contenido del usuario es intocable."""
    target = tmp_path / CANONICAL_FILES[0]
    target.write_text("contenido propio\n", encoding="utf-8")
    created = initialize_vault_structure(tmp_path)
    assert target not in created
    assert target.read_text(encoding="utf-8") == "contenido propio\n"


def test_initialize_vault_uses_the_external_files_dir(tmp_path: Path) -> None:
    context = _FakeContext(tmp_path)
    vault = initialize_vault(context)
    assert vault == tmp_path / VAULT_DIRNAME
    assert context.calls == [None]
    assert all((vault / name).is_file() for name in CANONICAL_FILES)


def test_mirror_copies_memory_profile_and_soul_into_the_vault(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "memory").mkdir(parents=True)
    (workspace / "memory" / "MEMORY.md").write_text("# Hechos\n\n- uno\n", encoding="utf-8")
    (workspace / "USER.md").write_text("---\nnombre: x\n---\n# Perfil\n", encoding="utf-8")
    (workspace / "SOUL.md").write_text("# Alma\n", encoding="utf-8")
    vault = tmp_path / "vault"

    written = mirror_workspace_memory(workspace, vault)

    assert {p.name for p in written} == {
        "bitacora_cognitiva.md",
        "perfil_usuario.md",
        "caracter_soberano.md",
    }
    bitacora = (vault / "bitacora_cognitiva.md").read_text(encoding="utf-8")
    assert "## Hechos" in bitacora
    assert "Consolidado desde `memory/MEMORY.md`" in bitacora
    # El frontmatter YAML del perfil no debe acabar dentro del Markdown.
    perfil = (vault / "perfil_usuario.md").read_text(encoding="utf-8")
    assert "nombre: x" not in perfil
    assert "# Perfil" in perfil


def test_mirror_skips_missing_sources_without_failing(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    assert mirror_workspace_memory(tmp_path / "nada", vault) == []
    assert all((vault / name).is_file() for name in CANONICAL_FILES)
