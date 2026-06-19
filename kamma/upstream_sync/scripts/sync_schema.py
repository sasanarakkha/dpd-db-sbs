#!/usr/bin/env python3

"""Define typed schema objects for upstream sync metadata JSON files."""

import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath

BOOTSTRAP_SHA_SENTINEL = "BOOTSTRAP_REQUIRED"
FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def validate_repo_relative_paths(
    paths: list[str],
    label: str,
    allow_globs: bool = False,
) -> list[str]:
    """Validate path strings that must stay inside the repository."""
    validated: list[str] = []
    git_pathspec_chars = set("*?[]")
    for index, path in enumerate(paths):
        item_label = f"{label}[{index}]"
        if not path.strip():
            raise ValueError(f"{item_label} must be a non-empty path")
        if path != path.strip():
            raise ValueError(f"{item_label} must not contain surrounding whitespace")
        if "\\" in path:
            raise ValueError(f"{item_label} must use forward slashes")
        if path.startswith("-"):
            raise ValueError(f"{item_label} must not start with '-'")
        if path.startswith(":"):
            raise ValueError(f"{item_label} must not use git pathspec magic")
        if not allow_globs and any(char in path for char in git_pathspec_chars):
            raise ValueError(
                f"{item_label} must not contain git pathspec metacharacters"
            )
        posix_path = PurePosixPath(path)
        if posix_path.is_absolute() or path.startswith("~"):
            raise ValueError(f"{item_label} must be a repo-relative path")
        if ".." in posix_path.parts:
            raise ValueError(f"{item_label} must stay inside the repository")
        validated.append(path)
    return validated


def validate_repo_relative_path(path: str, label: str) -> str:
    """Validate one path string that must stay inside the repository."""
    try:
        return validate_repo_relative_paths([path], label)[0]
    except ValueError as exc:
        raise ValueError(str(exc).replace(f"{label}[0]", label, 1)) from exc


def _as_object(raw: object, label: str) -> dict[str, object]:
    if not isinstance(raw, dict):
        raise TypeError(f"{label} must be a JSON object")
    return raw


def _required_string(data: dict[str, object], field: str) -> str:
    if field not in data:
        raise ValueError(f"missing required field '{field}'")
    value = data[field]
    if not isinstance(value, str):
        raise TypeError(f"field '{field}' must be a string")
    if not value.strip():
        raise ValueError(f"field '{field}' must be a non-empty string")
    return value


def _required_full_sha(
    data: dict[str, object], field: str, allow_bootstrap: bool = False
) -> str:
    value = _required_string(data, field)
    if allow_bootstrap and value == BOOTSTRAP_SHA_SENTINEL:
        return value
    if not FULL_SHA_RE.fullmatch(value):
        raise ValueError(
            f"field '{field}' must be a full 40-character lowercase git SHA"
        )
    return value


def _optional_string(data: dict[str, object], field: str) -> str | None:
    value = data.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"field '{field}' must be a string")
    return value


def _string_list(data: dict[str, object], field: str) -> list[str]:
    if field not in data:
        raise ValueError(f"missing required field '{field}'")
    value = data[field]
    if not isinstance(value, list):
        raise TypeError(f"field '{field}' must be a list")
    items: list[str] = []
    for index, item in enumerate(value):
        item_label = f"{field}[{index}]"
        if not isinstance(item, str):
            raise TypeError(f"field '{item_label}' must be a string")
        if not item.strip():
            raise ValueError(f"field '{item_label}' must be a non-empty string")
        items.append(item)
    return items


def _optional_string_list(data: dict[str, object], field: str) -> list[str]:
    if field not in data:
        return []
    return _string_list(data, field)


