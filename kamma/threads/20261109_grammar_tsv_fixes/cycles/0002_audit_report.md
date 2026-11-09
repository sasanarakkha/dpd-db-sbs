# Cycle 0002 — audit findings (report only, no TSV edited)

Cells proposed: 279 across 262 rows. Clear (conf 9-10): 130; probable (7-8): 145; uncertain (≤6): 4.

`⏎` marks `<br>`. `line` = physical file line (header = line 1). Confidence 1-10.


## a_masc.tsv (7 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 16 | 3306 | dhammānaṃ | dat pl ⏎ gen pl | native | для обучения ⏎ обучения | для учений ⏎ учений | number | 8 | pl shown as sg (обучения) |
| 20 | 320 | khayāya | dat sg | native | истощение | для истощения | case | 9 | dat sg without 'для' |
| 21 | 323 | nirodhāya | dat sg | native | прекращение | для прекращения | case | 9 | dat sg without 'для' |
| 41 | 306 | dhammā | nom pl ⏎ abl sg ⏎ voc sg & pl | native | преподавание ⏎ от преподавания ⏎ к преподаванию(ям)! | преподавание ⏎ от преподавания ⏎ о преподавание(я)! | case | 7 | voc rendered 'к' (dative) |
| 42 | 307 | kāyā | nom pl ⏎ abl sg ⏎ voc sg & pl | native | тела ⏎ из тела ⏎ в тело(а)! | тела ⏎ из тела ⏎ о тело(а)! | case | 8 | voc rendered 'в' (acc) |
| 43 | 308 | lokā | nom pl ⏎ abl sg ⏎ voc sg & pl | native | миры ⏎ из мира ⏎ в мир(ы)! | миры ⏎ из мира ⏎ о мир(ы)! | case | 8 | voc rendered 'в' (acc) |
| 51 | 350 | purisa | voc sg | native | О, боже! | О мужчина! | meaning | 10 | 'О, боже!' = 'oh God' |

## pr.tsv (3 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 28 | 426 | viharāmi | pr 1st sg ⏎ imp 1st sg | native | Я (должен) остановиться | Я (должен) жить | meaning | 7 | 'остановиться' = stop; viharati = dwell (pr:39 'живут') |
| 46 | 44904 | vipācenti | pr 3rd pl | native | они распространились | они распространяют | tense | 7 | pr rendered past |
| 59 | 457 | dhāretha | pr 2nd pl ⏎ imp 2nd pl | native | вы все (должны) подождать | вы все (должны) поднять | meaning | 8 | 'подождать' = wait; dhāreti = hold up (pr:7 'поднимает') |

## pr_aor_be.tsv (4 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 17 | 5055 | attha | pr 2nd pl ⏎ imp 2nd pl | native | вы все такие ⏎ вы все должны быть | вы все есть ⏎ вы все должны быть | meaning | 8 | 'вы все такие' = 'you all are such' |
| 18 | 556 | asi | pr 2nd sg | native | ты | ты есть | meaning | 8 | verb missing: 'ты' = 'you' |
| 24 | 522 | hotha | pr 2nd pl ⏎ imp 2nd pl | native | вы все такие ⏎ вы все должны быть | вы все есть ⏎ вы все должны быть | meaning | 8 | same as :17 |
| 25 | 523 | hosi | pr 2nd sg | native | ты | ты есть | meaning | 8 | same as :18 |

## aor.tsv (6 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 4 | 602 | abbhaññāsi | aor 3rd sg ⏎ aor 2nd sg | native | он знал напрямую, ⏎ ты знал напрямую | он знал напрямую ⏎ ты знал напрямую | typo | 8 | stray comma before  ⏎  |
| 13 | 666 | āmantesi | aor 3rd sg ⏎ aor 2nd sg | native | он обратился к вам, обратившись к вам. | он обратился ⏎ ты обратился | part count/number | 10 | two parts merged into one string; 'к вам' = to you pl |
| 22 | 620 | paccassosi | aor 3rd sg ⏎ aor 2nd sg | native | он согласился ⏎ вы согласились | он согласился ⏎ ты согласился | number | 7 | 2nd sg shown as 'вы' |
| 31 | 629 | sammodi | aor 3rd sg ⏎ aor 2nd sg | native | он поприветствовал ⏎ вы поприветствовали | он поприветствовал ⏎ ты поприветствовал | number | 7 | 2nd sg shown as 'вы' |
| 40 | 638 | vihāsuṃ | aor 3rd pl | eng | they removed | they lived | meaning | 8 | vihāsuṃ ← vihāsi 'lived' (DPD); not 'removed' |
| 40 | 638 | vihāsuṃ | aor 3rd pl | native | они удалили | они жили | meaning | 8 | 'удалили' = removed |

## i_masc.tsv (4 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 6 | 704 | aggī | nom pl ⏎ acc pl ⏎ voc pl | native | огонь ⏎ о огонь! | огни ⏎ о огни! | number | 10 | pl shown as sg |
| 31 | 729 | pāṇīhi | instr pl ⏎ abl pl | native | с пальмами ⏎ из пальм | с ладонями ⏎ из ладоней | meaning | 9 | 'пальмами' = palm trees; pāṇi = palm of hand |
| 33 | 737 | samādhissa | dat sg ⏎ gen sg | native | для душевного спокойствия ⏎ для душевного спокойствия | для душевного спокойствия ⏎ душевного спокойствия | case | 9 | gen sg given as dat |
| 38 | 736 | upadhīhi | instr pl ⏎ abl pl | native | с идентификацией ⏎ из идентификации | с идентификациями ⏎ из идентификаций | number | 7 | pl shown as sg |

## ii_masc.tsv (7 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 17 | 886 | hatthismiṃ | loc sg | native | слон | в слоне | case | 10 | loc sg shown as nominative |
| 18 | 887 | cakkavattini | loc sg | native | император | в императоре | case | 10 | loc sg shown as nominative |
| 21 | 820 | bhogino | nom pl ⏎ acc pl ⏎ dat sg ⏎ gen sg ⏎ voc pl | native | богатые люди ⏎ для богатого человека ⏎ из богатого человека ⏎ о богатые люди! | богатые люди ⏎ для богатого человека ⏎ богатого человека ⏎ о богатые люди! | case | 9 | gen sg shown with 'из' (abl) |
| 22 | 828 | brahmacārino | nom pl ⏎ acc pl ⏎ dat sg ⏎ gen sg ⏎ voc pl | eng | celibate men ⏎ for celibate men ⏎ of celibate men ⏎ o celibate men! | celibate men ⏎ for celibate man ⏎ of celibate man ⏎ o celibate men! | number | 8 | dat/gen sg shown pl |
| 22 | 828 | brahmacārino | nom pl ⏎ acc pl ⏎ dat sg ⏎ gen sg ⏎ voc pl | native | безбрачные мужчины ⏎ для безбрачных мужчин ⏎ безбрачных мужчин ⏎ о безбрачных мужчин! | безбрачные мужчины ⏎ для безбрачного мужчины ⏎ безбрачного мужчины ⏎ о безбрачные мужчины! | number | 8 | dat/gen sg shown pl (voc pl row currently 'о безбрачных мужчин!' gen) |
| 23 | 822 | tapassino | nom pl ⏎ acc pl ⏎ dat sg ⏎ gen sg ⏎ voc pl | eng | ascetics ⏎ for ascetics ⏎ of ascetics ⏎ o ascetics! | ascetics ⏎ for ascetic ⏎ of ascetic ⏎ o ascetics! | number | 8 | dat/gen sg shown pl |
| 23 | 822 | tapassino | nom pl ⏎ acc pl ⏎ dat sg ⏎ gen sg ⏎ voc pl | native | аскеты ⏎ для аскетов ⏎ из аскетов ⏎ о аскеты! | аскеты ⏎ для аскета ⏎ аскета ⏎ о аскеты! | number | 8 | dat/gen sg shown pl, gen with 'из' |

## pers_pron.tsv (12 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 4 | 902 | maṃ | 1st acc sg | native | мне | меня | case | 10 | 'мне' is dative; acc = меня |
| 6 | 904 | me | 1st acc & instr & dat & gen sg | native | я ⏎ со мной ⏎ для меня ⏎ мой | меня ⏎ со мной ⏎ для меня ⏎ мой | case | 10 | acc shown as nominative 'я' |
| 11 | 909 | mayā | 1st instr & abl sg | eng | with me ⏎ for me | with me ⏎ from me | case | 9 | abl rendered 'for me' |
| 11 | 909 | mayā | 1st instr & abl sg | native | со мной ⏎ для меня | со мной ⏎ от меня | case | 9 | abl rendered 'для меня' |
| 15 | 993 | amhe | 1st nom & acc pl | native | мы ⏎ мы | мы ⏎ нас | case | 10 | acc pl shown 'мы' |
| 17 | 995 | tumhākaṃ | 2nd acc & dat & gen pl | native | всем вам ⏎ для всех вас ⏎ ваши | всех вас ⏎ для всех вас ⏎ ваши | case | 9 | acc shown dat 'всем вам' |
| 18 | 996 | vo | 2nd acc & instr & dat & gen pl | native | вы все ⏎ с вами всеми ⏎ для вас всех ⏎ ваш | вас всех ⏎ с вами всеми ⏎ для вас всех ⏎ ваш | case | 9 | acc shown nominative 'вы все' |
| 19 | 997 | taṃ 2 | 2nd acc sg | native | ты | тебя | case | 9 | acc shown nominative |
| 20 | 998 | tavaṃ | 2nd acc sg | native | ты | тебя | case | 9 | acc shown nominative |
| 21 | 999 | te | 2nd acc & instr & dat & gen sg | native | ты ⏎ с тобой ⏎ для тебя ⏎ твой | тебя ⏎ с тобой ⏎ для тебя ⏎ твой | case | 9 | acc shown nominative 'ты' |
| 23 | 929 | tuyhaṃ | 2nd dat & gen sg | native | для вас ⏎ ваш | для тебя ⏎ твой | number | 7 | 2nd sg shown plural/polite 'вас' |
| 24 | 922 | tava | 2nd dat & gen sg | native | для вас ⏎ ваш | для тебя ⏎ твой | number | 7 | 2nd sg shown plural/polite 'вас' |

## fut.tsv (2 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 21 | 10109 | upādiyissāmi | fut 1st sg | native | Я пойму | Я схвачу | meaning | 6 | 'Я пойму' = I will understand; upādiyati = grasp |
| 22 | 1020 | viharissāma | fut 1st pl | native | мы будем останавливаться | мы будем жить | meaning | 7 | 'останавливаться' = stop; viharati = dwell |

