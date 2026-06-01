"""Functions for properties in SBS table"""

import csv
import os
from difflib import SequenceMatcher

from rich.console import Console

from tools.configger import config_read
from tools.paths_dps import DPSPaths

console = Console()

dpspth = DPSPaths()


class SBS_table_tools:
    def load_chant_index_map(self):
        """Load the chant-index mapping from a TSV file into a dictionary."""
        chant_index_map = {}
        if dpspth.sbs_index_path:
            with open(dpspth.sbs_index_path, "r", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile, delimiter="\t")
                next(reader)  # Skip header row
                for row in reader:
                    index, chant = row[0], row[1]
                    chant_index_map[chant] = int(index)
        return chant_index_map

    def load_chant_link_map(self):
        """Load the chant-link mapping from a TSV file into a dictionary."""
        chant_link_map = {}
        if dpspth.sbs_index_path:
            with open(dpspth.sbs_index_path, "r", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile, delimiter="\t")
                next(reader)  # Skip header row
                for row in reader:
                    chant, link = row[1], row[4]
                    chant_link_map[chant] = link
        return chant_link_map

    def fetch_sbs_index(self, pali_chant: str) -> tuple[str, str] | None:
        """Return (english_chant, chapter) for exact pali_chant match, or None."""
        if not dpspth.sbs_index_path:
            return None
        with open(dpspth.sbs_index_path, encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                if row["pali_chant"] == pali_chant:
                    return row["english_chant"], row["chapter"]
        return None

    def load_valid_chants(self) -> list[str]:
        """Return all pali_chant values from sbs_index.csv."""
        if not dpspth.sbs_index_path:
            return []
        with open(dpspth.sbs_index_path, encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            return [row["pali_chant"] for row in reader]

    def load_valid_mappings(self) -> set[tuple[str, str, str]]:
        """Return set of (pali_chant, english_chant, chapter) from sbs_index.csv."""
        if not dpspth.sbs_index_path:
            return set()
        mappings: set[tuple[str, str, str]] = set()
        with open(dpspth.sbs_index_path, encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                mappings.add((row["pali_chant"], row["english_chant"], row["chapter"]))
        return mappings

    def find_closest_chant(
        self, pali_chant: str, threshold: float = 0.8
    ) -> tuple[str, float] | None:
        """Return (best_matching_pali_chant, ratio) above threshold, or None."""
        best: tuple[str, float] | None = None
        for candidate in self.load_valid_chants():
            ratio = SequenceMatcher(None, pali_chant, candidate).ratio()
            if ratio >= threshold:
                if best is None or ratio > best[1]:
                    best = (candidate, ratio)
        return best

    def load_class_link_map(self):
        """Load the class-link mapping from a TSV file into a dictionary."""
        class_link_map = {}
        if dpspth.class_index_path:
            with open(dpspth.class_index_path, "r", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile, delimiter="\t")
                next(reader)  # Skip header row
                for row in reader:
                    class_num, link = (
                        int(row[0]),
                        row[2],
                    )  # Convert class_num to integer
                    class_link_map[class_num] = link
        return class_link_map

    def load_sutta_link_map(self):
        """Load the sutta-link mapping from a TSV file into a dictionary."""
        sutta_link_map = {}
        if dpspth.sutta_index_path:
            with open(dpspth.sutta_index_path, "r", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile, delimiter="\t")
                next(reader)  # Skip header row
                for row in reader:
                    sutta_num, link = row[0], row[2]
                    sutta_link_map[sutta_num] = link
        return sutta_link_map

    def generate_sbs_audio(self, lemma_clean):
        """Generate the sbs_audio string based on the presence of an audio file."""
        anki_media_dir_path = config_read("anki", "media_dir")
        if anki_media_dir_path:
            audio_path = os.path.join(anki_media_dir_path, f"{lemma_clean}.mp3")
            if os.path.exists(audio_path):
                return f"[sound:{lemma_clean}.mp3]"
        return ""


def paragraphs_are_similar_sbs(paragraph1, paragraph2, threshold):
    matcher = SequenceMatcher(None, paragraph1, paragraph2)
    similarity_ratio = matcher.ratio()
    return similarity_ratio >= threshold


list_of_discourses = [
    "MN107",
    "SN12.1",
    "SN12.10",
    "SN12.12",
    "SN12.15",
    "SN12.20",
    "SN12.22",
    "SN12.41",
    "SN12.51",
    "SN12.55",
    "SN12.61",
    "SN12.65",
    "SN12.66",
    "SN22.12",
    "SN22.18",
    "SN22.23",
    "SN22.24",
    "SN22.26",
    "SN22.28",
    "SN22.33",
    "SN22.58",
    "SN22.59",
    "SN22.63",
    "SN22.71",
    "SN22.78",
    "SN22.82",
    "SN22.94",
    "SN22.95",
    "SN22.102",
    "SN35.24",
    "SN35.28",
    "SN35.53",
    "SN35.60",
    "SN35.70",
    "SN35.85",
    "SN35.93",
    "SN35.118",
    "SN35.136",
    "SN35.228",
    "SN35.230",
    "SN35.232",
    "SN35.241",
    "SN35.246",
    "SN35.247",
    "SN43.1",
    "SN43.3",
    "SN43.4",
    "SN43.5",
    "SN43.6",
    "SN43.7",
    "SN43.8",
    "SN43.9",
    "SN43.10",
    "SN43.11",
    "SN43.12",
    "SN43.13",
    "SN43.14",
    "SN43.15",
    "SN43.16",
    "SN43.17",
    "SN43.18",
    "SN43.19",
    "SN43.20",
    "SN43.21",
    "SN43.22",
    "SN43.23",
    "SN43.24",
    "SN43.25",
    "SN43.26",
    "SN43.27",
    "SN43.28",
    "SN43.29",
    "SN43.30",
    "SN43.31",
    "SN43.32",
    "SN43.33",
    "SN43.34",
    "SN43.35",
    "SN43.36",
    "SN43.37",
    "SN43.38",
    "SN43.39",
    "SN43.40",
    "SN43.41",
    "SN43.42",
    "SN43.43",
    "SN43.44",
    "SN43.14-43",
    "SN45.2",
    "SN45.5",
    "SN45.8",
    "SN45.24",
    "SN45.49",
    "SN45.91",
    "SN45.160",
    "SN46.1",
    "SN46.2",
    "SN46.3",
    "SN46.5",
    "SN46.6",
    "SN46.14",
    "SN46.53",
    "SN47.1",
    "SN47.2",
    "SN47.4",
    "SN47.7",
    "SN47.9",
    "SN47.19",
    "SN47.20",
    "SN47.29",
    "SN56.1",
    "SN56.5",
    "SN56.7",
    "SN56.13",
    "SN56.21",
    "SN56.25",
    "SN56.27",
    "SN56.28",
    "SN56.29",
    "SN56.31",
    "SN56.33",
    "SN56.34",
    "SN56.37",
    "SN56.38",
    "SN56.42",
    "SN56.44",
    "SN56.47",
    "SN56.49",
]


sbs_category_list = [
    "sn12",
    "sn22",
    "sn35",
    "sn43",
    "sn45",
    "sn46",
    "sn47",
    "sn56",
    "mn107",
]


def recalculate_all_sbs_indices(db_session, db):
    """Recalculate sbs_index for all entries in the db and commit changes."""
    console.print("[green]Calculating sbs_index")
    try:
        for i in db:
            if i.sbs:
                sbs_index_old = i.sbs.sbs_index
                sbs_index_value = i.sbs.calculate_index()
                if sbs_index_old != sbs_index_value:
                    i.sbs.sbs_index = sbs_index_value
                    console.print(
                        f"[cyan]{i.lemma_1}[/cyan] old index {sbs_index_old} changed to {sbs_index_value}"
                    )

        db_session.commit()

    except Exception as e:
        console.print(f"[bold red]{str(e)}")