def _string_mapping(data: dict[str, object], field: str) -> dict[str, str]:
    if field not in data:
        raise ValueError(f"missing required field '{field}'")
    value = data[field]
    if not isinstance(value, dict):
        raise TypeError(f"field '{field}' must be an object")
    mapping: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError(f"field '{field}' key must be a non-empty string")
        if not isinstance(item, str):
            raise TypeError(f"field '{field}['{key}']' must be a string")
        if not item.strip():
            raise ValueError(f"field '{field}['{key}']' must be a non-empty string")
        mapping[key] = item
    return mapping


@dataclass(frozen=True)
class AcceptedSyncState:
    """Typed accepted upstream sync state."""

    last_accepted_upstream_sha: str
    last_accepted_upstream_date: str
    last_accepted_upstream_ref: str
    notes: str | None = None

    @classmethod
    def from_raw(cls, raw: object) -> "AcceptedSyncState":
        """Validate and parse an accepted sync state JSON object."""
        data = _as_object(raw, "accepted sync state")
        return cls(
            last_accepted_upstream_sha=_required_full_sha(
                data, "last_accepted_upstream_sha", allow_bootstrap=True
            ),
            last_accepted_upstream_date=_required_string(
                data, "last_accepted_upstream_date"
            ),
            last_accepted_upstream_ref=_required_string(
                data, "last_accepted_upstream_ref"
            ),
            notes=_optional_string(data, "notes"),
        )

    def to_json(self) -> dict[str, str]:
        """Return the stable accepted_sync.json wire format."""
        data = {
            "last_accepted_upstream_sha": self.last_accepted_upstream_sha,
            "last_accepted_upstream_date": self.last_accepted_upstream_date,
            "last_accepted_upstream_ref": self.last_accepted_upstream_ref,
        }
        if self.notes is not None:
            data["notes"] = self.notes
        return data


@dataclass(frozen=True)
class MappedAction:
    """Typed action for applying an upstream path to a local sync target."""

    category: str
    local_path: str
    local_target_path: str | None = None

    @classmethod
    def from_raw(cls, raw: object, label: str = "mapped action") -> "MappedAction":
        """Validate and parse one mapped action object."""
        data = _as_object(raw, label)
        try:
            category = _required_string(data, "category")
            local_path = _required_string(data, "local_path")
            local_target_path = _optional_string(data, "local_target_path")
            local_path = validate_repo_relative_path(local_path, "local_path")
            if local_target_path is not None:
                local_target_path = validate_repo_relative_path(
                    local_target_path, "local_target_path"
                )
        except ValueError as exc:
            if label == "mapped action":
                raise
            raise ValueError(f"{label}: {exc}") from exc
        return cls(
            category=category,
            local_path=local_path,
            local_target_path=local_target_path,
        )

    def to_json(self) -> dict[str, str]:
        """Return the stable manifest mapped action wire format."""
        data = {
            "category": self.category,
            "local_path": self.local_path,
        }
        if self.local_target_path is not None:
            data["local_target_path"] = self.local_target_path
        return data