## u_masc.tsv (6 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 5 | 1103 | bhikkhuno | dat sg ⏎ gen sg | native | для монаха ⏎ из монаха | для монаха ⏎ монаха | case | 9 | gen sg shown with 'из' |
| 6 | 1104 | bhikkhussa | dat sg ⏎ gen sg | native | для монаха ⏎ из монаха | для монаха ⏎ монаха | case | 9 | gen sg shown with 'из' |
| 20 | 11118 | hetumhi | loc sg | native | в разумных пределах | в причине | meaning | 8 | 'в разумных пределах' = within reasonable limits; hetu = reason |
| 23 | 11211 | kurūnaṃ | dat pl ⏎ gen pl | native | для Куруса ⏎ из Куруса (название страны) | для Куру ⏎ Куру (название страны) | case/number | 9 | 'Куруса' not a form; gen shown with 'из' |
| 25 | 1123 | maccuno | dat sg ⏎ gen sg | native | смерть ⏎ смерти | для смерти ⏎ смерти | case | 9 | dat sg without 'для' |
| 26 | 1124 | maccussa | dat sg ⏎ gen sg | native | смерть ⏎ смерти | для смерти ⏎ смерти | case | 9 | dat sg without 'для' |

## ar_masc.tsv (6 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 3 | 12012 | aññātāro | nom pl ⏎ acc pl ⏎ voc pl | eng | those who understands ⏎ o those who understands! | those who understand ⏎ o those who understand! | number | 7 | 'those who understands' |
| 3 | 12012 | aññātāro | nom pl ⏎ acc pl ⏎ voc pl | native | те, кто понимает ⏎ к тем, кто понимает! | те, кто понимает ⏎ о те, кто понимает! | case | 8 | voc shown with 'к' (dat) |
| 9 | 1207 | brūhetānaṃ | dat pl ⏎ gen pl | eng | for those who develops ⏎ of those who develops | for those who develop ⏎ of those who develop | number | 7 | 'those who develops' |
| 9 | 1207 | brūhetānaṃ | dat pl ⏎ gen pl | native | для тех, кто развивается ⏎ из тех, кто развивается | для тех, кто развивается ⏎ тех, кто развивается | case | 9 | gen pl shown with 'из' |
| 22 | 1220 | satthari | loc sg | native | в учитель | в учителе | case | 10 | loc sg 'в учитель' |
| 23 | 12212 | vattāro | nom pl ⏎ acc pl ⏎ voc pl | native | динамики ⏎ o динамики! | ораторы ⏎ о ораторы! | meaning | 9 | 'динамики' = loudspeakers; also Latin 'o' |

## ar2_masc.tsv (2 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 4 | 1302 | bhātūnaṃ | dat pl ⏎ gen pl | native | для братьев братьев | для братьев ⏎ братьев | part count | 10 | two parts merged: 'для братьев братьев' |
| 11 | 1309 | bhātari | loc sg | native | брат | в брате | case | 10 | loc sg shown nominative |

## uu_masc.tsv (7 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 3 | 14014 | abhibhuṃ | acc sg | native | Виктор | победитель | meaning | 10 | 'Виктор' = the name Victor |
| 5 | 1403 | abhibhusmiṃ | loc sg | native | победителем | в победителе | case | 10 | loc sg shown instrumental |
| 8 | 1406 | sabbaññuno | nom pl ⏎ acc pl ⏎ dat sg ⏎ gen sg ⏎ voc pl | native | всеведущие ⏎ для всеведущего ⏎ из всеведущего ⏎ о всеведущие! | всеведущие ⏎ для всеведущего ⏎ всеведущего ⏎ о всеведущие! | case | 9 | gen sg shown with 'из' |
| 9 | 1407 | vedaguno | nom pl ⏎ acc pl ⏎ dat sg ⏎ gen sg ⏎ voc pl | native | те, кто обладает совершенным знанием ⏎ для того, кто обладает совершенным знанием ⏎ о том, кто обладает совершенным знанием ⏎ для тех, кто обладает совершенным знанием! | те, кто обладает совершенным знанием ⏎ для того, кто обладает совершенным знанием ⏎ того, кто обладает совершенным знанием ⏎ о те, кто обладает совершенным знанием! | case | 8 | gen sg shown 'о том'; voc pl shown 'для тех' (dat) |
| 13 | 141414 | vidū | nom sg & pl ⏎ acc pl ⏎ voc sg & pl | native | провидцы ⏎ провидцы ⏎ о провидец(ы)! | провидец ⏎ провидцы ⏎ о провидец(ы)! | number | 8 | 'nom sg & pl' first part shown pl |
| 20 | 14148 | viññussa | gen sg | native | мудрецов | мудреца | number | 10 | gen sg shown gen pl 'мудрецов' |
| 21 | 14149 | viññūsu | loc pl | eng | amongst sage | amongst sages | number | 10 | loc pl shown 'sage' |

## ant.tsv (10 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 7 | 1505 | bhagavantānaṃ | dat pl ⏎ gen pl | native | для благословенных ⏎ из благословенных | для благословенных ⏎ благословенных | case | 9 | gen pl shown with 'из' |
| 8 | 1506 | sabbāvataṃ | dat pl ⏎ gen pl | native | для тех, у кого есть всё ⏎ для тех, у кого есть всё | для тех, у кого есть всё ⏎ тех, у кого есть всё | case | 9 | gen shown as dat (duplicate) |
| 10 | 1508 | vusitavataṃ | dat pl ⏎ gen pl | native | для тех, кто жил (святой жизнью) ⏎ из тех, кто жил (святой жизнью) | для тех, кто жил (святой жизнью) ⏎ тех, кто жил (святой жизнью) | case | 9 | gen pl shown with 'из' |
| 13 | 151515 | paññavantassa | dat sg ⏎ gen sg | native | мудрый ⏎ из мудрых | для мудрого ⏎ мудрого | case/number | 9 | dat sg shown nom; gen sg shown pl with 'из' |
| 14 | 15152 | sīlavato | dat sg ⏎ gen sg | native | добродетельный ⏎ из добродетельных | для добродетельного ⏎ добродетельного | case/number | 9 | dat sg shown nom; gen sg shown pl with 'из' |
| 15 | 15153 | sīlavantassa | dat sg ⏎ gen sg | native | добродетельный ⏎ из добродетельных | для добродетельного ⏎ добродетельного | case/number | 9 | dat sg shown nom; gen sg shown pl with 'из' |
| 31 | 1529 | āyasmanto | nom sg & pl ⏎ voc pl | native | почтенные ⏎ почтенные ⏎ о почтенные! | почтенный ⏎ почтенные ⏎ о почтенные! | number | 8 | 'nom sg & pl' sg part missing/shown pl |
| 34 | 1532 | bhagavā | nom sg ⏎ voc sg | native | Благословенный! О, Благословенный! | Благословенный ⏎ О Благословенный! | part count | 10 | two parts merged: 'Благословенный! О, Благословенный!' |
| 35 | 1533 | satimā | nom sg ⏎ voc sg | native | Внимательный человек ⏎ Внимательный человек! | Внимательный человек ⏎ о внимательный человек! | case | 7 | voc without 'о' |
| 38 | 1536 | pāpima | voc sg | native | О, злой дух! | О злой! | meaning | 5 | 'злой дух' = evil spirit; eng 'evil one' |

## adv_place.tsv (3 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 13 | 171717 | purato | ind, adv of place ⏎ abl sg | native | перед) | (перед) | typo | 9 | stray ')' without '(' |
| 17 | 17175 | samantato | ind, adv of place ⏎ abl sg | native | со всех сторон; повсюду; освещено со всех сторон. | вокруг; со всех сторон; повсюду; букв. со всех сторон | meaning | 8 | 'освещено со всех сторон' = illuminated; no such meaning |
| 20 | 17178 | parito | ind, adv of place ⏎ abl sg | native | повсюду; везде; освещено со всех сторон. | вокруг; повсюду; букв. со всех сторон | meaning | 8 | 'освещено со всех сторон' = illuminated; no such meaning |

## ger.tsv (1 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 3 | 18018 | paṭicca | ger | native | в зависимости от) | в зависимости (от) | typo | 9 | stray ')' without '(' |

## adv.tsv (2 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 3 | 21021 | tathā | ind, adv | native | так; таким образом; подобным образом; аналогично; аналогично | так; таким образом; подобным образом; также; аналогично | typo | 6 | 'аналогично' twice for 'likewise; similarly' |
| 27 | 2124 | accayena | ind, adv ⏎ instr sg | native | после смерти (чего-либо); после прекращения (чего-либо); букв. со словом «с смертью» | после смерти (чего-либо); после прекращения (чего-либо); букв. с прохождением | meaning | 9 | garbled 'со словом «с смертью»' |

## aa_fem.tsv (8 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 3 | 23023 | avijjā | nom sg & pl ⏎ acc pl ⏎ voc pl | native | невежество ⏎ невежества ⏎ о невежество! | невежество ⏎ невежества ⏎ о невежества! | number | 8 | voc pl shown sg |
| 4 | 2302 | avijjāya | instr sg ⏎ dat sg ⏎ abl sg ⏎ gen sg ⏎ loc sg | native | с невежеством ⏎ из невежества ⏎ из невежества ⏎ невежества ⏎ в невежестве | с невежеством ⏎ для невежества ⏎ из невежества ⏎ невежества ⏎ в невежестве | case | 9 | dat sg shown with 'из' |
| 8 | 2306 | devatā | nom sg & pl ⏎ acc pl ⏎ voc pl | native | божества ⏎ божества ⏎ о божества! | божество ⏎ божества ⏎ о божества! | number | 8 | 'nom sg & pl' sg part shown pl |
| 21 | 23239 | vedanā | nom sg & pl ⏎ acc pl ⏎ voc pl | native | чувства ⏎ чувства ⏎ о чувства! | чувство ⏎ чувства ⏎ о чувства! | number | 8 | 'nom sg & pl' sg part shown pl |
| 24 | 2322 | vedanāhi | instr pl ⏎ abl pl | eng | with feeling ⏎ from feeling | with feelings ⏎ from feelings | number | 10 | instr/abl pl shown sg |
| 24 | 2322 | vedanāhi | instr pl ⏎ abl pl | native | с чувством ⏎ из чувства | с чувствами ⏎ из чувств | number | 10 | instr/abl pl shown sg |
| 25 | 2323 | vedanānaṃ | dat pl ⏎ gen pl | native | чувства ⏎ чувства | для чувств ⏎ чувств | case/number | 9 | dat/gen pl shown as 'чувства' |
| 27 | 2325 | velāyaṃ | loc sg | native | со временем | во времени | case | 8 | loc sg 'со временем' = with time |

