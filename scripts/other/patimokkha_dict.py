"""Generate HTML files from Pātimokkha Word by Word Excel data."""
from pathlib import Path
import pandas as pd
import json
from rich.console import Console
from tools.printer import printer as pr
from tools.paths_dps import DPSPaths

def load_and_prepare_dataframe(excel_path: Path) -> pd.DataFrame | None:
    """Load Excel file and prepare DataFrame."""
    try:
        df = pd.read_excel(excel_path, engine="openpyxl")
        return df.replace("\n", "<br>")
    except Exception as e:
        Console().print(f"[red]Error loading Excel file: {e}[/red]")
        return None

def ensure_directories_exist(*paths: Path, console: Console) -> None:
    """Create directories if they don't exist."""
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)
        if not path.exists() or not path.is_dir():
            console.print(f"[bold red]CRITICAL: Directory {path} was NOT created or is not a directory after attempt.[/bold red]")
        else:
            console.print(f"[green]Confirmed directory exists: {path}[/green]")

def generate_json_files(df: pd.DataFrame, json_dir: Path, console: Console) -> list[dict[str, str]]:
    """Generate JSON files from DataFrame and return source metadata."""
    try:
        # Generate sources.json
        sources_json_path = json_dir / "sources.json"
        df[["source", "abbrev"]].ffill().drop_duplicates().to_json(
            sources_json_path, force_ascii=False, orient='records', indent=2
        )
        
        # Load and filter sources
        if not sources_json_path.exists():
            console.print(f"[bold red]CRITICAL: JSON file {sources_json_path} does NOT exist after write attempt.[/bold red]")
 
        with open(sources_json_path) as f:
            sources = [sj for sj in json.load(f) if sj["source"] is not None]
        
        # Generate individual source JSON files
        for source in sources:
            source_df = df[df["source"] == source["source"]]
            source_json_path = json_dir / f"{source['source']}.json"
            source_df[
                ["abbrev", "source", "sentence", "pali_1", "pos", "grammar", "case", 
                "meaning", "meaning_lit", "root", "base", "construction", 
                "compound_type", "compound_construction"]
            ].fillna("").to_json(
                source_json_path,
                force_ascii=False, orient='records', indent=2
            )
            if not source_json_path.exists():
                console.print(f"[bold red]CRITICAL: Source JSON file {source_json_path} does NOT exist after write attempt.[/bold red]")
 
        return sources
    except Exception as e:
        Console().print(f"[red]Error generating JSON files: {e}[/red]")
        return []

def generate_main_html(pat_dir: Path, sources: list[dict[str, str]], console: Console) -> bool:
    """Generate main HTML content table. Returns True on success."""
    main_html_path = pat_dir / "main.html"
    console.print(f"[cyan]Generating main HTML at: {main_html_path}[/cyan]")
    try:
        with open(main_html_path, "w") as f:
            f.write("""<!DOCTYPE html>
<html>
<head><link rel="stylesheet" href="scripts/main.css"></head>
<body>
<div class="topnav">
    <a class="active" href="main.html">[SBS] Bhikkhu Pātimokkha</a>
</div>\n""")
            
            for source in sources:
                f.write(f"""<h3><a href="./{source['source']}/{source['source']}.html">
    {source['abbrev']} {source['source']}
</a></h3>\n""")
            
            f.write("</body>\n</html>")
    except Exception as e:
        console.print(f"[red]Error generating main HTML: {e}[/red]")
        return False
    return True

