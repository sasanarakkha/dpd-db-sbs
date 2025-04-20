# Таблица DPD Headwords — столбцы и свойства

Основная функциональность базы данных реализована через

``` python
class DpdHeadword(Base):
    __tablename__ = "dpd_headwords"
```

Это можно найти в [db/models.py](https://github.com/sasanarakkha/dpd-db-sbs/blob/c0ff5b0591627fff7818b717d6c5f8e8ffdd63ec/db/models.py#L535){target="_blank"}.

- **`жирным`**  выделены названия столбцов таблицы,
- *`курсивом`* обозначены производные свойства,
- `[тип данных]` — в квадратных скобках,
- далее следует краткое описание столбца или свойства

Краткий обзор:

- **`id`** `[int]` уникальный числовой идентификатор для каждого слова

- **`lemma_1`** `[str]`  уникальная словарная форма с номером

- *`lemma_clean`* `[str]` lemma_1 без завершающих цифр

- *`lemma_1_`* `[str]` lemma_1 с подчёркиваниями вместо пробелов, используется в коде

- *`lemma_link`* `[str]` lemma_1 с %20 вместо пробелов, используется в веб-ссылках

- *`lemma_ipa`* `[str]` lemma_clean в международной фонетической транскрипции (IPA)

- *`lemma_tts`* `[str]` lemma_clean в международной фонетической транскрипции (IPA) для синтеза речи

- *`lemma_trad`* `[str]` форма слова, встречающаяся в традиционных грамматиках пали

- *`lemma_si`* `[str]` форма слова, встречающаяся в традиционных грамматиках пали, на Сингальском алфавите

- **`lemma_2`** `[str]` мужской именительный падеж единственного числа для имён существительных

- **`pos`** `[str]` часть речи

- *`pos_list`* `[list]` список всех частей речи в базе данных

- *`pos_si`* `[str]` часть речи на сингальском

- *`pos_si_full`* `[str]` часть речи на сингальском, без сокращений

- **`grammar`** `[str]` грамматическая информация

- **`derived_from`** `[str]` этимологический родитель, от которого образовано слово

- **`neg`** `[str]` является ли слово отрицательным или двойным отрицанием?

- **`verb`** `[str]` является ли глагол побудительным, страдательным или отымённым?

- **`trans`** `[str]` глагол переходный, непереходный или двойной переходный?

- **`plus_case`** `[str]` какой падеж вызывает слово в предложении?

- *`plus_case_si`* `[str]` вышеупомянутый падеж на сингальском

- **`meaning_1`** `[str]` контекстуальное значение на английском

- **`meaning_lit`** `[str]` буквальное значение на английском

- **`meaning_2`** `[str]` значение по словарю Буддхадатты

- *`meaning_combo`* `[str]` объединение meaning_1, meaning_lit и meaning_2

- *`meaning_combo_html`* `[str]` то же, с выделением meaning_1 в HTML <b\>

- *`meaning_si`* `[str]` meaning_1 переведённый на сингальский

- **`non_ia`** `[str]` заимствовано ли слово из неиндоарийского языка?

- **`sanskrit`** `[str]` ближайшее соответствие в санскрите по Монье-Вильямсу или Эджертону

- *`sanskrit_clean`* `[str]` санскритское соответствие, очищенное от содержимого в `[квадратных скобках]`?

- **`root_key`** `[str]` уникальный ключ корня из таблицы `dpd_roots`

- *`root_clean`* `[str]` root_key без завершающих цифр

- *`root_count`* `[int]` сколько раз встречается данный корень в базе

- **`root_sign`** `[str]` признак спряжения корня

- **`root_base`** `[str]` корень и признак спряжения вместе, основа

- *`root_base_clean`* `[str]` основа, но без фонетических изменений

- **`family_root`** `[str]` родственное семейство приставок и корней

- *`root_family_key`* `[str]` родственное семейство приставок и корней, через пробел

- **`family_word`** `[str]`  если не корень, то из какого словарного семейства слово? 

- **`family_compound`** `[str]` если составное слово, то его компоненты через пробел?

- *`family_compound_list`* `[list]` список значений family_compound

- **`family_idioms`** `[str]` если идиома, то её компоненты через пробел

- *`family_idioms_list`* `[list]` список значений family_idioms

- **`family_set`** `[str]` к какой группе принадлежит слово?

- *`family_set_list`* `[list]` список значений family_set

- **`construction`** `[str]` образование слова

- *`construction_clean`* `[str]` образование слова без фонетических изменений

- *`construction_summary`* `[str]` образование слова кратко в одну строку

- *`construction_summary_si`* `[str]` образование слова кратко в одну строку, на сингальском

- *`construction_line1`* `[str]` первая строка образование слова

- **`derivative`** `[str]` слово производное (kita, kicca, taddhita)

- **`suffix`** `[str]` суффикс (kita, kicca или taddhita)

- **`phonetic`** `[str]`  какие фонетические изменения произошли?

- **`compound_type`** `[str]` тип составного слова, если применимо

- **`compound_construction`** `[str]` образование составного слова, если применимо

- **`non_root_in_comps`** `[str]` (в основном не используется)

- **`source_1`** `[str]` источник первого примера

- *`source_link_1`* `[str]` источник первого примера с HTML-ссылкой

- **`sutta_1`** `[str]` из какой сутты первый пример?

- **`example_1`** `[str]` первый хороший контекстуальный пример

- **`source_2`** `[str]` источник второго примера

- *`source_link_2`* `[str]` источник второго примера с HTML-ссылкой

- *`source_link_sutta`* `[str]` код сутты с HTML-ссылкой

- **`sutta_2`** `[str]` из какой сутты второй пример?

- **`example_2`** `[str]` второй хороший контекстуальный пример

- *`degree_of_completion`* `[str]` насколько полные данные о слове

- *`degree_of_completion_html`* `[str]` насколько полные данные о слове, с HTML-тегами

- **`antonym`** `[str]` антонимы, через запятую и пробел

- *`antonym_list`* `[list]` список антонимов

- **`synonym`** `[str]` синонимы, через запятую и пробел

- *`synonym_list`* `[list]` список синонимов

- **`variant`** `[str]` what are the variant readings of the headword found in other Pāḷi texts, comma space separated?

- *`variant_list`* `[list]` list of all the variants

- **`var_phonetic`** `[str]` (currently unused) what are other phonetic variants of the headword found in Pāḷi texts, comma space separated?

- **`var_text`** `[str]` (currently unused) what are the variant readings of the headword found in other Pāḷi texts, comma space separated?

- **`commentary`** `[str]` how does the commentary define the headword, new line separated?

- **`notes`** `[str]` what further information should be mentioned about the headword?

- **`cognate`** `[str]` what English cognates does the headword have?

- **`link`** `[str]` for plants, animals and historical characters what is the wikipedia link?

- **`origin`** `[str]` what is the origin of the headword's data?

- **`stem`** `[str]` what is the stem upon which the inflection pattern is built?

- **`pattern`** `[str]` what is the inflection pattern found in the `inflection_patterns` table?

- **`created_at`** `[datetime]` when was the headword created?

- **`updated_at`** `[datetime]` when was the headword updated?

- **`inflections`** `[str]` what inflected forms does the headword take, comma separated?

- *`inflections_list`* `[list]` list of inflections

- **`inflections_api_ca_eva_iti`** `[str]` what inflected forms can be found in sandhi compounds with api, ca, eva and iti, comma separated?

- *`inflections_list_api_ca_eva_iti`* `[list]` list of inflections found in sandhi compounds with api, ca, eva and iti

- *`inflections_list_all`* `[list]` list of all inflections, including those with api, ca, eva and iti

- **`inflections_sinhala`** `[str]` what are the inflected forms in Sinhala script, comma separated?

- *`inflections_sinhala_list`* `[list]` list if all inflections in Sinhala script

- **`inflections_devanagari`** `[str]` what are the inflected forms in Devanagari script, comma separated?

- *`inflections_devanagari_list`* `[list]` list of all inflections in Devanagari script

- **`inflections_thai`** `[str]` what are the inflected forms in Thai script, comma separated?

- *`inflections_thai_list`* `[list]` list of all inflections in Thai script

- **`inflections_html`** `[str]` inflection table of the headwords as HTML table

- **`freq_html`** `[str]` frequency map of the word in CST corpus as HTML table

- **`ebt_count`** `[str]` how many times does the word occur in early Buddhist texts?

- *`needs_grammar_button`* `[bool]` does the headword need a grammar button?

- *`needs_example_button`* `[bool]` does the headword needs an example button?

- *`needs_examples_button`* `[bool]` does the headword needs an examples button?

- *`needs_conjugation_button`* `[bool]` does the headword need a conjugations button?

- *`needs_declension_button`* `[bool]` does the headword need a declensions button?

- *`needs_root_family_button`* `[bool]` does the headword need a root family button?

- *`needs_word_family_button`* `[bool]` does the headword need a word family button?

- *`needs_compound_family_button`* `[bool]` does the headword need a compound family button?

- *`needs_compound_families_button`* `[bool]` does the headword need a compound families button?

- *`needs_idioms_button`* `[bool]` does the headword need an idioms button?

- *`needs_set_button`* `[bool]` does the headword need a set button?

- *`needs_sets_button`* `[bool]` does the headword need a sets button?

- *`needs_frequency_button`* `[bool]` does the headword need a frequency button?

- *`cf_set`* `[set]` set of all compound families in the database

- *`idioms_set`* `[set]` set of all the idioms in the database

- *`__repr__`* `[str]` quick overview of headword data

## Database Relationships

The `DpdHeadword` class has direct access to other tables in the database through relationships.

- `.rt` connects to the `dpd_roots` table
- `.fr` connects to the `family_roots` table
- `.fw` connects to the `family_words` table
- `.sbs` connects to the `SBS` table
- `.ru` connects to the `russian` table
- `.si` connects to the `sinhala` table
- `.it` connects to the `inflection_templates` table