## opt.tsv (4 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 9 | 2406 | dhāreyyātha | opt 2nd pl | native | вы все могли бы подождать | вы все могли бы поднять | meaning | 8 | 'подождать' = wait; dhāreti = hold up |
| 12 | 2409 | bhāvetha | opt 2nd pl ⏎ pr 2nd pl ⏎ imp 2nd pl | native | вы все можете заниматься земледелием ⏎ вы все должны заниматься земледелием | вы все могли бы культивировать ⏎ вы все культивируете ⏎ вы все должны культивировать | meaning/part count | 8 | 'земледелием' = farming; 'pr 2nd pl' part missing |
| 16 | 24243 | bhuñje | opt 3rd & 2nd & 1st sg | native | мы с ним могли бы поесть | он, ты и я могли бы поесть | meaning | 9 | 'мы с ним' = he and I (drops 'you') |
| 24 | 24224 | vihareyya | opt 3rd sg | native | он мог бы остановиться | он мог бы жить | meaning | 7 | 'остановиться' = stop; viharati = dwell |

## i_fem.tsv (9 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 7 | 2605 | bhikkhunī | nom sg & pl ⏎ acc pl ⏎ voc sg & pl | native | монахини ⏎ монахини ⏎ о монахиня(и)! | монахиня ⏎ монахини ⏎ о монахиня(и)! | number | 8 | 'nom sg & pl' sg part shown pl |
| 8 | 2606 | duggati | nom sg ⏎ voc sg | native | привет ⏎ привет, ад! | ад ⏎ о ад! | meaning | 10 | 'привет' = hello; hell≠hello |
| 9 | 2607 | duggatī | nom pl ⏎ acc pl ⏎ voc pl | native | ад ⏎ о ад! | ады ⏎ о ады! | number | 8 | pl shown sg |
| 11 | 2609 | duggatiyo | nom pl ⏎ acc pl ⏎ voc pl | native | ад ⏎ о ад! | ады ⏎ о ады! | number | 8 | pl shown sg |
| 12 | 26260 | duggatiyā | instr sg ⏎ dat sg ⏎ abl sg ⏎ gen sg ⏎ loc sg | native | с адом ⏎ за ад ⏎ из ада ⏎ из ада ⏎ в аду | с адом ⏎ для ада ⏎ из ада ⏎ ада ⏎ в аду | case | 9 | dat shown 'за ад' (acc), gen shown 'из ада' |
| 13 | 262626 | duggatīhi | instr pl ⏎ abl pl | native | с адом ⏎ из ада | с адами ⏎ из адов | number | 8 | pl shown sg |
| 17 | 26265 | parihānīnaṃ | dat pl ⏎ gen pl | native | для ухудшения ⏎ ухудшения | для ухудшений ⏎ ухудшений | number | 8 | pl shown sg |
| 25 | 2623 | vuddhīnaṃ | dat pl ⏎ gen pl | native | для роста ⏎ ростов | для ростов ⏎ ростов | number | 7 | dat pl shown sg 'для роста' |
| 26 | 2624 | vuṭṭhī | nom pl ⏎ acc pl ⏎ voc pl | native | осадки ⏎ осадки! | осадки ⏎ о осадки! | case | 8 | voc without 'о' |

## u_fem.tsv (1 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 11 | 2709 | rajjuyā | instr sg ⏎ dat sg ⏎ abl sg ⏎ gen sg ⏎ loc sg | native | с веревкой ⏎ для веревки ⏎ из веревки ⏎ из веревки ⏎ в веревке | с веревкой ⏎ для веревки ⏎ из веревки ⏎ веревки ⏎ в веревке | case | 9 | gen sg shown 'из веревки' |

## ar_fem.tsv (2 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 8 | 2806 | mātaro | nom pl ⏎ acc pl ⏎ voc pl | native | матерям ⏎ о матерям! | матери ⏎ о матери! | number/case | 10 | nom/acc pl shown dative pl 'матерям' |
| 11 | 2809 | dhītaro | nom pl ⏎ acc pl ⏎ voc pl | native | дочерей ⏎ о дочерей! | дочери ⏎ о дочери! | number/case | 9 | nom/acc pl shown gen pl 'дочерей' |

## a_nt.tsv (11 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 5 | 2903 | āsane | acc pl ⏎ loc sg | eng | chairs ⏎ in chair! | chairs ⏎ in chair | typo | 8 | stray '!' |
| 5 | 2903 | āsane | acc pl ⏎ loc sg | native | стулья ⏎ в стуле! | стулья ⏎ в стуле | typo | 8 | stray '!' |
| 13 | 292929 | cittamhi | loc sg | native | с учетом | в уме | meaning | 9 | 'с учетом' = taking into account |
| 14 | 29292 | cittasmiṃ | loc sg | native | с учетом | в уме | meaning | 9 | 'с учетом' = taking into account |
| 16 | 29294 | maraṇā | nom pl ⏎ abl sg ⏎ voc sg | native | смерти ⏎ от смерти ⏎ до смерти! | смерти ⏎ от смерти ⏎ о смерть! | case | 9 | voc shown 'до смерти' (until) |
| 18 | 29296 | maraṇāya | dat sg | native | смерть | для смерти | case | 9 | dat sg without 'для' |
| 19 | 29297 | maraṇassa | dat sg ⏎ gen sg | native | смерть ⏎ смерти | для смерти ⏎ смерти | case | 9 | dat sg without 'для' |
| 32 | 2930 | sīlānaṃ | dat pl ⏎ gen pl | native | за добродетели ⏎ добродетелей | для добродетелей ⏎ добродетелей | case | 8 | dat pl 'за добродетели' = acc |
| 33 | 29329 | ṭhānehi | instr pl ⏎ abl pl | eng | with place ⏎ from place | with places ⏎ from places | number | 10 | instr/abl pl shown sg |
| 33 | 29329 | ṭhānehi | instr pl ⏎ abl pl | native | с местом ⏎ из места | с местами ⏎ из мест | number | 10 | instr/abl pl shown sg |
| 36 | 2934 | viññāṇe | acc pl ⏎ loc sg | native | сознание ⏎ в сознании | сознания ⏎ в сознании | number | 8 | acc pl shown sg |

## i_nt.tsv (6 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 9 | 3007 | aṭṭhīnaṃ | dat pl ⏎ gen pl | native | кости ⏎ костей | для костей ⏎ костей | case | 9 | dat pl without 'для' |
| 14 | 30302 | dadhi | nom sg ⏎ voc sg | native | творог! | творог ⏎ о творог! | part count | 10 | nom part missing |
| 17 | 30305 | sappissa | dat sg ⏎ gen sg | native | для топленого масла ⏎ из топленого масла | для топленого масла ⏎ топленого масла | case | 9 | gen sg shown with 'из' |
| 19 | 30307 | sappī | nom pl ⏎ acc pl ⏎ voc pl | native | геес ⏎ о геес! | топленые масла ⏎ о топленые масла! | meaning | 8 | 'геес' is garbled English 'ghees' |
| 20 | 30308 | sappi | nom sg ⏎ voc sg | eng | ghree ⏎ o ghee! | ghee ⏎ o ghee! | typo | 10 | 'ghree' |
| 20 | 30308 | sappi | nom sg ⏎ voc sg | native | ghree ⏎ o ghee! | топленое масло ⏎ о топленое масло! | meaning | 10 | native left untranslated English |

## u_nt.tsv (11 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 3 | 31031 | vatthusmā | abl sg | native | с сайта | с участка | meaning | 8 | 'сайт' = website; vatthu = site/plot |
| 4 | 3102 | dārūnaṃ | dat pl ⏎ gen pl | native | для древесины ⏎ из древесины | для древесины ⏎ древесины | case | 9 | gen pl shown with 'из' |
| 9 | 3107 | vatthussa | dat sg ⏎ gen sg | native | для сайта ⏎ сайта | для участка ⏎ участка | meaning | 8 | 'сайт' = website |
| 11 | 3109 | vatthūhi | instr pl ⏎ abl pl | native | с сайтами ⏎ из сайтов | с участками ⏎ из участков | meaning | 8 | 'сайты' = websites |
| 16 | 31314 | cakkhusmiṃ | loc sg | native | в глаз | в глазу | case | 10 | loc sg 'в глаз' = acc |
| 18 | 31316 | vatthusmiṃ | loc sg | native | на сайте | на участке | meaning | 8 | 'сайте' = website |
| 23 | 31231 | vatthū | nom pl ⏎ acc pl ⏎ voc pl | native | сайты ⏎ o сайты! | участки ⏎ о участки! | meaning | 8 | 'сайты' = websites; Latin 'o' |
| 24 | 3122 | vatthūni | nom pl ⏎ acc pl ⏎ voc pl | native | сайты ⏎ o сайты! | участки ⏎ о участки! | meaning | 8 | 'сайты' = websites; Latin 'o' |
| 28 | 3126 | āyu | nom sg ⏎ voc sg | eng | life force ⏎ o life forces! | life force ⏎ o life force! | number | 8 | voc sg shown 'life forces' |
| 28 | 3126 | āyu | nom sg ⏎ voc sg | native | жизненная сила ⏎ о жизненные силы! | жизненная сила ⏎ о жизненная сила! | number | 8 | voc sg shown pl |
| 30 | 3128 | vatthu | nom sg ⏎ voc sg | native | сайт ⏎ o сайт! | участок ⏎ о участок! | meaning | 8 | 'сайт' = website; Latin 'o' |

