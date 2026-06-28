#!/bin/bash
# This script uploads a file to the latest release of a GitHub repository.
# It requires the GitHub CLI (gh) to be installed and authenticated.
# It also requires jq to parse JSON responses.
# Ensure the script is run from the correct directory
# and that the file to be uploaded exists.
# Check if gh and jq are installed

#  Function to get the latest release tag from GitHub
get_latest_release() {
    repo_owner="sasanarakkha"
    repo_name="study-tools"
    gh api "repos/$repo_owner/$repo_name/releases/latest" --jq '.tag_name'
}

# Set the directory you want to work in
cd "$HOME/Documents/sasanarakkha/study-tools/temp-push" || exit

# Print current working directory
echo "Current working directory: $(pwd)"

# List files in the current directory
echo "Files in the directory:"
ls

# Prompt the user for input
read -p "Enter the full filename (including extension): " filename

# Check if the user provided an argument
if [ -z "$filename" ]; then
    echo "Filename cannot be empty. Exiting."
    exit 1
fi

# Ensure the file exists before attempting to upload
if [ ! -e "$filename" ]; then
    echo "File '$filename' does not exist. Exiting."
    exit 1
fi

# Fetch the latest release
latest_release=$(get_latest_release)
if [ -z "$latest_release" ]; then
    echo "Unable to get latest release. Exiting."
    exit 1
fi

# Upload the file to the latest release
echo "Uploading '$filename' to the release: $latest_release"
gh release upload "$latest_release" "$filename" --clobber