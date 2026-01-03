from exporter.mcp.ai_pali_translate import build_system_prompt

def test_build_system_prompt():
    analysis = [
        {
            "word": "cakkavattī",
            "status": "found",
            "data": [
                {
                    "key": "25702_0",
                    "id": 25702,
                    "lemma_1": "cakkavattī",
                    "pos": "masc",
                    "grammar": "masc, agent, comp",
                    "meaning_combo": "emperor",
                    "construction": "cakka + vattī",
                    "components": []
                }
            ]
        }
    ]
    
    prompt = build_system_prompt(analysis)
    
    assert "expert Pāḷi translator" in prompt
    assert "cakkavattī" in prompt
    assert "JSON object" in prompt
    assert "selected_key" in prompt
    assert "unique `key`" in prompt