@dataclass(frozen=True)
class PrepManifest:
    """Typed Stage 1 prep manifest."""

    from_upstream_sha: str
    to_upstream_sha: str
    target_upstream_ref: str
    generated_at: str
    changed_upstream_paths: list[str]
    deleted_upstream_paths: list[str]
    blocker_paths: list[str]
    discuss_paths: list[str]
    mapped_actions: dict[str, list[MappedAction]]
    needs_classification_paths: list[str]
    unregistered_local_paths: list[str] = field(default_factory=list)
    upstream_deleted_orphans: list[str] = field(default_factory=list)

    @classmethod
    def from_raw(cls, raw: object) -> "PrepManifest":
        """Validate and parse a prep_manifest.json object."""
        data = _as_object(raw, "prep manifest")
        from_upstream_sha = _required_full_sha(data, "from_upstream_sha")
        to_upstream_sha = _required_full_sha(data, "to_upstream_sha")
        target_upstream_ref = _required_string(data, "target_upstream_ref")
        generated_at = _required_string(data, "generated_at")
        changed_upstream_paths = _string_list(data, "changed_upstream_paths")
        deleted_upstream_paths = _string_list(data, "deleted_upstream_paths")
        blocker_paths = _optional_string_list(data, "blocker_paths")
        discuss_paths = _string_list(data, "discuss_paths")
        needs_classification_paths = _optional_string_list(
            data, "needs_classification_paths"
        )
        unregistered_local_paths = _optional_string_list(
            data, "unregistered_local_paths"
        )
        upstream_deleted_orphans = _optional_string_list(
            data, "upstream_deleted_orphans"
        )
        validate_repo_relative_paths(changed_upstream_paths, "changed_upstream_paths")
        validate_repo_relative_paths(deleted_upstream_paths, "deleted_upstream_paths")
        validate_repo_relative_paths(blocker_paths, "blocker_paths")
        validate_repo_relative_paths(discuss_paths, "discuss_paths")
        validate_repo_relative_paths(
            needs_classification_paths, "needs_classification_paths"
        )
        validate_repo_relative_paths(
            unregistered_local_paths, "unregistered_local_paths", allow_globs=True
        )
        validate_repo_relative_paths(
            upstream_deleted_orphans, "upstream_deleted_orphans", allow_globs=True
        )
        return cls(
            from_upstream_sha=from_upstream_sha,
            to_upstream_sha=to_upstream_sha,
            target_upstream_ref=target_upstream_ref,
            generated_at=generated_at,
            changed_upstream_paths=changed_upstream_paths,
            deleted_upstream_paths=deleted_upstream_paths,
            blocker_paths=blocker_paths,
            discuss_paths=discuss_paths,
            mapped_actions=cls._mapped_actions(data),
            needs_classification_paths=needs_classification_paths,
            unregistered_local_paths=unregistered_local_paths,
            upstream_deleted_orphans=upstream_deleted_orphans,
        )

    @staticmethod
    def _mapped_actions(data: dict[str, object]) -> dict[str, list[MappedAction]]:
        if "mapped_actions" not in data:
            raise ValueError("missing required field 'mapped_actions'")
        value = data["mapped_actions"]
        if not isinstance(value, dict):
            raise TypeError("field 'mapped_actions' must be an object")
        mapped_actions: dict[str, list[MappedAction]] = {}
        for path, actions in value.items():
            if not isinstance(path, str) or not path.strip():
                raise ValueError(
                    "field 'mapped_actions' key must be a non-empty string"
                )
            validate_repo_relative_path(path, f"mapped_actions key '{path}'")
            action_label = f"mapped_actions['{path}']"
            if not isinstance(actions, list):
                raise TypeError(f"field '{action_label}' must be a list")
            mapped_actions[path] = [
                MappedAction.from_raw(action, f"field '{action_label}[{index}]'")
                for index, action in enumerate(actions)
            ]
        return mapped_actions

    def to_json(self) -> dict[str, object]:
        """Return the stable prep_manifest.json wire format."""
        return {
            "from_upstream_sha": self.from_upstream_sha,
            "to_upstream_sha": self.to_upstream_sha,
            "target_upstream_ref": self.target_upstream_ref,
            "generated_at": self.generated_at,
            "changed_upstream_paths": self.changed_upstream_paths,
            "deleted_upstream_paths": self.deleted_upstream_paths,
            "blocker_paths": self.blocker_paths,
            "needs_classification_paths": self.needs_classification_paths,
            "mapped_actions": {
                path: [action.to_json() for action in actions]
                for path, actions in self.mapped_actions.items()
            },
            "discuss_paths": self.discuss_paths,
            "unregistered_local_paths": self.unregistered_local_paths,
            "upstream_deleted_orphans": self.upstream_deleted_orphans,
        }


