#!/bin/bash

# move all decks on the server and GitHub

cd "$HOME/Documents/dpd-db/anki_csvs"

cp -X "anki_patimokkha.csv" "$HOME/filesrv1/share1/Sharing between users/1 For Everyone/Software/Anki (learning tool)/Pātimokkha Word By Word/patimokkha-word-by-word.csv"
mv "anki_patimokkha.csv" "$HOME/Documents/sasanarakkha/study-tools/temp-push/patimokkha-word-by-word.csv"
# cp -X "anki_dps.csv" "$HOME/filesrv1/share1/Sharing between users/1 For Everyone/Software/Anki (learning tool)/Пали Словарь Анки/ru-pali-vocab.csv"
# mv "anki_dps.csv" "$HOME/Documents/sasanarakkha/study-tools/temp-push/ru-pali-vocab.csv" 
cp -X "anki_sbs.csv" "$HOME/filesrv1/share1/Sharing between users/1 For Everyone/Software/Anki (learning tool)/SBS Pāli-English Vocab/sbs-pd.csv"
mv "anki_sbs.csv" "$HOME/Documents/sasanarakkha/study-tools/temp-push/sbs-pd.csv"
# cp -X "anki_dhp.csv" "$HOME/filesrv1/share1/Sharing between users/1 For Everyone/Software/Anki (learning tool)/DHP Vocab/dhp-vocab.csv"
# mv "anki_dhp.csv" "$HOME/Documents/sasanarakkha/study-tools/temp-push/dhp-vocab.csv"
# cp -X "anki_parittas.csv" "$HOME/filesrv1/share1/Sharing between users/1 For Everyone/Software/Anki (learning tool)/Parittas/parittas.csv"
# mv "anki_parittas.csv" "$HOME/Documents/sasanarakkha/study-tools/temp-push/parittas.csv"
cp -X "anki_vibhanga.csv" "$HOME/filesrv1/share1/Sharing between users/1 For Everyone/Software/Anki (learning tool)/Vibhanga/vibhanga.csv"
mv "anki_vibhanga.csv" "$HOME/Documents/sasanarakkha/study-tools/temp-push/vibhanga.csv"

mv "sbs_rus.csv" "$HOME/Documents/sasanarakkha/study-tools/temp-push/sbs-rus.csv"


cd "$HOME/Downloads"

cp -X "Pali Patimokkha Word By Word.apkg" "$HOME/filesrv1/share1/Sharing between users/1 For Everyone/Software/Anki (learning tool)/Pātimokkha Word By Word/patimokkha-word-by-word.apkg"
mv "Pali Patimokkha Word By Word.apkg" "$HOME/Documents/sasanarakkha/study-tools/temp-push/patimokkha-word-by-word.apkg"
# cp -X "Пали Словарь.apkg" "$HOME/filesrv1/share1/Sharing between users/1 For Everyone/Software/Anki (learning tool)/Пали Словарь Анки/ru-pali-vocab.apkg"
# mv "Пали Словарь.apkg" "$HOME/Documents/sasanarakkha/study-tools/temp-push/ru-pali-vocab.apkg"
cp -X "SBS Pali-English Vocab.apkg" "$HOME/filesrv1/share1/Sharing between users/1 For Everyone/Software/Anki (learning tool)/SBS Pāli-English Vocab/sbs-pali-english-vocab.apkg"
mv "SBS Pali-English Vocab.apkg" "$HOME/Documents/sasanarakkha/study-tools/temp-push/sbs-pali-english-vocab.apkg"
# cp -X "Pali DHP vocab.apkg" "$HOME/filesrv1/share1/Sharing between users/1 For Everyone/Software/Anki (learning tool)/DHP vocab/dhp-vocab.apkg"
# mv "Pali DHP vocab.apkg" "$HOME/Documents/sasanarakkha/study-tools/temp-push/dhp-vocab.apkg"
# cp -X "Pali Parittas.apkg" "$HOME/filesrv1/share1/Sharing between users/1 For Everyone/Software/Anki (learning tool)/Parittas/parittas.apkg"
# mv "Pali Parittas.apkg" "$HOME/Documents/sasanarakkha/study-tools/temp-push/parittas.apkg"
# cp -X "Pali Patimokkha Memorizing.apkg" "$HOME/filesrv1/share1/Sharing between users/1 For Everyone/Software/Anki (learning tool)/Pātimokkha Learning/pātimokkha learning.apkg"
# mv "Pali Patimokkha Memorizing.apkg" "$HOME/Documents/sasanarakkha/study-tools/temp-push/patimokkha-learning.apkg"
cp -X "Pali Bhikkhu Vibhanga.apkg" "$HOME/filesrv1/share1/Sharing between users/1 For Everyone/Software/Anki (learning tool)/Vibhanga/vibhanga.apkg"
mv "Pali Bhikkhu Vibhanga.apkg" "$HOME/Documents/sasanarakkha/study-tools/temp-push/vibhanga.apkg"


# cp -X "Ñāṇatiloka Dictionary.apkg" "$HOME/filesrv1/share1/Sharing between users/1 For Everyone/Software/Anki (learning tool)/Ñāṇatiloka Dictionary/nanatiloka-dictionary.apkg"
# mv "Ñāṇatiloka Dictionary.apkg" "$HOME/Documents/sasanarakkha/study-tools/temp-push/nanatiloka-dictionary.apkg"
# cp -X "Sutta Q&A.apkg" "$HOME/filesrv1/share1/Sharing between users/1 For Everyone/Software/Anki (learning tool)/Sutta Q&A/sutta-q-a.apkg"
# mv "Sutta Q&A.apkg" "$HOME/Documents/sasanarakkha/study-tools/temp-push/sutta-q-a.apkg"

# cp -X "$HOME/filesrv1/share1/Sharing between users/1 For Everyone/Software/Anki (learning tool)/Reading common pali phrases/reading-common-pali-phrases.apkg" "$HOME/Documents/sasanarakkha/study-tools/temp-push/reading-common-pali-phrases.apkg"

# cp -X "$HOME/filesrv1/share1/Sharing between users/1 For Everyone/Software/Anki (learning tool)/Reading common pali phrases/reading-common-pali-phrases.csv" "$HOME/Documents/sasanarakkha/study-tools/temp-push/reading-common-pali-phrases.csv"

echo "Anki decks and csv of SBS-PED ; PAT ; DHP ; DPS ; Pāli Parittas moved for share"
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"

echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo "the job is done"
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"