## ta_pron.tsv (7 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 2 | 32320 | tāsaṃ | fem dat pl ⏎ fem gen pl | native | для тех ⏎ из тех | для тех ⏎ тех | case | 9 | gen shown with 'из' |
| 3 | 323232 | tasānaṃ | fem dat pl ⏎ fem gen pl | native | для тех ⏎ из тех | для тех ⏎ тех | case | 9 | gen shown with 'из' |
| 8 | 32326 | tassaṃ | fem loc sg | native | в том | в той | gender | 8 | fem loc sg shown masc 'в том' |
| 9 | 32329 | tāyaṃ | fem loc sg | native | в том | в той | gender | 8 | fem loc sg shown masc 'в том' |
| 10 | 3226 | tissaṃ | fem loc sg | native | в том | в той | gender | 8 | fem loc sg shown masc 'в том' |
| 17 | 32324 | tassa | masc & nt dat sg ⏎ masc & nt gen sg | native | для него ⏎ для этого ⏎ его ⏎ из этого | для него ⏎ для этого ⏎ его ⏎ этого | case | 8 | gen shown with 'из' |
| 27 | 3206 | taṃ 1.2 | nt nom sg  ⏎  masc & fem & nt acc sg  | native | что ⏎ ему ⏎ ей ⏎ что | что ⏎ его ⏎ её ⏎ что | case | 9 | acc 'him/her' shown dative 'ему/ей' |

## ima_pron.tsv (7 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 2 | 333333 | imāsaṃ | fem dat pl ⏎ fem gen pl | native | к этим ⏎ из этих | к этим ⏎ этих | case | 8 | gen shown with 'из' |
| 4 | 3323 | imissā | fem dat sg ⏎ fem gen sg | native | для этого ⏎ из этого | для этой ⏎ этой | gender/case | 9 | fem shown masc; gen with 'из' |
| 6 | 33336 | imāya | fem instr sg ⏎ fem dat sg ⏎ fem abl sg ⏎ fem gen sg | native | с этим ⏎ к этому ⏎ от этого ⏎ из этого | с этой ⏎ к этой ⏎ от этой ⏎ этой | gender/case | 8 | fem shown masc; gen with 'из' |
| 8 | 3324 | imissaṃ | fem loc sg | native | в этом | в этой | gender | 8 | fem loc sg shown masc |
| 14 | 3320 | imesaṃ | masc & nt dat pl ⏎ masc & nt gen pl | native | для этих ⏎ из этих | для этих ⏎ этих | case | 8 | gen shown with 'из' |
| 15 | 33033 | assa 2 | masc & nt dat sg ⏎ masc & nt gen sg | native | для него ⏎ для этого ⏎ его ⏎ из этого | для него ⏎ для этого ⏎ его ⏎ этого | case | 8 | gen shown with 'из' |
| 16 | 33334 | imassa | masc & nt dat sg ⏎ masc & nt gen sg | native | для него ⏎ для этого ⏎ его ⏎ из этого | для него ⏎ для этого ⏎ его ⏎ этого | case | 8 | gen shown with 'из' |

## a_pron.tsv (9 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 2 | 3400 | yāsaṃ | fem dat pl ⏎ fem gen pl | native | для любого из них | для любых ⏎ любых | part count | 7 | dat+gen merged into 'для любого из них' |
| 3 | 34034 | yassā | fem dat sg ⏎ fem gen sg | native | для любого из них | для любой ⏎ любой | part count | 7 | dat+gen merged into 'для любого из них' |
| 4 | 3402 | yāhi | fem instr pl ⏎ fem abl pl | native | с любым ⏎ из любого | с любыми ⏎ из любых | number | 8 | instr/abl pl shown sg |
| 5 | 3403 | yāya | fem instr sg ⏎ fem dat sg ⏎ fem abl sg ⏎ fem gen sg ⏎ fem loc sg | native | с любым ⏎ для любого ⏎ из любого ⏎ из любого ⏎ в любом | с любой ⏎ для любой ⏎ из любой ⏎ любой ⏎ в любой | gender/case | 8 | fem shown masc; gen with 'из' |
| 7 | 3405 | yāyaṃ | fem loc sg | native | в каком бы | в какой бы | gender | 7 | fem loc sg shown masc |
| 8 | 3406 | yassaṃ | fem loc sg | native | в каком бы | в какой бы | gender | 7 | fem loc sg shown masc |
| 12 | 343434 | yesaṃ | masc & nt dat pl ⏎ masc & nt gen pl | native | для любого из них | для любых ⏎ любых | part count | 7 | dat+gen merged into 'для любого из них' |
| 13 | 34342 | yassa | masc & nt dat sg ⏎ masc & nt gen sg | native | для любого из них | для любого ⏎ любого | part count | 7 | dat+gen merged into 'для любого из них' |
| 14 | 34343 | yehi | masc & nt instr pl ⏎ masc & nt abl pl | native | с любым ⏎ из любого | с любыми ⏎ из любых | number | 8 | instr/abl pl shown sg |

## mana_prp.tsv (14 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 2 | 3508 | ākaṅkhamānānaṃ | masc & fem & nt dat pl ⏎ masc & fem & nt gen pl | native | для тех, кто желает ⏎ из тех, кто желает | для тех, кто желает ⏎ тех, кто желает | case | 8 | gen pl with 'из' |
| 5 | 3500 | bhāsamānāya | fem instr sg ⏎ masc & fam & nt  dat sg ⏎ fem abl sg ⏎ fem gen sg ⏎ fem loc sg | native | с (тем, кто) говорит ⏎ для (того, кто) говорит ⏎ от (того, кто) говорит ⏎ о (того, кто) говорит ⏎ в (том, кто) говорит | с (тем, кто) говорит ⏎ для (того, кто) говорит ⏎ от (того, кто) говорит ⏎ (того, кто) говорит ⏎ в (том, кто) говорит | case | 8 | gen shown 'о (того' |
| 6 | 3509 | bhāsamānānaṃ | masc & fem & nt dat pl ⏎ masc & fem & nt gen pl | native | говорящих | для (тех, кто) говорят ⏎ (тех, кто) говорят | part count | 9 | two parts merged into 'говорящих' |
| 7 | 353535 | bhāsamānassa | masc & nt dat sg ⏎ masc & nt gen sg | native | говорящий | для (того, кто) говорит ⏎ (того, кто) говорит | part count/case | 9 | two parts merged into nominative 'говорящий' |
| 8 | 35358 | bhāsamānasmiṃ | masc & nt loc sg | native | говорящий | в (том, кто) говорит | case | 9 | loc sg shown nominative |
| 11 | 3522 | cavamāne | masc & nt acc pl ⏎ masc & nt loc sg ⏎ fem voc sg | native | (те, кто) отпадают ⏎ в (тот, кто) отпадает ⏎ о (тот, кто) отпадает! | (те, кто) отпадают ⏎ в (том, кто) отпадает ⏎ о (тот, кто) отпадает! | case | 7 | loc 'в (тот' |
| 14 | 35359 | haññamānasmiṃ | masc & nt loc sg | native | в (того, кто) подвергается удару | в (том, кто) подвергается удару | case | 8 | 'в (того' |
| 16 | 35035 | maññamānāya | fem instr sg ⏎ masc & fam & nt  dat sg ⏎ fem abl sg ⏎ fem gen sg ⏎ fem loc sg | native | с (тем, кто) думает ⏎ для (того, кто) думает ⏎ от (того, кто) думает ⏎ о (того, кто) думает ⏎ в (том, кто) думает | с (тем, кто) думает ⏎ для (того, кто) думает ⏎ от (того, кто) думает ⏎ (того, кто) думает ⏎ в (том, кто) думает | case | 8 | gen shown 'о (того' |
| 22 | 3506 | saṃvijjamānā | fem nom sg ⏎ masc & fem & nt nom pl ⏎ fem acc pl ⏎ macs & nt abl sg ⏎ masc & nt voc sg ⏎ masc & fem voc pl | native | (тот, кто) существует ⏎ (те, кто) существуют ⏎ от (тот, кто) существует ⏎ o (тот, кто) существует! ⏎ o (те, кто) существуют! | (тот, кто) существует ⏎ (те, кто) существуют ⏎ от (того, кто) существует ⏎ о (тот, кто) существует! ⏎ о (те, кто) существуют! | case | 8 | abl 'от (тот'; Latin 'o' |
| 24 | 35235 | upapajjamāne | masc & nt acc pl ⏎ masc & nt loc sg ⏎ fem voc sg | native | (те, кто) возникают ⏎ в (тот, кто) возникает ⏎ о (тот, кто) возникает! | (те, кто) возникают ⏎ в (том, кто) возникает ⏎ о (тот, кто) возникает! | case | 7 | loc 'в (тот' |
| 25 | 3507 | uppajjamānā | fem nom sg ⏎ masc & fem & nt nom pl ⏎ fem acc pl ⏎ macs & nt abl sg ⏎ masc & nt voc sg ⏎ masc & fem voc pl | native | (тот, кто) возникает ⏎ (те, кто) возникают ⏎ из (тот, кто) возникает ⏎ o (тот, кто) возникает! ⏎ o (те, кто) возникают! | (тот, кто) возникает ⏎ (те, кто) возникают ⏎ из (того, кто) возникает ⏎ о (тот, кто) возникает! ⏎ о (те, кто) возникают! | case | 8 | abl 'из (тот'; Latin 'o' |
| 26 | 3528 | uppajjamānaṃ | nt nom sg ⏎ masc & fem & nt acc sg | native | (тот, кто) поднимается | (тот, кто) возникает | meaning | 6 | 'поднимается' = rises; eng 'arising' |
| 30 | 3503 | vijjamānāsu | fem loc pl | native | среди (тех, кто) существующих | среди (тех, кто) существуют | number | 7 | 'существующих' garbled |
| 31 | 35350 | vuccamānassa | masc & nt dat sg ⏎ masc & nt gen sg | native | для того, к кому обращаются ⏎ для того, к кому обращаются | для того, к кому обращаются ⏎ того, к кому обращаются | case | 8 | gen shown with 'для' |