def generate_source_html(pat_dir: Path, json_dir: Path, source: dict[str, str], console: Console) -> bool:
    """Generate HTML page for a single source. Returns True on success."""
    source_dir = pat_dir / source["source"]
    html_path = source_dir / f"{source['source']}.html"
    
    try:
        source_dir.mkdir(exist_ok=True)
        # console.print(f"[cyan]Generating HTML for {source['source']} at: {html_path}[/cyan]")
        
        with open(html_path, "w") as f:
            # Write HTML header
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="../scripts/main.css">
</head>
<body>
    <button onclick="topFunction()" id="topBtn" title="Go to top">Top</button>
    <div class="topnav">
        <a class="active" href="../main.html">Home</a>
        <a href="#{source['source']}"><b>[{source['abbrev']}] {source['source']}</b></a>
        <a class="link" href="https://docs.google.com/forms/d/e/1FAIpQLSdG6zKDtlwibtrX-cbKVn4WmIs8miH4VnuJvb7f94plCDKJyA/viewform?usp=pp_url" style="float:right;">Feedback</a>
    </div>
    <h1>{source['abbrev']}\t{source['source']}</h1>\n""")
            
            # Load source data
            source_df = pd.read_json(json_dir / f"{source['source']}.json")
            
            # Write sentence links
            f.write('<div class="sentence">')
            sentences = source_df[["sentence"]].drop_duplicates().ffill()
            for _, row in sentences.iterrows():
                if row["sentence"]:
                    f.write(f"""<a href="#{row['sentence'].replace(' ', '_')}">
                        {row['sentence']}
                    </a><br>\n""")
            f.write("</div><br><br><hr>\n")
            
            # Write sentence details
            for _, sentence_row in sentences.iterrows():
                if sentence_row["sentence"]:
                    sentence = sentence_row["sentence"]
                    f.write(f"""<b style="font-size:20px" id="{sentence.replace(' ', '_')}">
                        {sentence}
                    </b><br>\n""")
                    
                    # Write word definitions table
                    definitions = source_df[source_df["sentence"] == sentence][[
                        "pali_1", "pos", "grammar", "case", "meaning", 
                        "meaning_lit", "root", "base", "construction", 
                        "compound_type", "compound_construction"
                    ]].fillna("")
                    
                    table_html = definitions.to_html(justify='left', index=False)
                    table_html = table_html.replace("0", "").replace("pali_1", "pāḷi")
                    f.write(f"{table_html}<br><br>\n")
            
            f.write("""<a class="active" href="../main.html">Home</a>
    <script src="../scripts/main.js"></script>
</body>
</html>""")
    except Exception as e:
        console.print(f"[red]Error generating HTML for {source['source']}: {e}[/red]")
        return False
    return True

def generate_pat_links_tsv(tsv_path: Path, sources: list[dict[str, str]], console: Console) -> bool:
    """Generate TSV file with web links to source HTML pages. Returns True on success."""
    console.print("[cyan]Generating links to source[/cyan]")
    try:
        data = [{
            "source": source["source"],
            "web_link": f"https://sasanarakkha.github.io/study-tools/bhikkhu_patimokkha/{source['source']}/{source['source']}.html"
        } for source in sources]
        
        pd.DataFrame(data).to_csv(tsv_path, sep='\t', index=False)
        console.print(f"[green]TSV file generated at {tsv_path}[/green]")
    except Exception as e:
        console.print(f"[red]Error generating TSV file: {e}[/red]")
        return False
    return True

def main() -> None:
    """Main function to generate HTML from Pātimokkha data."""
    console = Console()
    import os
    console.print(f"[cyan]os.getcwd() reports: {os.getcwd()}[/cyan]")
    pr.tic()
    console.print("[yellow]Starting HTML generation from Pātimokkha ODS[/yellow]")

    # Define paths
    project_dir = Path.cwd()
    doc_dir = project_dir.parent
    pat_dir = doc_dir / "sasanarakkha" / "study-tools" / "bhikkhu_patimokkha"
    downloads_dir = doc_dir.parent / "Downloads"
    json_dir = pat_dir / "json"
    dps_paths = DPSPaths()
    tsv_path = dps_paths.pat_links_path

    # Load and prepare data
    excel_path = downloads_dir / "Pātimokkha Word by Word.xlsx"
    df = load_and_prepare_dataframe(excel_path)
    if df is None:
        return

    # Ensure directories exist
    ensure_directories_exist(pat_dir, json_dir, console=console)

    # Generate JSON files and get sources
    sources = generate_json_files(df, json_dir, console)
    if not sources:
        console.print("[red]No source data generated[/red]")
        return

    # Track generation results
    success_count = 0
    error_count = 0
    
    # Generate main HTML
    if not generate_main_html(pat_dir, sources, console):
        error_count += 1
    
    # Generate source HTML pages
    console.print(f"[yellow]Generating HTML pages for {len(sources)} sources...[/yellow]")
    for source in sources:
        if generate_source_html(pat_dir, json_dir, source, console):
            success_count += 1
        else:
            error_count += 1
    
    # Generate TSV file
    if not generate_pat_links_tsv(tsv_path, sources, console):
        error_count += 1
    
    # Print summary
    console.print(f"[green]Successfully generated: {success_count} HTML pages[/green]")
    if error_count > 0:
        console.print(f"[red]Failed to generate: {error_count} items[/red]")
    else:
        console.print("[green]All files generated successfully[/green]")
    pr.toc()

if __name__ == "__main__":
    main()
