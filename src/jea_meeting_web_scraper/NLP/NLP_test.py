"""src/nlp/NLP_test.py"""

import spacy

nlp = spacy.load("en_core_web_sm")
doc = nlp("The JEA board approved a $2 million stormwater rehabilitation project for downtown Jacksonville.")

for ent in doc.ents:
    print(ent.text, ent.label_)