## anta_prp.tsv (28 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 2 | 36363 | āgacchante | masc & nt acc pl ⏎ masc & nt loc sg | native | (те, кто) приходят ⏎ приходит (тот, кто) приходит | (те, кто) приходят ⏎ в (том, кто) приходит | case | 9 | garbled 'приходит (тот, кто) приходит' |
| 3 | 3647 | āgacchantiyā | fem instr sg ⏎ fem dat sg ⏎ fem abl sg ⏎ fem gen sg ⏎ fem loc sg | native | с (тем, кто) идет ⏎ для (того, кто) идет ⏎ от (того, кто) идет ⏎ того, кто (то, кто) идет ⏎ в (того, кто) идет | с (тем, кто) идет ⏎ для (того, кто) идет ⏎ от (того, кто) идет ⏎ (того, кто) идет ⏎ в (том, кто) идет | case | 9 | garbled gen 'того, кто (то, кто) идет'; loc 'в (того' |
| 7 | 3624 | ajānato | masc & nt dat sg ⏎ masc & nt gen sg | native | для (того, кто) не знает ⏎ о (того, кто) не знает | для (того, кто) не знает ⏎ (того, кто) не знает | case | 8 | gen shown 'о (того' |
| 8 | 3630 | ajānataṃ | masc & nt dat pl ⏎ masc & nt gen pl | native | для тех, кто не знает ⏎ из тех, кто не знает | для тех, кто не знает ⏎ тех, кто не знает | case | 8 | gen with 'из' |
| 9 | 3646 | ajānantiyā | fem instr sg ⏎ fem dat sg ⏎ fem abl sg ⏎ fem gen sg ⏎ fem loc sg | native | с (тем, кто) не знает ⏎ для (того, кто) не знает ⏎ от (того, кто) не знает ⏎ из (того, кто) не знает ⏎ в (том, кто) не знает | с (тем, кто) не знает ⏎ для (того, кто) не знает ⏎ от (того, кто) не знает ⏎ (того, кто) не знает ⏎ в (том, кто) не знает | case | 8 | gen with 'из'; loc 'в (том' |
| 11 | 3622 | alabhantehi | masc & nt instr pl ⏎ masc & nt abl pl | native | с (теми, кто) не получают ⏎ от (теми, кто) не получают | с (теми, кто) не получают ⏎ от (тех, кто) не получают | case | 9 | abl 'от (теми' |
| 12 | 3652 | anussarantīnaṃ | fem dat pl ⏎ fem gen pl | native | для тех, кто помнит ⏎ из тех, кто помнит | для тех, кто помнит ⏎ тех, кто помнит | case | 8 | gen with 'из' |
| 14 | 3625 | apassato | masc & nt dat sg ⏎ masc & nt gen sg | native | для (того, кто) не видит ⏎ для (того, кто) не видит | для (того, кто) не видит ⏎ (того, кто) не видит | case | 8 | gen shown with 'для' |
| 15 | 36336 | apassataṃ | masc & nt dat pl ⏎ masc & nt gen pl | native | для тех, кто не видит ⏎ из тех, кто не видит | для тех, кто не видит ⏎ тех, кто не видит | case | 8 | gen with 'из' |
| 18 | 3626 | bhaṇantassa | masc & nt dat sg ⏎ masc & nt gen sg | native | проповедующий | для (того, кто) проповедует ⏎ (того, кто) проповедует | part count | 9 | two parts merged into 'проповедующий' |
| 19 | 3605 | carantā | masc & nt nom pl ⏎ masc & nt voc pl | eng | (those who are) walking ⏎ o (those who are) dwelling! | (those who are) walking ⏎ o (those who are) walking! | meaning | 9 | voc copied from 'dwelling' |
| 19 | 3605 | carantā | masc & nt nom pl ⏎ masc & nt voc pl | native | (те, кто) ходят ⏎ о (те, кто) живут! | (те, кто) ходят ⏎ о (те, кто) ходят! | meaning | 9 | voc copied from 'dwelling' |
| 20 | 3608 | caranto | masc nom sg ⏎ masc nom pl ⏎ masc & nt voc pl | native | (тот, кто) идет ⏎ (те, кто) идет ⏎ o (те, кто) идет! | (тот, кто) идет ⏎ (те, кто) идут ⏎ о (те, кто) идут! | number | 8 | pl with sg verb |
| 23 | 3607 | gacchanto | masc nom sg ⏎ masc nom pl ⏎ masc & nt voc pl | native | (тот, кто) идет ⏎ (те, кто) идет ⏎ o (те, кто) идет! | (тот, кто) идет ⏎ (те, кто) идут ⏎ о (те, кто) идут! | number | 8 | pl with sg verb |
| 26 | 3627 | gacchantassa | masc & nt dat sg ⏎ masc & nt gen sg | native | для того, кто уходит ⏎ из того, кто уходит | для того, кто уходит ⏎ того, кто уходит | case | 8 | gen with 'из' |
| 27 | 3639 | gacchantī | fem nom sg & pl ⏎ fem acc pl ⏎ fem voc sg & pl | native | (тот, кто) идёт ⏎ (те, кто) идёт ⏎ о (тот, кто) идёт! ⏎ о (те, кто) идёт! | (тот, кто) идёт ⏎ (те, кто) идут ⏎ о (тот, кто) идёт! ⏎ о (те, кто) идут! | number | 7 | pl with sg verb |
| 30 | 3650 | gacchantīnaṃ | fem dat pl ⏎ fem gen pl | native | для (тех, кто) уходит ⏎ из (тех, кто) уходит | для (тех, кто) уходят ⏎ (тех, кто) уходят | case/number | 8 | gen with 'из'; pl with sg verb |
| 34 | 3634 | khiyyantānaṃ | masc & nt dat pl ⏎ masc & nt gen pl | native | для (тех, кто) критикует ⏎  | для (тех, кто) критикуют ⏎ (тех, кто) критикуют | part count | 10 | second part empty |
| 35 | 36536 | khiyyantīnaṃ | fem dat pl ⏎ fem gen pl | native | для (тех, кто) критикует ⏎  | для (тех, кто) критикуют ⏎ (тех, кто) критикуют | part count | 10 | second part empty |
| 43 | 3628 | ujjhāyantassa | masc & nt dat sg ⏎ masc & nt gen sg | native | для того, кто находит недостатки ⏎ для того, кто находит недостатки | для того, кто находит недостатки ⏎ того, кто находит недостатки | case | 8 | gen shown with 'для' |
| 44 | 3633 | ujjhāyantānaṃ | masc & nt dat pl ⏎ masc & nt gen pl | native | для тех, кто находит недостатки ⏎  | для тех, кто находит недостатки ⏎ тех, кто находит недостатки | part count | 10 | second part empty |
| 46 | 3648 | vasantiyā | fem instr sg ⏎ fem dat sg ⏎ fem abl sg ⏎ fem gen sg ⏎ fem loc sg | native | с (тем, кто) живет ⏎ для (того, кто) живет ⏎ от (того, кто) живет ⏎ из (того, кто) живет ⏎ в (того, кто) живет | с (тем, кто) живет ⏎ для (того, кто) живет ⏎ от (того, кто) живет ⏎ (того, кто) живет ⏎ в (том, кто) живет | case | 8 | gen with 'из'; loc 'в (того' |
| 47 | 3606 | viharanto | masc nom sg ⏎ masc nom pl ⏎ masc & nt voc pl | native | (тот, кто) живет ⏎ (те, кто) живет ⏎ o (те, кто) живет! | (тот, кто) живет ⏎ (те, кто) живут ⏎ о (те, кто) живут! | number | 8 | pl with sg verb |
| 49 | 36362 | viharante | masc & nt acc pl ⏎ masc & nt loc sg | native | (те, кто) обитает ⏎ в (том, кто) обитает | (те, кто) обитают ⏎ в (том, кто) обитает | number/case | 8 | pl with sg verb |
| 52 | 3623 | viharato | masc & nt dat sg ⏎ masc & nt gen sg | native | для (того, кто) обитает ⏎ того, кто) обитает | для (того, кто) обитает ⏎ (того, кто) обитает | typo | 9 | unbalanced ')' and gen part |
| 53 | 3629 | viharataṃ | masc & nt dat pl ⏎ masc & nt gen pl | native | для (тех, кто) проживает ⏎ из (тех, кто) проживает | для (тех, кто) проживают ⏎ (тех, кто) проживают | case/number | 8 | gen with 'из'; sg verb |
| 54 | 3632 | viharantānaṃ | masc & nt dat pl ⏎ masc & nt gen pl | native | для (тех, кто) проживает ⏎ из (тех, кто) проживает | для (тех, кто) проживают ⏎ (тех, кто) проживают | case/number | 8 | gen with 'из'; sg verb |
| 55 | 3638 | viharantī | fem nom sg & pl ⏎ fem acc pl ⏎ fem voc sg & pl | native | (тот, кто) обитает ⏎ (те, кто) обитает ⏎ o (тот, кто) обитает! ⏎ o (те, кто) обитает! | (тот, кто) обитает ⏎ (те, кто) обитают ⏎ о (тот, кто) обитает! ⏎ о (те, кто) обитают! | number | 8 | pl with sg verb |

## a_pp.tsv (10 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 5 | 3703 | khīṇasmiṃ | masc & nt loc sg | native | истощенный (что-либо) | в (чём-либо) истощённом | case | 8 | loc without 'в' |
| 18 | 37377 | paṭiviratassa | masc & nt dat sg ⏎ masc & nt gen sg | native | воздержавшийся (один) ⏎ из воздержавшихся (один) | для воздержавшегося (одного) ⏎ воздержавшегося (одного) | case/number | 8 | dat without 'для'; gen shown pl with 'из' |
| 19 | 37378 | paṭiviratehi | masc & nt instr pl ⏎ masc & nt abl pl | eng | with abstained (one) ⏎ from abstained (one) | with abstained (ones) ⏎ from abstained (ones) | number | 7 | instr/abl pl shown sg |
| 19 | 37378 | paṭiviratehi | masc & nt instr pl ⏎ masc & nt abl pl | native | воздержавшийся (один) ⏎ от воздержавшегося (один) | с воздержавшимися (теми) ⏎ от воздержавшихся (тех) | number | 7 | instr/abl pl shown sg |
| 22 | 3720 | puṭṭhā | fem nom sg ⏎ masc & fem & nt nom pl ⏎ fem acc pl ⏎ masc & nt abl sg ⏎ masc & nt voc sg ⏎ masc & fem voc pl | native | (та, которую) спросили ⏎ (те, кого спросили) спросили ⏎ от (той, которую спросили) спросили ⏎ к (тем, кого спросили) спросили! | (та, которую) спросили ⏎ (те, кого) спросили ⏎ от (того, кого) спросили ⏎ о (те, кого) спросили! | meaning/typo | 9 | garbled duplicate 'спросили спросили'; voc 'к' |
| 23 | 37237 | puṭṭhānaṃ | masc & fem & nt dat pl ⏎ masc & fem & nt gen pl | native | для (тех, кого) спросили ⏎ из (тех, кого) спросили | для (тех, кого) спросили ⏎ (тех, кого) спросили | case | 8 | gen with 'из' |
| 24 | 3722 | puṭṭhassa | masc & nt dat sg ⏎ masc & nt gen sg | native | для (того, кого) спросили ⏎ для (того, кого) спросили | для (того, кого) спросили ⏎ (того, кого) спросили | case | 8 | gen shown with 'для' |
| 26 | 3724 | puṭṭho | masc nom sg | native | (того, кого спросили) | (тот, кого) спросили | case | 9 | nom shown genitive '(того, кого' |
| 32 | 3733 | uppanne | masc & nt acc pl ⏎ masc & nt loc sg ⏎ fem voc sg | eng | (somethings) arisen ⏎ in (something) arisen ⏎ o (something) arisen one! | (somethings) arisen ⏎ in (something) arisen ⏎ o (something) arisen! | typo | 9 | stray 'one' |
| 32 | 3733 | uppanne | masc & nt acc pl ⏎ masc & nt loc sg ⏎ fem voc sg | native | (что-то) возникло ⏎ в (что-то) возникло ⏎ о (что-то) возникло один! | (что-то) возникло ⏎ в (что-то) возникло ⏎ о (что-то) возникло! | typo | 9 | stray 'один' |

