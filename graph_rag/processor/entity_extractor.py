import logging

import spacy
from spacy.cli import download


def load_spacy_model(model_name: str):
    try:
        return spacy.load(model_name)
    except OSError:
        print(f"Downloading the {model_name} model...")
        download(model_name)
        return spacy.load(model_name)


class EntityExtractor:
    def __init__(self):
        self.nlp = load_spacy_model("en_core_web_sm")

    def extract_entities(self, text):
        logging.getLogger().info("Extracting entities started")
        doc = self.nlp(text)
        entities = {}
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = set()
            entities[ent.label_].add(ent.text)
        return {k: list(v) for k, v in entities.items()}
