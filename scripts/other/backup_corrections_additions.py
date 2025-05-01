#!/usr/bin/env python3

"""pull corrections and additions to git"""

from git import Repo
from rich import print
from tools.printer import printer as pr
from datetime import datetime


def backup_paliword_paliroot():
    pr.tic()
    print("[bright_yellow]Backing corrections and additions")
    git_commit()
    pr.toc()


def are_files_modified(repo, file_paths):
    diff_index = repo.index.diff(None)  # Compares the working directory with the index
    for file_path in file_paths:
        if any(
            change.a_path == file_path or change.b_path == file_path
            for change in diff_index
        ):
            return True
    return False


def git_commit():
    try:
        repo = Repo("./")

        files_to_check = [
            "gui/corrections.tsv",
            "gui/additions.tsv",
            "shared_data/deconstructor/manual_corrections.tsv",
            "shared_data/deconstructor/checked.csv",
            "shared_data/deconstructor/variant_readings.tsv",
            "shared_data/sbs_csvs/vinaya.tsv",
            "shared_data/rus/russian_words_user_dict.txt",
            "gui/delated_words_history.tsv",
        ]

        # Check for changes in specific files
        if not are_files_modified(repo, files_to_check):
            print("[bold red]No changes to commit.")
            return False

        index = repo.index
        index.add(
            [
                "gui/corrections.tsv",
                "gui/additions.tsv",
                "shared_data/deconstructor/manual_corrections.tsv",
                "shared_data/deconstructor/checked.csv",
                "shared_data/deconstructor/variant_readings.tsv",
                "shared_data/sbs_csvs/vinaya.tsv",
                "shared_data/rus/russian_words_user_dict.txt",
                "gui/delated_words_history.tsv",
            ]
        )
        commit = index.commit("corrections & additions")

        print("[blue]Commit Details:")
        commit_details = repo.commit(commit)

        print(f"Commit ID: {commit_details.hexsha}")
        print(f"Message: {commit_details.message.strip()}")
        print(f"Author: {commit_details.author.name} <{commit_details.author.email}>")
        print(
            f"Committer: {commit_details.committer.name} <{commit_details.committer.email}>"
        )
        print(
            f"Authored Date: {datetime.utcfromtimestamp(commit_details.authored_date)}"
        )
        print(
            f"Committed Date: {datetime.utcfromtimestamp(commit_details.committed_date)}"
        )

        return True
    except Exception as e:
        print(f"[bold red]Error occurred during commit: {e}")
        return False


if __name__ == "__main__":
    backup_paliword_paliroot()
