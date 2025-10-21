# -*- coding: utf-8 -*-
import json
import re
from pathlib import Path
from typing import Optional

from tools.paths_dps import DPSPaths
from tools.printer import printer as pr


class DpsExampleStashManager:
    """Manages stashing and reloading example data (source, sutta, example) for DPS fields."""

    def __init__(self, toolkit=None):
        self._stash_path: Path = DPSPaths().example_stash_json_path
        self.stash_data: dict[str, dict[str, str]] = {}
        self._load()

    def _load(self) -> None:
        """Load stash data from JSON file."""
        if not self._stash_path.exists():
            self.stash_data = {}
            return

        try:
            with open(self._stash_path, "r", encoding="utf-8") as f:
                if loaded := json.load(f):
                    self.stash_data = loaded if isinstance(loaded, dict) else {}
        except (json.JSONDecodeError, Exception) as e:
            pr.error(f"Error loading DPS stash {self._stash_path}: {e}")
            self.stash_data = {}

    def _save(self) -> None:
        """Save current stash data to JSON file."""
        try:
            self._stash_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._stash_path, "w", encoding="utf-8") as f:
                json.dump(self.stash_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            pr.error(f"Error saving DPS stash {self._stash_path}: {e}")

    def stash(self, key: str, fields_dict: dict[str, str]) -> None:
        """Stash data into specified slot."""
        # Clean example field if present
        if "example" in fields_dict:
            fields_dict["example"] = re.sub(r"</?b>", "", fields_dict["example"])
        
        self.stash_data[key] = fields_dict
        self._save()

    def reload(self, key: str) -> Optional[dict[str, str]]:
        """Reload stashed data from specified slot."""
        return self.stash_data.get(key)

    @property
    def last_example(self) -> Optional[dict[str, str]]:
        """Get the last stashed example."""
        return self.reload("dps_last")

    @last_example.setter
    def last_example(self, value: dict[str, str]) -> None:
        """Set the last example."""
        self.stash("dps_last", value)

    def stash_shared_example(self, fields_dict: dict[str, str]) -> None:
        """Stashes the shared example data for DPS fields."""
        self.stash("dps_shared", fields_dict)

    def reload_shared_example(self) -> Optional[dict[str, str]]:
        """Reloads the shared example data for DPS fields."""
        return self.reload("dps_shared")
