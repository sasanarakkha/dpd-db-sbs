# Documentation System Setup Guide

This guide documents the documentation system used in the `dpd-db` project. It is intended to help replicate this setup in another repository.

## Overview

The documentation site is a static site generated using **MkDocs** with the **Material for MkDocs** theme. It features:
- **Markdown Source**: Content is written in Markdown in the `docs/` directory.
- **Python Automation**: Custom Python scripts generate dynamic content (e.g., bibliographies, changelogs, indices) from data sources (TSV files) before the build.
- **Automated Deployment**: A GitHub Actions workflow builds the site and deploys it to a separate GitHub Pages repository (`digitalpalidictionary.github.io`).

## Prerequisites & Dependencies

To build and manage the documentation locally, you need:

1.  **Python 3.12+**
2.  **uv** (Python package manager)
3.  **MkDocs Dependencies**:
    *   `mkdocs`
    *   `mkdocs-material`
    *   `PyYAML`

These are managed via `pyproject.toml` and installed via `uv sync`.

## Configuration (`mkdocs.yaml`)

The central configuration file is `mkdocs.yaml`. Key sections include:

*   **`site_name`, `site_url`, `repo_url`**: Basic metadata.
*   **`nav`**: Explicitly defines the navigation structure.
*   **`theme`**: Uses `material`. configured with features like:
    *   `content.code.copy`
    *   `navigation.footer`
    *   `navigation.instant`
    *   `navigation.indexes`
*   **`extra_css`**: Custom styling located in `docs/stylesheets/`.
*   **`markdown_extensions`**: Enhancements like `admonition`, `attr_list`, `pymdownx.highlight`, `pymdownx.superfences`.
*   **`plugins`**: `search`, `blog` (for release notes/blog posts), `tags`.

## Directory Structure

*   **`docs/`**: Source directory for Markdown files.
    *   `assets/`: Images and other static assets.
    *   `stylesheets/`: Custom CSS files (`extra.css`, `dpd-variables.css`).
    *   Subdirectories (e.g., `features/`, `install/`, `technical/`) organize content.
*   **`tools/`**: Contains Python scripts for content generation.
*   **`scripts/build/`**: Contains scripts for build-time modifications.
*   **`.github/workflows/`**: CI/CD configuration.

## Content Generation Workflow

The project uses a "generate-then-build" approach. Before running `mkdocs build`, several Python scripts are executed to populate or update specific Markdown files.

### 1. Data-Driven Content (The `tools/` scripts)

These scripts read data (often from TSV files or git history) and write it to Markdown files in `docs/`.

*   `tools/docs_update_abbreviations.py`: Updates abbreviation lists.
*   `tools/docs_update_bibliography.py`: Generates the bibliography page.
*   `tools/docs_update_thanks.py`: Generates the "Thanks" page from a TSV source.
*   `tools/docs_changelog_and_release_notes.py`: Generates changelogs from git history or release notes.

**To replicate:** You will need to identify which parts of your new documentation can be automated and write similar scripts using your project's data sources.

### 2. Build-Time Enhancements (The `scripts/build/` scripts)

These scripts run immediately before the build to structure the content.

*   **`scripts/build/docs_add_indexes.py`**: This script reads the `nav` section of `mkdocs.yaml`. For every subdirectory in the navigation, it finds the corresponding `index.md` and appends a list of links to all other pages in that subdirectory. This automates the creation of index pages.

## Build and Deployment

### Local Development

1.  **Update Content**: Run the generation scripts.
    ```bash
    # Example command from justfile
    just docs-update
    ```
    (This runs the python scripts in `tools/`)

2.  **Serve Locally**:
    ```bash
    mkdocs serve
    ```

### CI/CD (GitHub Actions)

The workflow is defined in `.github/workflows/static.yml`.

**Triggers**: Pushes to `main` affecting `docs/**` or `mkdocs.yaml`.

**Steps**:
1.  **Checkout Code**.
2.  **Setup Python & uv**.
3.  **Install Dependencies**: `uv pip install --system mkdocs mkdocs-material PyYAML`.
4.  **Run Build Scripts**:
    *   `python3 scripts/build/docs_add_indexes.py` (Populate index pages)
    *   `python3 scripts/build/docs_update_css.py` (Update CSS variables if needed)
5.  **Build Site**: `mkdocs build`.
6.  **Deploy**:
    *   Clones the target repository (e.g., `username.github.io`).
    *   Syncs the `site/` directory content to the repo.
    *   Commits and pushes changes.

## Replication Checklist

To set this up in a new repository:

1.  [ ] **Initialize MkDocs**: Run `mkdocs new .` or copy `mkdocs.yaml` and adjust settings (site name, repo URL, nav).
2.  [ ] **Install Theme**: Add `mkdocs-material` to your dependencies.
3.  [ ] **Create Source Directory**: Set up `docs/` with your markdown files.
4.  [ ] **Add Custom CSS**: Copy `docs/stylesheets/` if you want the same styling.
5.  [ ] **Copy Scripts**:
    *   Copy `scripts/build/docs_add_indexes.py` if you want automated index pages.
    *   Adapt `tools/docs_update_*.py` scripts if you have data-driven content.
6.  [ ] **Configure CI/CD**: Copy `.github/workflows/static.yml` and adapt it:
    *   Change the deploy step to push to `gh-pages` branch or your specific pages repository.
    *   Ensure you have the necessary secrets (like `DPD_DEPLOY_KEY` or `GITHUB_TOKEN`) configured in your repo settings.
7.  [ ] **Update `justfile` or `Makefile`**: Add commands to run your update scripts and build command for easy local use.
