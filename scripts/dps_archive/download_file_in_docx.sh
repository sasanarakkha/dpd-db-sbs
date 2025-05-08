#!/bin/bash

# Check for internet connection
if ! ping -c 1 google.com &> /dev/null; then
    echo "\033[0;31mError: No internet connection. Please check your network settings."
    exit 1
fi

# Set the URL of the Google Doc
url="https://docs.google.com/document/d/1uyOA--pUQlHTzs1GWFQHorXkeVkwBEmJdWmPMBWoBXc/export?format=pdf"


# Set the URL of the Google Doc
# url="https://docs.google.com/spreadsheets/d/1kXmflSuk70jAOmn42D0BGSoxhMYuUpo-tmsbSXOz52A/export?format=ods"


# Set the output file name
output_file="downloaded_document.docx"

# Download the file using wget
wget -O "$output_file" "$url"