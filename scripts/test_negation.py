import re

def strip_negations(text: str) -> str:
    # Remove phrases like "mrdt neg", "malaria excluded", "no cough, no vomiting", etc.
    # 1. Test results negative
    text = re.sub(r"\b(?:mrdt|rdt|bs|mps|malaria|tb|hiv|upt)\s*(?:is\s*)?(?:neg(?:ative)?|\-|\b0\b)", " ", text, flags=re.IGNORECASE)
    # 2. Disease excluded
    text = re.sub(r"\b\w+\s+excluded\b", " ", text, flags=re.IGNORECASE)
    # 3. "no <terms>" up to punctuation
    text = re.sub(r"\b(?:no|denies|without|ruled\s+out|not)\s+[^,\.;\n]+", " ", text, flags=re.IGNORECASE)
    return text

sample = "S: 28M boda rider c/o fever with chills and rigors x3/7, frontal headache, generalised body aches. No vomiting, no convulsions, no confusion. No cough. Dx viral URTI, malaria excluded."
print("Original:", sample)
print("Stripped:", strip_negations(sample))
