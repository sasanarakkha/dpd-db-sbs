#!/usr/bin/env bash

# move all class materials on the server and GitHub

cd "$HOME/Downloads"

cp -f "Vocab Pali Class.apkg" "$HOME/Documents/sasanarakkha/study-tools/temp-push/vocab-pali-class.apkg"

mv -X -f "Vocab Pali Class.apkg" "$HOME/filesrv1/share1/Sharing between users/13 For Pāli class/Anki Decks/Vocab Pali Class.apkg"

cp -f "Grammar Pali Class.apkg" "$HOME/Documents/sasanarakkha/study-tools/temp-push/grammar-pali-class.apkg"

mv -X -f "Grammar Pali Class.apkg" "$HOME/filesrv1/share1/Sharing between users/13 For Pāli class/Anki Decks/Grammar Pali Class.apkg"

cp -f "Roots Pali Class.apkg" "$HOME/Documents/sasanarakkha/study-tools/temp-push/roots-pali-class.apkg"

mv -X -f "Roots Pali Class.apkg" "$HOME/filesrv1/share1/Sharing between users/13 For Pāli class/Anki Decks/Roots Pali Class.apkg"

cp -f "Phonetic Changes Pali Class.apkg" "$HOME/Documents/sasanarakkha/study-tools/temp-push/phonetic-pali-class.apkg"

mv -X -f "Phonetic Changes Pali Class.apkg" "$HOME/filesrv1/share1/Sharing between users/13 For Pāli class/Anki Decks/Phonetic Changes Pali Class.apkg"

cp -f "Common Roots Pali Class.apkg" "$HOME/Documents/sasanarakkha/study-tools/temp-push/common-roots-pali-class.apkg"

mv -X -f "Common Roots Pali Class.apkg" "$HOME/filesrv1/share1/Sharing between users/13 For Pāli class/Anki Decks/Common Roots Pali Class.apkg"

cp -f "Suttas Advanced Pali Class.apkg" "$HOME/Documents/sasanarakkha/study-tools/temp-push/suttas-advanced-pali-class.apkg"

mv -X -f "Suttas Advanced Pali Class.apkg" "$HOME/filesrv1/share1/Sharing between users/13 For Pāli class/Anki Decks/Suttas Advanced Pali Class.apkg"

echo "all apkg - done"

cp -X -rf "$HOME/Documents/dpd-db/anki_csvs/pali_class/"* "$HOME/filesrv1/share1/Sharing between users/13 For Pāli class/Anki Decks/csvs/"

cp -rf "$HOME/Documents/dpd-db/anki_csvs/pali_class/class_all.csv" "$HOME/Documents/sasanarakkha/study-tools/temp-push/vocab-pali-class.csv"

cp -rf "$HOME/Documents/dpd-db/anki_csvs/pali_class/class_all.csv" "$HOME/Documents/sasanarakkha/study-tools/temp-push/vocab-pali-class.csv"

cp -rf "$HOME/Documents/dpd-db/anki_csvs/pali_class/phonetic_class.csv" "$HOME/Documents/sasanarakkha/study-tools/temp-push/phonetic-pali-class.csv"

cp -rf "$HOME/Documents/dpd-db/anki_csvs/pali_class/roots_class.csv" "$HOME/Documents/sasanarakkha/study-tools/temp-push/roots-pali-class.csv"

cp -rf "$HOME/Documents/dpd-db/anki_csvs/pali_class/suttas_class.csv" "$HOME/Documents/sasanarakkha/study-tools/temp-push/suttas-advanced-pali-class.csv"

cp -rf "$HOME/Documents/dpd-db/anki_csvs/pali_class/grammar/cl_sum_abbr.csv" "$HOME/Documents/sasanarakkha/study-tools/temp-push/grammar-pali-class-abbr.csv"

cp -rf "$HOME/Documents/dpd-db/anki_csvs/pali_class/grammar/cl_sum_gramm.csv" "$HOME/Documents/sasanarakkha/study-tools/temp-push/grammar-pali-class-gramm.csv"

cp -rf "$HOME/Documents/dpd-db/anki_csvs/pali_class/grammar/cl_sum_sandhi.csv" "$HOME/Documents/sasanarakkha/study-tools/temp-push/grammar-pali-class-sandhi.csv"

# cp -f "$HOME/Documents/dps/csv-for-anki/abbr.xlsx" "$HOME/filesrv1/share1/Sharing between users/13 For Pāli class/Anki Decks/abbreviations.xlsx"

echo "all csv for anki - done"


