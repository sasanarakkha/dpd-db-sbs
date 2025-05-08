#!/bin/bash

# all for update of sbs-study-tools (https://sasanarakkha.github.io/study-tools/)

echo -e "\033[1;33m We are going to make various csv and push decks on the server. \033[0m"

cd "$HOME/Documents/dpd-db/"


while true; do
    echo -ne "\033[1;34m need to make latest csv for anki? \033[0m"
    read -n 1 -s yn
    echo
    if [[ $yn == "q" ]]; then
        echo -e "\n\033[1;31m Aborted by user.\033[0m"
        exit 1
    fi
    case $yn in
        [Yy]* )
            uv run python scripts/change_in_db/class_relation.py
            uv run python scripts/export/anki_csv.py
            break;;
        * )
            break;;
    esac
done


# cd "$HOME/Documents/dps/utilities"

while true; do
    echo -ne "\033[1;34m need to push vocab for classes? \033[0m"
    read -n 1 -s yn
    echo
    if [[ $yn == "q" ]]; then
        echo -e "\n\033[1;31m Aborted by user.\033[0m"
        exit 1
    fi
    case $yn in
        [Yy]* )
            echo -e "\033[1;33m pushing vocab for classes...\033[0m"
            uv run python scripts/export/save_classes_vocab_individual.py
            uv run python scripts/export/save_classes_vocab_united.py
            cp -X -rf "$HOME/Documents/sasanarakkha/study-tools/pali-class/vocab/vocab-for-classes.xlsx" "$HOME/filesrv1/share1/Sharing between users/13 For Pāli class/vocab-for-classes.xlsx"
            cd "$HOME/Documents/sasanarakkha/study-tools"
            git-push
            break;;
        * )
            break;;
    esac
done

# grammar.xlsx - https://docs.google.com/spreadsheets/d/1KV5LmebIQpNyNKl03Pmo_Ti-LNW3IYWB6uc7OfGRGPU/

while true; do
    echo -ne "\033[1;34m need to make updated grammar.csv? \033[0m"
    read -n 1 -s yn
    echo
    if [[ $yn == "q" ]]; then
        echo -e "\n\033[1;31m Aborted by user.\033[0m"
        exit 1
    fi
    case $yn in
        [Yy]* )
            echo -e "\033[1;33m generating grammar.csv...\033[0m"
            uv run bash scripts/bash/download_grammar.sh
            uv run python scripts/work_with_csv/anki_class_grammar.py
            break;;
        * )
            break;;
    esac
done


# Pātimokkha.xlsx - https://docs.google.com/spreadsheets/d/1rS-IlX4DvKmnBO58KON37eVnOZqwfkG-ot-zIjCuzH4/

while true; do
    # echo -e "\033[1;36m please download the latest Pātimokkha XLSX! \033[0m"
    echo -ne "\033[1;34m need to generate patimokkha.csv? \033[0m"
    read -n 1 -s yn
    echo
    if [[ $yn == "q" ]]; then
        echo -e "\n\033[1;31m Aborted by user.\033[0m"
        exit 1
    fi
    case $yn in
        [Yy]* )
            echo -e "\033[1;33m generating patimokkha.csv...\033[0m"
            uv run bash scripts/bash/download_patimokkha.sh
            uv run bash scripts/bash/make_pat.sh
            break;;
        * )
            break;;
    esac
done

while true; do
    echo -e "\033[1;36m please save all class anki decks! \033[0m"
    echo -ne "\033[1;34m need to move all classes? \033[0m"
    read -n 1 -s yn
    echo
    if [[ $yn == "q" ]]; then
        echo -e "\n\033[1;31m Aborted by user.\033[0m"
        exit 1
    fi
    case $yn in
        [Yy]* )
            echo -e "\033[1;33m moving all classes...\033[0m"
            uv run bash scripts/bash/move_class.sh
            break;;
        * )
            break;;
    esac
done

while true; do
    echo -ne "\033[1;34m need to create wordtree for all classes? \033[0m"
    read -n 1 -s yn
    echo
    if [[ $yn == "q" ]]; then
        echo -e "\n\033[1;31m Aborted by user.\033[0m"
        exit 1
    fi
    case $yn in
        [Yy]* )
            echo -e "\033[1;33m creating wordtree...\033[0m"
            uv run bash scripts/bash/wordtree.sh
            break;;
        * )
            break;;
    esac
done

while true; do
    echo -e "\033[1;36m please save all other anki decks! \033[0m"
    echo -ne "\033[1;34m need to move all other decks? \033[0m"
    read -n 1 -s yn
    echo
    if [[ $yn == "q" ]]; then
        echo -e "\n\033[1;31m Aborted by user.\033[0m"
        exit 1
    fi
    case $yn in
        [Yy]* )
            echo -e "\033[1;33m moving all other decks...\033[0m"
            uv run bash scripts/bash/move_decks.sh
            break;;
        * )
            break;;
    esac
done

while true; do
    echo -ne "\033[1;34m need to push individually on GitHub and repeat? \033[0m"
    read -n 1 -s answer
    echo
    if [[ $answer == "q" ]]; then
        echo -e "\n\033[1;31m Aborted by user.\033[0m"
        exit 1
    fi
    case $answer in
        [Yy]* )
            echo -e "\033[1;33m Pushing all...\033[0m"
            uv run bash scripts/bash/push_from_temp.sh  
            ;;                      # start over
        * )
            break                    
            ;;
    esac
done


# cd "$HOME/Documents/sasanarakkha/study-tools/temp-push"

# echo -ne "\033[1;34m before pushing all on GitHub need to make zip for all class docs \033[0m"


# while true; do
#     echo -ne "\033[1;34m need to push all on GitHub? \033[0m"
#     read -n 1 -s yn
#     echo
#     if [[ $yn == "q" ]]; then
#         echo -e "\n\033[1;31m Aborted by user.\033[0m"
#         exit 1
#     fi
#     case $yn in
#         [Yy]* )
#             echo -e "\033[1;33m pushing all...\033[0m"
#             bash github-assets-uploader.sh
#             break;;
#         *  )
#             break;;
#     esac
# done


echo -e "\033[1;32m what have to be done has been done! \033[0m"

echo -e "\033[1;32m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ \033[0m"