## a_adj.tsv (4 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 2 | 3805 | aniccāya | fem instr sg ⏎ masc & fem & nt dat sg ⏎ fem abl sg ⏎ fem gen sg ⏎ fem loc sg | native | с непостоянным (вещью) ⏎ для непостоянной (вещи) ⏎ от непостоянной (вещи) ⏎ из непостоянной (вещи) ⏎ в непостоянной (вещи) | с непостоянной (вещью) ⏎ для непостоянной (вещи) ⏎ от непостоянной (вещи) ⏎ непостоянной (вещи) ⏎ в непостоянной (вещи) | gender/case | 9 | fem instr shown masc; gen with 'из' |
| 3 | 38038 | aniccā | fem nom sg ⏎ masc & fem & nt nom pl ⏎ fem acc pl ⏎ masc & nt abl sg ⏎ masc & nt voc sg ⏎ masc & fem voc pl | native | непостоянная (вещь) ⏎ непостоянные (вещи) ⏎ от непостоянной (вещи) ⏎ в непостоянную (вещь(и))! | непостоянная (вещь) ⏎ непостоянные (вещи) ⏎ от непостоянной (вещи) ⏎ о непостоянная (вещь(и))! | case | 9 | voc shown 'в' + acc |
| 12 | 38383 | anuttarāya | fem instr sg ⏎ masc & fem & nt dat sg ⏎ fem abl sg ⏎ fem gen sg ⏎ fem loc sg | native | с непревзойденным (вещью) ⏎ для непревзойденного (вещи) ⏎ из непревзойденного (вещи) ⏎ из непревзойденного (вещи) ⏎ в непревзойденном (вещи) | с непревзойденной (вещью) ⏎ для непревзойденной (вещи) ⏎ из непревзойденной (вещи) ⏎ непревзойденной (вещи) ⏎ в непревзойденной (вещи) | gender/case | 8 | fem shown masc; gen duplicates abl |
| 34 | 3832 | piyasmiṃ | masc & nt loc sg | native | понравившаяся (вещь) | в понравившейся (вещи) | case | 8 | loc sg shown nominative |

## i_adj.tsv (10 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 2 | 39393 | gāminiyā | fem instr sg ⏎ fem dat sg ⏎ fem abl sg ⏎ fem gen sg ⏎ fem loc sg | native | с (одним), который идет ⏎ за (одним), который идет ⏎ от (одним), который идет ⏎ из (одним), который идет ⏎ в (одном), который идет | с (той), которая идет ⏎ для (той), которая идет ⏎ от (той), которая идет ⏎ (той), которая идет ⏎ в (той), которая идет | case | 7 | ungrammatical 'с (одним), который', 'от (одним)'; 'за' for dat |
| 4 | 39397 | nikāmalābhiniyo | fem nom pl ⏎ fem acc pl ⏎ fem voc pl | native | (те), кто легко получает ⏎ то (те), кто легко получает! | (те), кто легко получают ⏎ о (те), кто легко получают! | typo | 9 | 'то' for 'о'; sg verb |
| 9 | 39395 | nikāmalābhī | masc & fem nom sg ⏎ masc & nt nom pl ⏎ masc & nt acc pl ⏎ masc voc sg ⏎ nt voc pl | eng | (one) who easily gets ⏎ (those) who easily gets ⏎ o (one) who easily gets! ⏎ o (those) who easily get! | (one) who easily gets ⏎ (those) who easily get ⏎ o (one) who easily gets! ⏎ o (those) who easily get! | number | 9 | '(those) who easily gets' |
| 9 | 39395 | nikāmalābhī | masc & fem nom sg ⏎ masc & nt nom pl ⏎ masc & nt acc pl ⏎ masc voc sg ⏎ nt voc pl | native | (тот), кто легко получает ⏎ (те), кто легко получает ⏎ тот, кто легко получает! ⏎ тот, кто легко получает! | (тот), кто легко получает ⏎ (те), кто легко получают ⏎ о (тот), кто легко получает! ⏎ о (те), кто легко получают! | case/number | 9 | voc parts lack 'о' and sg/pl |
| 16 | 39394 | jegucchismiṃ | masc & nt loc sg | native | у (того), кто испытывает отвращение | в (том), кто испытывает отвращение | case | 7 | 'у' = at; eng 'in' |
| 17 | 3922 | tādinaṃ | masc acc sg ⏎ masc & nt dat pl ⏎ masc & nt gen pl | native | (один) такого характера ⏎ для (тех) такого характера ⏎ из (тех) такого характера | (один) такого характера ⏎ для (тех) такого характера ⏎ (тех) такого характера | case | 8 | gen with 'из' |
| 18 | 3907 | ātāpino | masc nom pl ⏎ masc acc pl ⏎ masc & nt dat sg ⏎ masc & nt gen sg ⏎ masc voc pl | native | страстные (вещи) ⏎ для страстной (вещи) ⏎ из страстной (вещи) ⏎ о страстные (вещи)! | страстные (вещи) ⏎ для страстной (вещи) ⏎ страстной (вещи) ⏎ о страстные (вещи)! | case | 8 | gen with 'из' |
| 19 | 393939 | evaṃdiṭṭhino | masc nom pl ⏎ masc acc pl ⏎ masc & nt dat sg ⏎ masc & nt gen sg ⏎ masc voc pl | native | (те, кто) придерживается такой точки зрения ⏎ для (одного) придерживающегося такой точки зрения ⏎ из (одного) придерживающегося такой точки зрения ⏎ o (те, кто) придерживается такой точки зрения! | (те, кто) придерживается такой точки зрения ⏎ для (одного) придерживающегося такой точки зрения ⏎ (одного) придерживающегося такой точки зрения ⏎ o (те, кто) придерживается такой точки зрения! | case | 8 | gen with 'из' |
| 20 | 39398 | nikāmalābhino | masc nom pl ⏎ masc acc pl ⏎ masc & nt dat sg ⏎ masc & nt gen sg ⏎ masc voc pl | native | (те), кто легко получает ⏎ для (одного), кто легко получает ⏎ из (одного), кто легко получает ⏎ для (тех), кто легко получает! | (те), кто легко получает ⏎ для (одного), кто легко получает ⏎ (одного), кто легко получает ⏎ о (те), кто легко получают! | case | 9 | gen with 'из'; voc pl shown 'для' |
| 24 | 39396 | nikāmalābhiṃ | nt nom sg ⏎ masc & nt acc sg ⏎ nt voc sg | native | (тот), кто легко получает ⏎ тот, кто легко получает! | (тот), кто легко получает ⏎ о (тот), кто легко получает! | case | 8 | voc without 'о' |

## u_adj.tsv (4 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 3 | 40409 | abhijjhālūhi | masc & fem & nt instr pl ⏎ masc & fem & nt abl pl | native | с алчными (теми) ⏎ от алчных (теми) | с алчными (теми) ⏎ от алчных (тех) | case | 9 | abl 'от алчных (теми)' |
| 6 | 40405 | abhijjhālussa | masc & nt dat sg ⏎ masc & nt gen sg | native | алчный (один) ⏎ из алчного (один) | для алчного (одного) ⏎ алчного (одного) | case | 8 | dat shown nominative; gen with 'из' |
| 7 | 40408 | abhijjhāluno | masc & nt dat sg ⏎ masc & nt gen sg | native | алчный (один) ⏎ из алчного (один) | для алчного (одного) ⏎ алчного (одного) | case | 8 | dat shown nominative; gen with 'из' |
| 22 | 40240 | dummaṅkuyaṃ | fem loc sg | native | упрямый (один) | в упрямом (одном) | case | 9 | loc sg shown nominative |

## card.tsv (10 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 2 | 4100 | catassannaṃ | fem dat pl ⏎ fem gen pl | native | для четырех из четырех | для четырех ⏎ четырех | part count | 10 | two parts merged: 'для четырех из четырех' |
| 6 | 4105 | catunnaṃ | masc & nt dat pl ⏎ masc & nt gen pl | native | для четырех из четырех | для четырех ⏎ четырех | part count | 10 | two parts merged |
| 10 | 414141 | dvinnaṃ | x dat pl ⏎ x gen pl | native | для двух из двух | для двух ⏎ двух | part count | 10 | two parts merged |
| 15 | 4122 | ekissā | fem dat sg ⏎ fem gen sg | native | для одного из одного | для одной ⏎ одной | part count | 10 | two parts merged |
| 16 | 4120 | ekāya | fem instr sg ⏎ fem dat sg ⏎ fem abl sg ⏎ fem gen sg ⏎ fem loc sg | native | один ⏎ за один ⏎ из одного ⏎ из одного ⏎ в одном | с одной ⏎ для одной ⏎ из одной ⏎ одной ⏎ в одной | gender/case | 9 | instr shown nominative; dat 'за один'; fem shown masc |
| 17 | 41413 | ekā | fem nom sg | native | один | одна | gender | 9 | fem nom sg shown 'один' |
| 20 | 41419 | ekassa | masc & nt dat sg ⏎ masc & nt gen sg | native | для одного из одного | для одного ⏎ одного | part count | 10 | two parts merged |
| 26 | 4127 | tissannaṃ | fem dat pl ⏎ fem gen pl | native | для трех из трех | для трех ⏎ трех | part count | 10 | two parts merged |
| 28 | 4125 | tīhi | masc & fem & nt instr pl ⏎ masc & fem & nt abl pl | native | с тремя из трех | с тремя ⏎ из трех | part count | 10 | two parts merged: 'с тремя из трех' |
| 30 | 4126 | tiṇṇaṃ | masc & nt dat pl ⏎ masc & nt gen pl | native | для трех из трех | для трех ⏎ трех | part count | 10 | two parts merged |