@dataclass(frozen=True)
class ModifiedUpstreamEntry:
    """Typed registry entry for a modified upstream file."""

    path: str
    discuss: bool
    discuss_reason: str | None = None

    @classmethod
    def from_raw(cls, raw: object, label: str) -> "ModifiedUpstreamEntry":
        """Validate and parse one modified_upstream_files entry."""
        data = _as_object(raw, label)
        try:
            path = _required_string(data, "path")
        except ValueError as exc:
            raise ValueError(f"{label}: {exc}") from exc
        if "discuss" not in data:
            raise ValueError(f"{label}: missing required field 'discuss'")
        discuss = data["discuss"]
        if not isinstance(discuss, bool):
            raise TypeError(f"{label}: field 'discuss' must be a bool")
        discuss_reason = _optional_string(data, "discuss_reason")
        return cls(path=path, discuss=discuss, discuss_reason=discuss_reason)


@dataclass(frozen=True)
class InspiredByUpstreamEntry:
    """Typed registry entry for inspired-by-upstream local files."""

    upstream: str
    divergence_reason: str

    @classmethod
    def from_raw(cls, raw: object, label: str) -> "InspiredByUpstreamEntry":
        """Validate and parse one inspired_by_upstream entry."""
        data = _as_object(raw, label)
        try:
            upstream = _required_string(data, "upstream")
            divergence_reason = _required_string(data, "divergence_reason")
        except ValueError as exc:
            raise ValueError(f"{label}: {exc}") from exc
        return cls(upstream=upstream, divergence_reason=divergence_reason)


@dataclass(frozen=True)
class RegistryData:
    """Typed upstream sync registry data."""

    modified_upstream_files: list[ModifiedUpstreamEntry]
    russian_copies: dict[str, str]
    sbs_copies: dict[str, str]
    dps_copies: dict[str, str]
    tamil_copies: dict[str, str]
    inspired_by_upstream: dict[str, InspiredByUpstreamEntry]
    unique_paths: list[str]
    no_sync_files: list[str]
    skip_sync_patterns: list[str]

    @classmethod
    def from_raw(cls, raw: object) -> "RegistryData":
        """Validate and parse registry.json data."""
        data = _as_object(raw, "registry")
        return cls(
            modified_upstream_files=cls._modified_upstream_files(data),
            russian_copies=_string_mapping(data, "russian_copies"),
            sbs_copies=_string_mapping(data, "sbs_copies"),
            dps_copies=_string_mapping(data, "dps_copies"),
            tamil_copies=_string_mapping(data, "tamil_copies"),
            inspired_by_upstream=cls._inspired_by_upstream(data),
            unique_paths=_string_list(data, "unique_paths"),
            no_sync_files=_string_list(data, "no_sync_files"),
            skip_sync_patterns=_string_list(data, "skip_sync_patterns"),
        )

    @staticmethod
    def _modified_upstream_files(
        data: dict[str, object],
    ) -> list[ModifiedUpstreamEntry]:
        if "modified_upstream_files" not in data:
            raise ValueError("missing required field 'modified_upstream_files'")
        entries = data["modified_upstream_files"]
        if not isinstance(entries, list):
            raise TypeError("field 'modified_upstream_files' must be a list")
        return [
            ModifiedUpstreamEntry.from_raw(
                entry, f"field 'modified_upstream_files[{index}]'"
            )
            for index, entry in enumerate(entries)
        ]

    @staticmethod
    def _inspired_by_upstream(
        data: dict[str, object],
    ) -> dict[str, InspiredByUpstreamEntry]:
        if "inspired_by_upstream" not in data:
            raise ValueError("missing required field 'inspired_by_upstream'")
        entries = data["inspired_by_upstream"]
        if not isinstance(entries, dict):
            raise TypeError("field 'inspired_by_upstream' must be an object")
        parsed: dict[str, InspiredByUpstreamEntry] = {}
        for path, entry in entries.items():
            if not isinstance(path, str) or not path.strip():
                raise ValueError(
                    "field 'inspired_by_upstream' key must be a non-empty string"
                )
            parsed[path] = InspiredByUpstreamEntry.from_raw(
                entry, f"field 'inspired_by_upstream['{path}']'"
            )
        return parsed
