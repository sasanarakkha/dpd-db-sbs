import json
from db.db_helpers import get_db_session
from tools.paths import ProjectPaths
from exporter.analysis.analyzer import analyze_sentence
from exporter.analysis.translate_core import _find_missing_score_groups

sentence = "anamataggo'yaṃ [anamataggāyaṃ] bhikkhave, saṃsāro. pubbā koṭi na paññāyati avijjānīvaraṇānaṃ sattānaṃ taṇhāsaṃyojanānaṃ sandhāvataṃ saṃsarataṃ. seyyathā'pi, bhikkhave, puriso yaṃ imasmiṃ jambudīpe tiṇakaṭṭhasākhāpalāsaṃ taṃ chetvā [tacchetvā (bahūsu)] ekajjhaṃ saṃharitvā caturaṅgulaṃ caturaṅgulaṃ ghaṭikaṃ katvā nikkhipeyya, ayaṃ me mātā, tassā me mātu ayaṃ mātā'ti, apariyādinnā'va [apariyādiṇṇā'va] bhikkhave, tassa purisassa mātumātaro assu, atha imasmiṃ jambudīpe tiṇakaṭṭhasākhāpalāsaṃ parikkhayaṃ pariyādānaṃ gaccheyya. taṃ kissa hetu? anamataggo'yaṃ, bhikkhave, saṃsāro. pubbā koṭi na paññāyati avijjānīvaraṇānaṃ sattānaṃ taṇhāsaṃyojanānaṃ sandhāvataṃ saṃsarataṃ. evaṃ dīgharattaṃ vo, bhikkhave, dukkhaṃ paccanubhūtaṃ tibbaṃ paccanubhūtaṃ byasanaṃ paccanubhūtaṃ, kaṭasī [kaṭasi kaṭā chavā sayan'ti etthā'ti kaṭasī] vaḍḍhitā. yāvañ'c'idaṃ, bhikkhave, alam'eva sabbasaṅkhāresu nibbindituṃ alaṃ virajjituṃ alaṃ vimuccitun'ti. paṭhamaṃ."

paths = ProjectPaths()
session = get_db_session(paths.dpd_db_path)
try:
    print("Running analyze_sentence...")
    analysis = analyze_sentence(sentence, session)
    print(f"Analysis got {len(analysis)} tokens.")
    missing = _find_missing_score_groups(analysis, {})
    print(f"Missing got {len(missing)} groups.")
    with open("scripts/dps_archive/missing_groups.json", "w", encoding="utf-8") as f:
        json.dump(missing, f, indent=2, ensure_ascii=False)
    print("Done writing to scripts/dps_archive/missing_groups.json")
finally:
    session.close()
