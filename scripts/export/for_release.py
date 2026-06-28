"""Explicit manifest of study-tools release asset filenames for the upload pipeline.

Called by upload_study_tools.sh to enumerate every asset that should be attached
to a sasanarakkha/study-tools GitHub release.
"""

RELEASE_ASSETS: list[str] = [
    "common-roots.apkg",
    "common-roots.csv",
    "dhp-vocab.apkg",
    "dhp-vocab.csv",
    "grammar-pali-class-abbr.csv",
    "grammar-pali-class-gramm.csv",
    "grammar-pali-class-sandhi.csv",
    "grammar-pali-class.apkg",
    "parittas.apkg",
    "parittas.csv",
    "patimokkha-word-by-word.apkg",
    "patimokkha-word-by-word.csv",
    "phonetic-pali-class.apkg",
    "phonetic-pali-class.csv",
    "roots-pali-class.apkg",
    "roots-pali-class.csv",
    "ru-pali-vocab.apkg",
    "ru-pali-vocab.csv",
    "sbs-pali-english-vocab.apkg",
    "sbs-pd.csv",
    "sbs-rus.csv",
    "suttas-advanced-pali-class.apkg",
    "suttas-advanced-pali-class.csv",
    "vibhanga.apkg",
    "vibhanga.csv",
    "vocab-pali-class.apkg",
    "vocab-pali-class.csv",
    "ru_common_roots.csv",
    "ru_cl_sum_gramm.csv",
]

if __name__ == "__main__":
    print(" ".join(RELEASE_ASSETS))
