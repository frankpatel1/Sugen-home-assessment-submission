import json
from src.retriever import ICD11Retriever
from src.main import process_single_note
from src.llm import LLMCoder

retriever = ICD11Retriever()
llm = LLMCoder()

test_cases = [
    {"id": "test-empty", "text": ""},
    {"id": "test-punct", "text": "... ??? --- !!!"},
    {"id": "test-swahili", "text": "Mgonjwa ana homa kali na maumivu ya kichwa tangu siku tatu. Kupima damu: malaria falciparum trophozoites."},
    {"id": "test-french", "text": "Patient de 45 ans présentant une toux productive, fièvre à 39°C et douleur thoracique droite. Diagnostic: pneumonie aiguë."},
    {"id": "test-spanish", "text": "Paciente femenina con dolor al orinar y polaquiuria. Examen de orina positivo para infección urinaria."},
]

print("Running edge cases...")
for tc in test_cases:
    res = process_single_note(tc, retriever, llm)
    print(f"ID: {res['id']}")
    print(f"  Codes: {res['codes']}")
    print(f"  Titles: {[retriever.by_code[c]['title'] for c in res['codes']]}")
    assert len(res["codes"]) <= 3
    assert len(res["codes"]) > 0
    assert all(c in retriever.valid_codes for c in res["codes"])

print("All edge cases passed successfully!")

