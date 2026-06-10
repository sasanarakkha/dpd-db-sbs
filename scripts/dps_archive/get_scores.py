import json
from db.db_helpers import get_db_session
from tools.paths import ProjectPaths
from exporter.analysis.translate_core import translate_sentence
from tools.ai_manager import AIManager

sentence = "anamataggo'yaṃ [anamataggāyaṃ] bhikkhave, saṃsāro. pubbā koṭi na paññāyati avijjānīvaraṇānaṃ sattānaṃ taṇhāsaṃyojanānaṃ sandhāvataṃ saṃsarataṃ. seyyathā'pi, bhikkhave, puriso yaṃ imasmiṃ jambudīpe tiṇakaṭṭhasākhāpalāsaṃ taṃ chetvā [tacchetvā (bahūsu)] ekajjhaṃ saṃharitvā caturaṅgulaṃ caturaṅgulaṃ ghaṭikaṃ katvā nikkhipeyya, ayaṃ me mātā, tassā me mātu ayaṃ mātā'ti, apariyādinnā'va [apariyādiṇṇā'va] bhikkhave, tassa purisassa mātumātaro assu, atha imasmiṃ jambudīpe tiṇakaṭṭhasākhāpalāsaṃ parikkhayaṃ pariyādānaṃ gaccheyya. taṃ kissa hetu? anamataggo'yaṃ, bhikkhave, saṃsāro. pubbā koṭi na paññāyati avijjānīvaraṇānaṃ sattānaṃ taṇhāsaṃyojanānaṃ sandhāvataṃ saṃsarataṃ. evaṃ dīgharattaṃ vo, bhikkhave, dukkhaṃ paccanubhūtaṃ tibbaṃ paccanubhūtaṃ byasanaṃ paccanubhūtaṃ, kaṭasī [kaṭasi kaṭā chavā sayan'ti etthā'ti kaṭasī] vaḍḍhitā. yāvañ'c'idaṃ, bhikkhave, alam'eva sabbasaṅkhāresu nibbindituṃ alaṃ virajjituṃ alaṃ vimuccitun'ti. paṭhamaṃ."

paths = ProjectPaths()
session = get_db_session(paths.dpd_db_path)
ai_manager = AIManager()

debug = {}
try:
    print("Calling translate_sentence with debug enabled...")
    merged = translate_sentence(
        sentence, session, ai_manager=ai_manager, debug=debug, verbose=True
    )
    print("Success!")
    with open("scripts/dps_archive/final_scores.json", "w", encoding="utf-8") as f:
        json.dump(debug.get("final_scores", {}), f, indent=2, ensure_ascii=False)
    print("Saved to scripts/dps_archive/final_scores.json")
except Exception:
    import traceback

    print("Error occurred:")
    traceback.print_exc()
finally:
    session.close()
