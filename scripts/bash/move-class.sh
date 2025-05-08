#!/usr/bin/env bash

# move all class materials on the server and GitHub

cd "~/Documents/dps/utilities"

# bash push-sbs-pd.sh

# bash push-ru.sh

cd "~/Downloads"

cp -f "Vocab Pali Class.apkg" "~/Documents/sasanarakkha/study-tools/temp-push/vocab-pali-class.apkg"

mv -f "Vocab Pali Class.apkg" "~/filesrv1/share1/Sharing between users/13 For Pāli class/Anki Decks/Vocab Pali Class.apkg"

cp -f "Grammar Pali Class.apkg" "~/Documents/sasanarakkha/study-tools/temp-push/grammar-pali-class.apkg"

mv -f "Grammar Pali Class.apkg" "~/filesrv1/share1/Sharing between users/13 For Pāli class/Anki Decks/Grammar Pali Class.apkg"

cp -f "Roots Pali Class.apkg" "~/Documents/sasanarakkha/study-tools/temp-push/roots-pali-class.apkg"

mv -f "Roots Pali Class.apkg" "~/filesrv1/share1/Sharing between users/13 For Pāli class/Anki Decks/Roots Pali Class.apkg"

cp -f "Phonetic Changes Pali Class.apkg" "~/Documents/sasanarakkha/study-tools/temp-push/phonetic-pali-class.apkg"

mv -f "Phonetic Changes Pali Class.apkg" "~/filesrv1/share1/Sharing between users/13 For Pāli class/Anki Decks/Phonetic Changes Pali Class.apkg"

cp -f "Common Roots Pali Class.apkg" "~/Documents/sasanarakkha/study-tools/temp-push/common-roots-pali-class.apkg"

mv -f "Common Roots Pali Class.apkg" "~/filesrv1/share1/Sharing between users/13 For Pāli class/Anki Decks/Common Roots Pali Class.apkg"

cp -f "Suttas Advanced Pali Class.apkg" "~/Documents/sasanarakkha/study-tools/temp-push/suttas-advanced-pali-class.apkg"

mv -f "Suttas Advanced Pali Class.apkg" "~/filesrv1/share1/Sharing between users/13 For Pāli class/Anki Decks/Suttas Advanced Pali Class.apkg"

echo "all apkg - done"

cp -rf "~/Documents/dpd-db/dps/csvs/anki_csvs/pali_class/"* "~/filesrv1/share1/Sharing between users/13 For Pāli class/Anki Decks/csvs/"

cp -rf "~/Documents/dpd-db/dps/csvs/anki_csvs/pali_class/class_all.csv" "~/Documents/sasanarakkha/study-tools/temp-push/vocab-pali-class.csv"

cp -rf "~/Documents/dpd-db/dps/csvs/anki_csvs/pali_class/class_all.csv" "~/Documents/sasanarakkha/study-tools/temp-push/vocab-pali-class.csv"

cp -rf "~/Documents/dpd-db/dps/csvs/anki_csvs/pali_class/phonetic_class.csv" "~/Documents/sasanarakkha/study-tools/temp-push/phonetic-pali-class.csv"

cp -rf "~/Documents/dpd-db/dps/csvs/anki_csvs/pali_class/roots_class.csv" "~/Documents/sasanarakkha/study-tools/temp-push/roots-pali-class.csv"

cp -rf "~/Documents/dpd-db/dps/csvs/anki_csvs/pali_class/suttas_class.csv" "~/Documents/sasanarakkha/study-tools/temp-push/suttas-advanced-pali-class.csv"

cp -rf "~/Documents/dpd-db/dps/csvs/anki_csvs/pali_class/grammar/cl_sum_abbr.csv" "~/Documents/sasanarakkha/study-tools/temp-push/grammar-pali-class-abbr.csv"

cp -rf "~/Documents/dpd-db/dps/csvs/anki_csvs/pali_class/grammar/cl_sum_gramm.csv" "~/Documents/sasanarakkha/study-tools/temp-push/grammar-pali-class-gramm.csv"

cp -rf "~/Documents/dpd-db/dps/csvs/anki_csvs/pali_class/grammar/cl_sum_sandhi.csv" "~/Documents/sasanarakkha/study-tools/temp-push/grammar-pali-class-sandhi.csv"

# cp -f "~/Documents/dps/csv-for-anki/abbr.xlsx" "~/filesrv1/share1/Sharing between users/13 For Pāli class/Anki Decks/abbreviations.xlsx"

echo "all csv for anki - done"

# cp -f "~/Documents/dps/test.md" "~/Documents/sasanarakkha/study-tools/pali-class/class-test.md"

# echo "making wordtree"

# cd "~/Documents/dps/word-frequency/"

# bash wordtree-for-all-class.sh

# echo "wordtree cleaning"

# cd "~/filesrv1/share1/Sharing between users/13 For Pāli class/wordtree"

# find . -wholename './class1/*' | xargs rm -rf
# find . -wholename './class2/*' | xargs rm -rf
# find . -wholename './class3/*' | xargs rm -rf
# find . -wholename './class4/*' | xargs rm -rf
# find . -wholename './class5/*' | xargs rm -rf
# find . -wholename './class6/*' | xargs rm -rf
# find . -wholename './class7/*' | xargs rm -rf
# find . -wholename './class8/*' | xargs rm -rf
# find . -wholename './class9/*' | xargs rm -rf
# find . -wholename './class10/*' | xargs rm -rf
# find . -wholename './class11/*' | xargs rm -rf
# find . -wholename './class12/*' | xargs rm -rf
# find . -wholename './class13/*' | xargs rm -rf
# find . -wholename './class14/*' | xargs rm -rf

# cd "~/Documents/sasanarakkha/study-tools/pali-class/wordtree"

# find . -wholename './class1/*' | xargs rm -rf
# find . -wholename './class2/*' | xargs rm -rf
# find . -wholename './class3/*' | xargs rm -rf
# find . -wholename './class4/*' | xargs rm -rf
# find . -wholename './class5/*' | xargs rm -rf
# find . -wholename './class6/*' | xargs rm -rf
# find . -wholename './class7/*' | xargs rm -rf
# find . -wholename './class8/*' | xargs rm -rf
# find . -wholename './class9/*' | xargs rm -rf
# find . -wholename './class10/*' | xargs rm -rf
# find . -wholename './class11/*' | xargs rm -rf
# find . -wholename './class12/*' | xargs rm -rf
# find . -wholename './class13/*' | xargs rm -rf
# find . -wholename './class14/*' | xargs rm -rf


# cp -rf "~/Documents/dps/word-frequency/pics-wordtree/wordtree" "~/filesrv1/share1/Sharing between users/13 For Pāli class/"

# cp -rf "~/Documents/dps/word-frequency/pics-wordtree/wordtree" "~/Documents/sasanarakkha/study-tools/pali-class/"


# echo "all pics-wordtree - done"

echo "all done - new class updated"


