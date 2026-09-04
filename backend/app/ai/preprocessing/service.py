import re
from typing import Dict, Any, Optional
from app.ai.interfaces import BasePreprocessor, PreprocessedText


class PreprocessingService(BasePreprocessor):
    """
    Text normalization, linguistic cleaning, tokenization, phrase boundary detection,
    and metadata extraction for the safety intelligence pipeline.
    """

    def preprocess(self, text: str, context: Optional[Dict[str, Any]] = None) -> PreprocessedText:
        if not text:
            return PreprocessedText(raw_text="", cleaned_text="", tokens=[], phrases=[], keywords=[], metadata={})

        raw = text.strip()
        # Clean synthetic/boilerplate tokens while keeping observational content
        cleaned = re.sub(r'\[SYNTHETIC DEMO DATA\]', '', raw, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        # Extract sentences / semantic clauses
        phrases = [p.strip() for p in re.split(r'[.,;\n]+', cleaned) if p.strip()]

        # Tokenize words
        tokens = [t.lower() for t in re.findall(r'\b[a-zA-Z0-9_\-]+\b', cleaned)]

        # Extract stopword-filtered keywords
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'from', 'up', 'about', 'into', 'over', 'after', 'is', 'was', 'are', 'were', 'been', 'be',
            'have', 'has', 'had', 'do', 'does', 'did', 'while', 'as', 'it', 'this', 'that', 'these',
            'they', 'them', 'their', 'we', 'our', 'i', 'my', 'you', 'your', 'which', 'who', 'whom'
        }
        keywords = [t for t in tokens if len(t) > 2 and t not in stopwords]

        metadata = {
            "token_count": len(tokens),
            "keyword_count": len(keywords),
            "phrase_count": len(phrases),
            "character_count": len(cleaned),
            "context_supplied": bool(context),
        }

        return PreprocessedText(
            raw_text=raw,
            cleaned_text=cleaned,
            tokens=tokens,
            phrases=phrases,
            keywords=keywords,
            metadata=metadata,
        )
