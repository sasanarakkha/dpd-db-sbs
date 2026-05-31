#!/usr/bin/env python3

"""Define typed schema objects for upstream sync metadata JSON files."""

from dataclasses import dataclass


def _as_object(raw: object, label: str) -> dict[str, object]:
    if not isinstance(raw, dict):
        raise ValueError(f"{label} must be a JSON object")
    return raw


def _required_string(data: dict[str, object], field: str) -> str:
    if field not in data:
        raise ValueError(f"missing required field '{field}'")
    value = data[field]
    if not isinstance(value, str):
        raise ValueError(f"field '{field}' must be a string")
    if not value.strip():
        raise ValueError(f"field '{field}' must be a non-empty string")
    return value


def _optional_string(data: dict[str, object], field: str) -> str | None:
    value = data.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"field '{field}' must be a string")
    return value


def _string_list(data: dict[str, object], field: str) -> list[str]:
    if field not in data:
        raise ValueError(f"missing required field '{field}'")
    value = data[field]
    if not isinstance(value, list):
        raise ValueError(f"field '{field}' must be a list")
    items: list[str] = []
    for index, item in enumerate(value):
        item_label = f"{field}[{index}]"
        if not isinstance(item, str):
            raise ValueError(f"field '{item_label}' must be a string")
        if not item.strip():
            raise ValueError(f"field '{item_label}' must be a non-empty string")
        items.append(item)
    return items


def _string_mapping(data: dict[str, object], field: str) -> dict[str, str]:
    if field not in data:
        raise ValueError(f"missing required field '{field}'")
    value = data[field]
    if not isinstance(value, dict):
        raise ValueError(f"field '{field}' must be an object")
    mapping: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError(f"field '{field}' key must be a non-empty string")
        if not isinstance(item, str):
            raise ValueError(f"field '{field}['{key}']' must be a string")
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
            last_accepted_upstream_sha=_required_string(
                data, "last_accepted_upstream_sha"
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
    discuss_paths: list[str]
    mapped_actions: dict[str, list[MappedAction]]

    @classmethod
    def from_raw(cls, raw: object) -> "PrepManifest":
        """Validate and parse a prep_manifest.json object."""
        data = _as_object(raw, "prep manifest")
        from_upstream_sha = _required_string(data, "from_upstream_sha")
        to_upstream_sha = _required_string(data, "to_upstream_sha")
        target_upstream_ref = _required_string(data, "target_upstream_ref")
        generated_at = _required_string(data, "generated_at")
        changed_upstream_paths = _string_list(data, "changed_upstream_paths")
        deleted_upstream_paths = _string_list(data, "deleted_upstream_paths")
        discuss_paths = _string_list(data, "discuss_paths")
        return cls(
            from_upstream_sha=from_upstream_sha,
            to_upstream_sha=to_upstream_sha,
            target_upstream_ref=target_upstream_ref,
            generated_at=generated_at,
            changed_upstream_paths=changed_upstream_paths,
            deleted_upstream_paths=deleted_upstream_paths,
            discuss_paths=discuss_paths,
            mapped_actions=cls._mapped_actions(data),
        )

    @staticmethod
    def _mapped_actions(data: dict[str, object]) -> dict[str, list[MappedAction]]:
        if "mapped_actions" not in data:
            raise ValueError("missing required field 'mapped_actions'")
        value = data["mapped_actions"]
        if not isinstance(value, dict):
            raise ValueError("field 'mapped_actions' must be an object")
        mapped_actions: dict[str, list[MappedAction]] = {}
        for path, actions in value.items():
            if not isinstance(path, str) or not path.strip():
                raise ValueError(
                    "field 'mapped_actions' key must be a non-empty string"
                )
            action_label = f"mapped_actions['{path}']"
            if not isinstance(actions, list):
                raise ValueError(f"field '{action_label}' must be a list")
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
            "mapped_actions": {
                path: [action.to_json() for action in actions]
                for path, actions in self.mapped_actions.items()
            },
            "discuss_paths": self.discuss_paths,
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
            raise ValueError(f"{label}: field 'discuss' must be a bool")
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
            raise ValueError("field 'modified_upstream_files' must be a list")
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
            raise ValueError("field 'inspired_by_upstream' must be an object")
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