## a_card.tsv (5 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 5 | 4204 | satānaṃ | nt dat pl ⏎ nt gen pl | native | сто ⏎ из ста | для ста ⏎ ста | case | 9 | dat/gen shown 'сто ⏎ из ста' |
| 6 | 4209 | satāya | nt dat sg | native | сто | для ста | case | 9 | dat sg shown 'сто' |
| 7 | 4208 | satassa | nt dat sg ⏎ nt gen sg | native | сто ⏎ из ста | для ста ⏎ ста | case | 9 | dat/gen shown 'сто ⏎ из ста' |
| 16 | 42426 | pañcannaṃ | x dat pl ⏎ x gen pl | native | за пять ⏎ из пяти | для пяти ⏎ пяти | case | 8 | dat shown 'за пять'; gen with 'из' |
| 18 | 42427 | pañcasu | x loc pl | eng | amonst five | amongst five | typo | 10 | 'amonst' |

## i_card.tsv (4 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 3 | 4302 | koṭīnaṃ | fem dat pl ⏎ fem gen pl | native | за десять миллионов ⏎ из десяти миллионов | для десяти миллионов ⏎ десяти миллионов | case | 8 | dat 'за'; gen with 'из' |
| 5 | 4306 | koṭiyā | fem instr sg ⏎ fem dat sg ⏎ fem abl sg ⏎ fem gen sg ⏎ fem loc sg | native | с десятью миллионами ⏎ для десяти миллионов ⏎ из десяти миллионов ⏎ из десяти миллионов ⏎ в десяти миллионах | с десятью миллионами ⏎ для десяти миллионов ⏎ из десяти миллионов ⏎ десяти миллионов ⏎ в десяти миллионах | case | 8 | gen with 'из' |
| 11 | 4305 | vīsāya | fem instr sg ⏎ fem dat sg ⏎ fem abl sg ⏎ fem gen sg ⏎ fem loc sg | native | с двадцатью ⏎ за двадцать ⏎ из двадцати ⏎ в двадцать | с двадцатью ⏎ для двадцати ⏎ из двадцати ⏎ двадцати ⏎ в двадцати | part count | 10 | 4 parts for 5; dat 'за двадцать' |
| 15 | 4304 | vīsatiyā | fem instr sg ⏎ fem dat sg ⏎ fem abl sg ⏎ fem gen sg ⏎ fem loc sg | native | с двадцатью ⏎ за двадцать ⏎ из двадцати ⏎ в двадцать | с двадцатью ⏎ для двадцати ⏎ из двадцати ⏎ двадцати ⏎ в двадцати | part count | 10 | 4 parts for 5; dat 'за двадцать' |

## ordin.tsv (9 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 3 | 44044 | chaṭṭhīnaṃ | fem dat pl ⏎ fem gen pl | native | для шестых (единиц) ⏎ из шестых (единиц) | для шестых (единиц) ⏎ шестых (единиц) | case | 8 | gen with 'из' |
| 4 | 4404 | catutthiyā | fem instr sg ⏎ fem dat sg ⏎ fem abl sg ⏎ fem gen sg ⏎ fem loc sg | native | с четвертым (одним) ⏎ для четвертого (одного) ⏎ из четвертого (одного) ⏎ в четвертом (одном) | с четвертым (одним) ⏎ для четвертого (одного) ⏎ из четвертого (одного) ⏎ четвертого (одного) ⏎ в четвертом (одном) | part count | 10 | 4 parts for 5 |
| 8 | 44440 | pañcamiyo | fem nom pl ⏎ fem acc pl ⏎ fem voc pl | native | пятый (единицы) ⏎ о пятый (единицы)! | пятые (единицы) ⏎ о пятые (единицы)! | number | 8 | pl noun with sg adj |
| 10 | 4405 | paṭhamāya | fem instr sg ⏎ masc & fem & nt dat sg ⏎ fem abl sg ⏎ fem gen sg ⏎ fem loc sg | native | с первым (одним) ⏎ для первого (одного) ⏎ из первого (одного) ⏎ в первом (одном) | с первым (одним) ⏎ для первого (одного) ⏎ из первого (одного) ⏎ первого (одного) ⏎ в первом (одном) | part count | 10 | 4 parts for 5 |
| 13 | 444444 | dutiyāyo | fem nom pl ⏎ fem acc pl ⏎ fem voc pl | native | второй (один) ⏎ о второй (один)! | вторые (единицы) ⏎ о вторые (единицы)! | number | 8 | pl shown sg |
| 14 | 44443 | paṭhamā | fem nom sg ⏎ masc & fem & nt nom pl ⏎ fem acc pl ⏎ masc & nt abl sg ⏎ masc & nt voc sg ⏎ masc & fem voc pl | native | первый (один(ы)) ⏎ от первого (один) ⏎ до первого (один(ы))! | первый (один(ы)) ⏎ от первого (один) ⏎ о первый (один(ы))! | case | 9 | voc shown 'до' |
| 15 | 44444 | dutiyānaṃ | masc & fem & nt dat pl ⏎ masc & fem & nt gen pl | native | для второго (единиц) ⏎ второго (единиц) | для вторых (единиц) ⏎ вторых (единиц) | number | 8 | pl shown sg 'второго' |
| 17 | 4423 | paṭhame | masc & nt acc pl ⏎ masc & nt loc sg ⏎ fem voc sg | native | первые (единицы) ⏎ в первый (один) ⏎ о первый (один)! | первые (единицы) ⏎ в первом (одном) ⏎ о первый (один)! | case | 9 | loc shown nominative-acc 'в первый' |
| 18 | 44447 | paṭhamassa | masc & nt dat sg ⏎ masc & nt gen sg | native | для первого (одного) ⏎ из первого (одного) | для первого (одного) ⏎ первого (одного) | case | 8 | gen with 'из' |

