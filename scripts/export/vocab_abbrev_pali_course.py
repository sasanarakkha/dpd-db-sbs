# Generate Markdown vocabulary and abbreviation pages for dpd-pali-courses.

import csv
from pathlib import Path
from sqlalchemy.orm import joinedload

from db.models import DpdHeadword, SBS
from db.db_helpers import get_db_session
from tools.paths import ProjectPaths
from tools.printer import printer as pr

OUTPUT_DIR = Path("/Users/deva/Documents/dpd-pali-courses/docs/generated")

def generate_vocab(db_session, output_dir: Path) -> None:
    """Iterate SBS classes 2-29, skip empty, write cumulative Markdown vocabulary files for web."""
    pr.green("vocab")
    
    vocab_dir = output_dir / "vocab"
    vocab_dir.mkdir(parents=True, exist_ok=True)
    
    total_files = 0
    # Range 2-29 (class 1 has no words under the combined filter)
    for sbs_class in range(2, 30):
        words = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.sbs)).join(SBS).filter(
            SBS.sbs_class <= sbs_class,
            SBS.class_anki <= sbs_class
        ).all()
        
        if not words:
            continue

        # Sort by sbs_class naturally, then by lemma_1
        words.sort(key=lambda x: (x.sbs.sbs_class, x.lemma_1))
            
        filename = vocab_dir / f"class-{sbs_class:02d}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# Class {sbs_class} Vocabulary\n\n")
            f.write("| Pāḷi | POS | Meaning | Root | Construction | Pattern | cl. |\n")
            f.write("| --- | --- | --- | --- | --- | --- | --- |\n")
            
            for word in words:
                if word.rt:
                    root_value = f"{word.root_clean} {word.rt.root_group} {word.root_sign} ({word.rt.root_meaning})"
                else:
                    root_value = word.root_key if word.root_key else ""
                
                # Replace markdown pipes to avoid broken tables
                pali = word.lemma_1.replace("|", "\\|")
                pos = word.pos.replace("|", "\\|")
                meaning = word.meaning_1.replace("|", "\\|")
                root = root_value.replace("|", "\\|")
                construction = word.construction_line1.replace("|", "\\|") if word.construction_line1 else ""
                pattern = word.pattern.replace("|", "\\|") if word.pattern else ""
                
                # Use word.sbs.sbs_class for the class column
                f.write(f"| {pali} | {pos} | {meaning} | {root} | {construction} | {pattern} | {word.sbs.sbs_class} |\n")
        
        total_files += 1

    if total_files > 0:
        pr.yes(f"{total_files} files")
    else:
        pr.no("0 files")

def generate_vocab_index(output_dir: Path) -> None:
    """Generate index file for vocabulary section."""
    pr.green("vocab index")
    
    vocab_dir = output_dir / "vocab"
    vocab_dir.mkdir(parents=True, exist_ok=True)
        
    index_file = vocab_dir / "index.md"
    
    files = sorted([f for f in vocab_dir.glob("class-*.md")])
    if not files:
        pr.no("no class files found")
        return
        
    with open(index_file, "w", encoding="utf-8") as f:
        f.write("# Vocabulary Reference\n\n")
        f.write("Each class includes the vocabulary from all previous classes (see homework).\n\n")
        
        for file in files:
            class_num = int(file.stem.split("-")[1])
            f.write(f"- [Class {class_num}]({file.name})\n")
            
    pr.yes("ok")

def generate_abbreviations(pth: ProjectPaths, output_dir: Path) -> None:
    """Read abbreviations.tsv, filter, and write to single Markdown file."""
    pr.green("abbrev")
    
    tsv_path = pth.abbreviations_tsv_path
    if not tsv_path.exists():
        pr.no(f"File not found: {tsv_path}")
        return
        
    output_file = output_dir / "abbreviations.md"
    
    try:
        with open(tsv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            
            rows = []
            for row in reader:
                abbrev = row.get("abbrev", "")
                # Filter: drop rows where abbrev contains uppercase letters
                if any(c.isupper() for c in abbrev):
                    continue
                rows.append(row)
                
        if not rows:
            pr.no("no matching abbreviations")
            return
            
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# Abbreviations\n\n")
            f.write("| abbrev | meaning | pāli | example | explanation |\n")
            f.write("| --- | --- | --- | --- | --- |\n")
            
            for row in rows:
                abbrev = row.get("abbrev", "").replace("|", "\\|")
                meaning = row.get("meaning", "").replace("|", "\\|")
                pali = row.get("pāli", "").replace("|", "\\|")
                example = row.get("example", "").replace("|", "\\|")
                explanation = row.get("explanation", "").replace("|", "\\|")
                f.write(f"| {abbrev} | {meaning} | {pali} | {example} | {explanation} |\n")
                
        pr.yes("ok")
    except Exception as e:
        pr.no(f"Error processing abbreviations: {e}")

def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    generate_vocab(db_session, OUTPUT_DIR)
    generate_vocab_index(OUTPUT_DIR)
    generate_abbreviations(pth, OUTPUT_DIR)
    
    db_session.close()

if __name__ == "__main__":
    main()
