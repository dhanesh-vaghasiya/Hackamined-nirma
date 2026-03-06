from typing import List
import importlib

from app.services.user_input.config import MODEL_NAME, SKILL_SIMILARITY_THRESHOLD


class SemanticSkillModel:
    def __init__(self) -> None:
        self._model = None
        self._util = None
        self._skills_cache: List[str] = []
        self._skill_embeddings = None
        self._load_error = None

        try:
            st_module = importlib.import_module("sentence_transformers")
            sentence_transformer = getattr(st_module, "SentenceTransformer")
            util = getattr(st_module, "util")
            self._model = sentence_transformer(MODEL_NAME)
            self._util = util
        except Exception as exc:  # pragma: no cover - runtime availability guard
            self._load_error = str(exc)

    @property
    def is_available(self) -> bool:
        return self._model is not None

    def _ensure_skill_embeddings(self, skills: List[str]) -> None:
        if not self.is_available:
            return
        normalized_skills = [skill.strip().lower() for skill in skills]
        if normalized_skills == self._skills_cache and self._skill_embeddings is not None:
            return
        self._skills_cache = normalized_skills
        self._skill_embeddings = self._model.encode(normalized_skills, convert_to_tensor=True)

    def extract_semantic_skills(
        self,
        text: str,
        skills: List[str],
        threshold: float = SKILL_SIMILARITY_THRESHOLD,
    ) -> List[str]:
        if not text or not self.is_available:
            return []

        self._ensure_skill_embeddings(skills)
        text_embedding = self._model.encode(text, convert_to_tensor=True)
        similarities = self._util.cos_sim(text_embedding, self._skill_embeddings)[0]

        detected = []
        for index, score in enumerate(similarities):
            if float(score) > threshold:
                detected.append(self._skills_cache[index])
        return detected


semantic_skill_model = SemanticSkillModel()
