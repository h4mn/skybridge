# -*- coding: utf-8 -*-
"""
Extrator de referencia para estruturas de arquivos.
"""
from __future__ import annotations

from datetime import datetime
import fnmatch
import hashlib
import os
from pathlib import Path
from typing import Any
import subprocess

from skybridge.platform.observability.snapshot.capture import generate_snapshot_id
from skybridge.platform.observability.snapshot.extractors.base import StateExtractor
from skybridge.platform.observability.snapshot.models import Snapshot, SnapshotMetadata, SnapshotStats, SnapshotSubject, Diff, DiffItem, DiffSummary, DiffChange

DEFAULT_IGNORE_DIRS = [
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
    ".idea",
]

DEFAULT_IGNORE_FILES = [".DS_Store", "Thumbs.db"]


class FileOpsExtractor(StateExtractor):
    """Extrator para observacao de estruturas de arquivos."""

    @property
    def subject(self) -> SnapshotSubject:
        return SnapshotSubject.FILEOPS

    def capture(
        self,
        target: str,
        depth: int = 5,
        include_extensions: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        **options,
    ) -> Snapshot:
        root_path = Path(target).resolve()
        if not root_path.exists():
            raise ValueError(f"Caminho nao encontrado: {root_path}")
        if not root_path.is_dir():
            raise ValueError(f"Caminho nao e um diretorio: {root_path}")

        include_exts = self._normalize_extensions(include_extensions or [])
        exclude_patterns = exclude_patterns or []
        tags = options.get("tags", {})

        files: list[dict[str, Any]] = []
        dirs: set[str] = set()
        total_size = 0
        file_types: dict[str, int] = {}

        tree = {"name": ".", "type": "dir", "path": ".", "children": []}

        for current_root, dirnames, filenames in os.walk(root_path):
            rel_dir = Path(current_root).relative_to(root_path)
            depth_level = len(rel_dir.parts)

            if depth_level >= depth:
                dirnames[:] = []

            filtered_dirs = []
            for dirname in dirnames:
                rel_path = (rel_dir / dirname).as_posix()
                if self._should_ignore_dir(dirname, rel_path, exclude_patterns):
                    continue
                filtered_dirs.append(dirname)
                dirs.add(rel_path)
                self._ensure_dir_node(tree, rel_path)
            dirnames[:] = filtered_dirs

            for filename in filenames:
                rel_path = (rel_dir / filename).as_posix()
                if self._should_ignore_file(filename, rel_path, exclude_patterns, include_exts):
                    continue

                full_path = Path(current_root) / filename
                file_info = self._create_file_node(full_path, rel_path)
                files.append(file_info)
                total_size += file_info.get("size", 0)

                ext = Path(filename).suffix.lower() or "(none)"
                file_types[ext] = file_types.get(ext, 0) + 1

                self._add_file_node(tree, rel_path, file_info)

        self._sort_tree(tree)

        git_hash, git_branch = self._get_git_info(root_path)
        snapshot_id = generate_snapshot_id(self.subject, str(root_path))
        timestamp = datetime.utcnow()

        metadata = SnapshotMetadata(
            snapshot_id=snapshot_id,
            timestamp=timestamp,
            subject=self.subject,
            target=str(root_path),
            depth=depth,
            git_hash=git_hash,
            git_branch=git_branch,
            tags=tags,
        )
        stats = SnapshotStats(
            total_files=len(files),
            total_dirs=len(dirs),
            total_size=total_size,
            file_types=file_types,
        )
        return Snapshot(metadata=metadata, stats=stats, structure=tree, files=files)

    def compare(self, old: Snapshot, new: Snapshot) -> Diff:
        old_files = {item["path"]: item for item in old.files}
        new_files = {item["path"]: item for item in new.files}
        old_dirs = self._extract_dirs(old)
        new_dirs = self._extract_dirs(new)

        added_files = set(new_files) - set(old_files)
        removed_files = set(old_files) - set(new_files)
        added_dirs = set(new_dirs) - set(old_dirs)
        removed_dirs = set(old_dirs) - set(new_dirs)

        modified_files: list[str] = []
        size_delta = 0
        for path in set(old_files) & set(new_files):
            old_item = old_files[path]
            new_item = new_files[path]
            if old_item.get("size") != new_item.get("size") or old_item.get("modified") != new_item.get("modified"):
                modified_files.append(path)
                size_delta += (new_item.get("size", 0) - old_item.get("size", 0))

        size_delta += sum(new_files[path].get("size", 0) for path in added_files)
        size_delta -= sum(old_files[path].get("size", 0) for path in removed_files)

        moved_pairs: list[tuple[str, str]] = []
        moved_candidates = self._find_moved_files(removed_files, added_files, old_files, new_files)
        for old_path, new_path in moved_candidates:
            moved_pairs.append((old_path, new_path))
            removed_files.discard(old_path)
            added_files.discard(new_path)

        changes: list[DiffItem] = []
        for path in sorted(added_files):
            changes.append(DiffItem(type=DiffChange.ADDED, path=path, size_delta=new_files[path].get("size")))
        for path in sorted(removed_files):
            changes.append(DiffItem(type=DiffChange.REMOVED, path=path, size_delta=-old_files[path].get("size", 0)))
        for path in sorted(modified_files):
            changes.append(DiffItem(type=DiffChange.MODIFIED, path=path, size_delta=new_files[path].get("size", 0) - old_files[path].get("size", 0)))
        for old_path, new_path in moved_pairs:
            changes.append(DiffItem(type=DiffChange.MOVED, path=new_path, old_path=old_path))

        summary = DiffSummary(
            added_files=len(added_files),
            removed_files=len(removed_files),
            modified_files=len(modified_files),
            moved_files=len(moved_pairs),
            added_dirs=len(added_dirs),
            removed_dirs=len(removed_dirs),
            size_delta=size_delta,
        )

        diff_id = self._generate_diff_id(old.metadata.snapshot_id, new.metadata.snapshot_id)
        return Diff(
            diff_id=diff_id,
            timestamp=datetime.utcnow(),
            old_snapshot_id=old.metadata.snapshot_id,
            new_snapshot_id=new.metadata.snapshot_id,
            subject=self.subject,
            summary=summary,
            changes=changes,
        )

    def _normalize_extensions(self, extensions: list[str]) -> set[str]:
        result = set()
        for ext in extensions:
            if not ext:
                continue
            normalized = ext.lower()
            if not normalized.startswith("."):
                normalized = f".{normalized}"
            result.add(normalized)
        return result

    def _should_ignore_dir(self, name: str, rel_path: str, patterns: list[str]) -> bool:
        if name.lower() in {d.lower() for d in DEFAULT_IGNORE_DIRS}:
            return True
        return self._matches_patterns(rel_path + "/", patterns)

    def _should_ignore_file(self, name: str, rel_path: str, patterns: list[str], include_exts: set[str]) -> bool:
        if name in DEFAULT_IGNORE_FILES:
            return True
        if include_exts:
            ext = Path(name).suffix.lower()
            if ext not in include_exts:
                return True
        if self._matches_patterns(rel_path, patterns):
            return True
        return False

    def _matches_patterns(self, rel_path: str, patterns: list[str]) -> bool:
        return any(fnmatch.fnmatch(rel_path, pattern) for pattern in patterns)

    def _create_file_node(self, full_path: Path, rel_path: str) -> dict[str, Any]:
        try:
            stat = full_path.stat()
            size = stat.st_size
            modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
        except (OSError, PermissionError):
            size = 0
            modified = datetime.utcnow().isoformat()

        ext = full_path.suffix.lower()
        file_type = "file"
        if ext in [".py", ".js", ".ts", ".java", ".cpp", ".c"]:
            file_type = "code"
        elif ext in [".md", ".txt", ".rst"]:
            file_type = "text"
        elif ext in [".json", ".yaml", ".yml", ".xml"]:
            file_type = "config"
        elif ext in [".png", ".jpg", ".jpeg", ".gif", ".svg"]:
            file_type = "image"

        return {
            "name": full_path.name,
            "path": rel_path,
            "size": size,
            "modified": modified,
            "file_type": file_type,
        }

    def _ensure_dir_node(self, tree: dict[str, Any], rel_path: str) -> None:
        if rel_path in (".", ""):
            return
        parts = [part for part in rel_path.split("/") if part]
        current = tree
        current_path = []
        for part in parts:
            current_path.append(part)
            child = next((c for c in current["children"] if c.get("type") == "dir" and c.get("name") == part), None)
            if child is None:
                child = {
                    "name": part,
                    "type": "dir",
                    "path": "/".join(current_path),
                    "children": [],
                }
                current["children"].append(child)
            current = child

    def _add_file_node(self, tree: dict[str, Any], rel_path: str, file_info: dict[str, Any]) -> None:
        parts = rel_path.split("/")
        if len(parts) == 1:
            tree["children"].append({
                "name": file_info["name"],
                "type": "file",
                "path": file_info["path"],
                "size": file_info["size"],
                "modified": file_info["modified"],
                "file_type": file_info["file_type"],
            })
            return
        dir_path = "/".join(parts[:-1])
        self._ensure_dir_node(tree, dir_path)
        current = tree
        for part in parts[:-1]:
            current = next(c for c in current["children"] if c.get("type") == "dir" and c.get("name") == part)
        current["children"].append({
            "name": file_info["name"],
            "type": "file",
            "path": file_info["path"],
            "size": file_info["size"],
            "modified": file_info["modified"],
            "file_type": file_info["file_type"],
        })

    def _sort_tree(self, node: dict[str, Any]) -> None:
        children = node.get("children", [])
        children.sort(key=lambda item: (item.get("type") != "dir", item.get("name", "").lower()))
        for child in children:
            if child.get("type") == "dir":
                self._sort_tree(child)

    def _extract_dirs(self, snapshot: Snapshot) -> set[str]:
        dirs: set[str] = set()

        def walk(node: dict[str, Any]) -> None:
            if node.get("type") == "dir" and node.get("path") not in (".", None):
                dirs.add(node["path"])
            for child in node.get("children", []):
                walk(child)

        walk(snapshot.structure)
        return dirs

    def _find_moved_files(
        self,
        removed: set[str],
        added: set[str],
        old_files: dict[str, dict[str, Any]],
        new_files: dict[str, dict[str, Any]],
    ) -> list[tuple[str, str]]:
        matches: list[tuple[str, str]] = []
        added_by_signature: dict[tuple[str, int], list[str]] = {}
        for path in added:
            info = new_files[path]
            signature = (Path(path).name, int(info.get("size", 0)))
            added_by_signature.setdefault(signature, []).append(path)

        for old_path in list(removed):
            info = old_files[old_path]
            signature = (Path(old_path).name, int(info.get("size", 0)))
            candidates = added_by_signature.get(signature, [])
            if candidates:
                new_path = candidates.pop(0)
                matches.append((old_path, new_path))
        return matches

    def _get_git_info(self, path: Path) -> tuple[str | None, str | None]:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            git_hash = result.stdout.strip() if result.returncode == 0 else None

            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            git_branch = result.stdout.strip() if result.returncode == 0 else None

            return git_hash, git_branch
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return None, None

    def _generate_diff_id(self, old_id: str, new_id: str) -> str:
        digest = f"{old_id}:{new_id}".encode("utf-8")
        suffix = hashlib.md5(digest).hexdigest()[:8]
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"diff_{timestamp}_{suffix}"