## a_ptp.tsv (13 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 5 | 4503 | kappiye | masc & nt acc pl ⏎ masc & nt loc sg ⏎ fem voc sg | native | допустимые (вещи) ⏎ в допустимой (вещи) ⏎ в допустимой (вещи)! | допустимые (вещи) ⏎ в допустимой (вещи) ⏎ о допустимая (вещь)! | case | 9 | voc shown 'в' |
| 6 | 4504 | karaṇīyā | fem nom sg ⏎ masc & fem & nt nom pl ⏎ fem acc pl ⏎ masc & nt abl sg ⏎ masc & nt voc sg ⏎ masc & fem voc pl | native | (то, что) следует сделать ⏎ из (то, что) следует сделать ⏎ o (то, что) следует сделать! | (то, что) следует сделать ⏎ из (того, что) следует сделать ⏎ о (то, что) следует сделать! | case | 8 | abl 'из (то'; Latin 'o' |
| 7 | 4508 | karaṇīye | masc & nt acc pl ⏎ masc & nt loc sg ⏎ fem voc sg | native | (вещи, которые) следует делать ⏎ в (вещь, которую) следует делать ⏎ о (вещь, которую) следует делать! | (вещи, которые) следует делать ⏎ в (вещи, которую) следует делать ⏎ о (вещь, которую) следует делать! | case | 8 | loc 'в (вещь' |
| 13 | 454545 | manasikaraṇīyānaṃ | masc & fem & nt dat pl ⏎ masc & fem & nt gen pl | native | о (вещах, которые) следует помнить ⏎ о (вещах, которые) следует помнить | для (вещей, которые) следует помнить ⏎ (вещей, которые) следует помнить | case | 9 | dat/gen shown 'о (вещах' |
| 14 | 45452 | pahātabbā | fem nom sg ⏎ masc & fem & nt nom pl ⏎ fem acc pl ⏎ masc & nt abl sg ⏎ masc & nt voc sg ⏎ masc & fem voc pl | native | (вещь(и), от которой следует отказаться ⏎ из (вещь, от которой) следует отказаться ⏎ o (вещь(и), от которой) следует отказаться! | (вещь(и), от которой) следует отказаться ⏎ из (вещи, от которой) следует отказаться ⏎ о (вещь(и), от которой) следует отказаться! | typo | 8 | unbalanced parenthesis; abl; Latin 'o' |
| 15 | 45454 | pahātabbassa | masc & nt dat sg ⏎ masc & nt gen sg | native | для (вещи, которую) следует оставить ⏎ из (вещи, которую) следует оставить | для (вещи, которую) следует оставить ⏎ (вещи, которую) следует оставить | case | 8 | gen with 'из' |
| 18 | 45456 | sacchikaraṇīyassa | masc & nt dat sg ⏎ masc & nt gen sg | eng | for (thing) realizable by oneself ⏎ of for (thing) realizable by oneself | for (thing) realizable by oneself ⏎ of (thing) realizable by oneself | typo | 10 | 'of for' |
| 18 | 45456 | sacchikaraṇīyassa | masc & nt dat sg ⏎ masc & nt gen sg | native | для (вещи), реализуемой самостоятельно ⏎ для (вещи), реализуемой самостоятельно | для (вещи), реализуемой самостоятельно ⏎ (вещи), реализуемой самостоятельно | case | 10 | gen shown 'для' (duplicate) |
| 19 | 45458 | sevitabbā | fem nom sg ⏎ masc & fem & nt nom pl ⏎ fem acc pl ⏎ masc & nt abl sg ⏎ masc & nt voc sg ⏎ masc & fem voc pl | native | (то, что) следует практиковать ⏎ из (то, что) следует практиковать ⏎ o (то, что) следует практиковать! | (то, что) следует практиковать ⏎ из (того, что) следует практиковать ⏎ о (то, что) следует практиковать! | case | 8 | abl 'из (то'; Latin 'o' |
| 20 | 4520 | sevitabbe | masc & nt acc pl ⏎ masc & nt loc sg ⏎ fem voc sg | native | (вещи, которые) следует практиковать ⏎ в (вещь, которую) следует практиковать ⏎ o (вещь, которую) следует практиковать! | (вещи, которые) следует практиковать ⏎ в (вещи, которую) следует практиковать ⏎ о (вещь, которую) следует практиковать! | case | 8 | loc 'в (вещь' |
| 26 | 4524 | vacanīyā | fem nom sg ⏎ masc & fem & nt nom pl ⏎ fem acc pl ⏎ masc & nt abl sg ⏎ masc & nt voc sg ⏎ masc & fem voc pl | native | (что(и) следует сказать) ⏎ из (что(и) следует сказать) ⏎ o (что(и) следует сказать) следует сказать! | (то(те), что) следует сказать ⏎ из (того, что) следует сказать ⏎ о (то(те), что) следует сказать! | meaning/typo | 9 | garbled 'что(и)'; repeated 'следует сказать' |
| 29 | 4527 | veditabbā | fem nom sg ⏎ masc & fem & nt nom pl ⏎ fem acc pl ⏎ masc & nt abl sg ⏎ masc & nt voc sg ⏎ masc & fem voc pl | native | (вещь(и), которую(ые) можно узнать ⏎ из (вещи, которую) можно узнать ⏎ o (вещь(и), которую) можно узнать! | (вещь(и), которую(ые)) можно узнать ⏎ из (вещи, которую) можно узнать ⏎ о (вещь(и), которую) можно узнать! | typo | 8 | unbalanced parenthesis; Latin 'o' |
| 30 | 4530 | veditabbe | masc & nt acc pl ⏎ masc & nt loc sg ⏎ fem voc sg | native | (вещи, которые) можно познать ⏎ в (вещь, которую) можно познать ⏎ o (вещь, которую) можно познать! | (вещи, которые) можно познать ⏎ в (вещи, которую) можно познать ⏎ о (вещь, которую) можно познать! | case | 8 | loc 'в (вещь' |

## as_masc.tsv (5 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 12 | 5104 | manamhi | loc sg | native | с учетом | в уме | meaning | 9 | 'с учетом' = taking into account |
| 13 | 5107 | manasi | loc sg | native | с учетом | в уме | meaning | 9 | 'с учетом' = taking into account |
| 14 | 5109 | manasmiṃ | loc sg | native | с учетом | в уме | meaning | 9 | 'с учетом' = taking into account |
| 16 | 51051 | manā | nom pl ⏎ abl sg ⏎ voc sg & pl | native | разум ⏎ от разума ⏎ к разуму(ам)! | умы ⏎ от разума ⏎ о разум(ы)! | number/case | 8 | nom pl shown sg; voc 'к' (dat) |
| 18 | 5100 | mana | voc sg | native | О, помни! | О разум! | meaning | 10 | 'О, помни!' = 'oh, remember!' |

## go_masc.tsv (2 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 6 | 52052 | gavaṃ | acc sg ⏎ dat pl ⏎ gen pl | eng | cow<pr>for cows ⏎ of cows | cow ⏎ for cows ⏎ of cows | typo | 10 | '<pr>' instead of ' ⏎ ' |
| 6 | 52052 | gavaṃ | acc sg ⏎ dat pl ⏎ gen pl | native | корова<pr>для коров ⏎ коров | корова ⏎ для коров ⏎ коров | typo | 10 | '<pr>' instead of ' ⏎ ' |

## a2_masc.tsv (1 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 11 | 53053 | attā | nom sg ⏎ voc sg | native | самолюбие! | самость ⏎ о самость! | meaning | 9 | 'самолюбие' = self-love; no 'nom' part |

## app.tsv (3 cells)

| line | id | pali | gramma | col | current | proposed | type | conf | note |
|---|---|---|---|---|---|---|---|---|---|
| 5 | 6303 | bhuttāvino | masc nom pl ⏎ masc acc pl ⏎ masc & nt dat sg ⏎ masc & nt gen sg ⏎ masc voc pl | native | (те), кто ел ⏎ для (одного), кто ел ⏎ из (одного), кто ел ⏎ o (те), кто ел! | (те), кто ел ⏎ для (одного), кто ел ⏎ (одного), кто ел ⏎ о (те), кто ел! | case | 8 | gen with 'из'; Latin 'o' |
| 6 | 6304 | bhuttāvīnaṃ | masc & nt dat pl ⏎ masc & nt gen pl | native | для тех, кто ел ⏎ из тех, кто ел | для тех, кто ел ⏎ тех, кто ел | case | 8 | gen with 'из' |
| 12 | 63630 | vijitāvinaṃ | masc acc sg ⏎ masc & nt dat pl ⏎ masc & nt gen pl | eng | (one) who has conquered ⏎ for (those) who has conquered ⏎ of (those) who has conquered | (one) who has conquered ⏎ for (those) who have conquered ⏎ of (those) who have conquered | number | 8 | 'those who has' |

## Uncertain — need your decision (no proposed edit unless stated)

- **aor** (36): viharimhā/viharittha/vihariṃsu (aor:36-38) 'removed' matches DPD 'vihari 2.1'; but sibling aor:39 'I lived' and `of`='vihari'. Decide: keep 'removed' or change to 'lived'. Native aor:37 'вы все удалены' is passive either way (should be 'вы все удалили').
- **systemic** (gender): '(вещь)' used with masc/neut adjective endings in a_adj, i_adj, u_adj, a_pp ('непостоянный (вещь)', 'с непостоянным (вещью)'); a_adj:21 uses '(предмета)'. Needs a convention decision; not listed per cell.
- **systemic** (adjectives): a_pp/a_ptp: participle after preposition left uninflected ('из (чего-то) истощенный', 'с (чем-то) возник'). Needs convention decision.
- **systemic** (у/в): loc 'in' rendered 'у' in go_masc:12-13, raja_masc:14-15 ('у королей'); proposal 'в коровах'/'в королях' (confidence 6).
- **raja_masc** (5): 'царей' vs 'королей' within raja_masc (5,6,7 vs 10,11): inconsistent glosses of 'king'.
- **a_ptp** (24): sikkhitabba: 'обучать' = teach (others); 'train' ≈ 'обучаться/осваивать'.
- **cond** (native): cond.tsv: native column empty for all 12 rows (not translated yet; not an error).
- **app** (9): bhuttāvissa gramma 'nt gen sg' but eng 'for (one)...' (dat). Probably gramma should be 'masc & nt dat sg<br>masc & nt gen sg' like sibling rows; needs decision.
- **app** (10): dassāvine gramma 'masc loc sg' native 'у (того)' (at); check case against DPD.
- **a2_masc** (3): attānaṃ: native 'само<br>для себя<br>самости' (dat pl shown sg 'себя', gen pl 'самости'); wording decision.
- **a2_masc** (12): atta voc 'о себя!' — wording decision (propose 'о самость!').
- **perf** (10): agacchaṃ eng 'I reached' vs 'I went' of sibling rows.
- **i_fem** (5): dat sg rendered 'за' (i_fem:5, 12; a_nt:20 'за отказ') instead of 'для'.
- **ii_masc** (14): udāyinā 'поднимаясь<br>от поднимаясь' ungrammatical; may be proper name Udāyī.
- **ii_masc** (24): gihī native voc 'о домовладельце(ах)!' prepositional endings; propose 'о домовладелец(ы)!'.
- **ii_masc** (26): medhāvī: gramma 3 parts, eng/native 4 parts.
- **aor** (33): santappesuṃ 'они были довольны' (passive) vs 'they pleased'; maybe 'они удовлетворили'.
- **ant** (38): pāpima 'О, злой дух!' vs eng 'o evil one'.
- **ii_masc** (14): udāyinā: 'поднимаясь<br>от поднимаясь' ungrammatical; may be proper name Udāyī
- **ii_masc** (26): medhāvī gramma 3 parts, eng/native 4 parts
- **aor** (33): santappesuṃ 'they pleased' → 'они были довольны' (passive); maybe 'они удовлетворили'
- **systemic** (acc sg): native shows acc sg of animates in nominative (a_masc:10 Брахман, :14 мужчина; i_masc:10,:18; ii_masc:3-5; u_masc:3...)
- **systemic** (2nd sg): 'вы' used for 2nd sg in pr:62-66,69-71,74-78; fut:14,17,19,20 while 'ты' used elsewhere
- **ger** (4): pahāya/pahātuṃ/appahāya 'giving up' rendered 'сдаваться/сдаться' (= surrender); propose 'отказываясь/отказаться/не отказываясь'
- **ger** (10): native uses nouns/adjectives/finite verbs for gerunds: vineyya 'удаление', pariyādāya 'изнашивается', samādāya 'предприятие', abhibhuyya 'победа', atikkamma 'преодоление', paricca 'всеобъемлющий'; abs:6 'лично пережил'

## Mechanical classes found by scripted scans (need your approval as a rule; not in the table above)
- **Latin `o` instead of Cyrillic `о`** at the start of a vocative native part: 71 cells (e.g. u_fem 'o элементы!', anta_prp 'o (те, кто) идет!'). Fix: replace leading `o ` with `о ` in native parts. Overlaps with some table rows (those already carry `о`).
- **Genitive part of `native` starting with `из `** where the matching `gramma` part is `gen`: 55 cells (a large subset is already in the table above with full proposed values; the rest would be fixed by dropping `из `). Apply individual rows first, then the rule on what remains.
- **Whitespace/typo**: trailing space in pali `mama `, `gavaṃ `, `attānaṃ ` (pers_pron:7, go_masc:6, a2_masc:3); trailing space in a_masc:34 eng, adv_time:9 gramma, ta_pron:28 gramma (`nt nom sg <br> masc & fem & nt acc sg `), double spaces/`fam` typo in mana_prp:5 and :16 gramma (`masc & fam & nt  dat sg`), stray space in a_pp:12 eng. Not in table; a pure trim/typo fix.
- **cond.tsv**: native empty in all 12 rows (not translated; not an error).

## NOTICED — NOT TOUCHING
- `samasa.tsv` was already modified in the working tree before this thread started (git status at session start); not touched.
- opt.tsv lines 6-7, 19-21, opt_be.tsv:10 and adv.tsv:15-16 contain quoted cells with an embedded newline or tab (e.g. gramma `"opt 3rd pl<TAB>"`); they parse correctly with a normal CSV reader. Left as is.
- Verified OK against dpd.db (not errors): adv `pare` ('day before yesterday'), `uddhaṃ` ('after; afterwards'), `yathā`, cond 'would have fallen into' (DPD gloss for agamissa).

## Limits of the scan
- Read: `gramma`, `eng`, `native`, `pali`, `of` of all 49 sheets that have `eng`/`native` (1,321 rows). The 12 sandhi/etymology sheets without `eng`/`native` were not audited.
- Russian wording is my reading, not a native check; proposals marked 7-8 should be reviewed by you. Confidence is per proposal, not per sheet.
- Row-level reading was single-pass; absence of a finding is not proof a row is correct. Systemic items (gender of '(вещь)', uninflected participles, 'вы' for 2nd sg, acc sg of animates in nominative) are listed once, not per cell.

