"""
Text Processing Utility Module
================================
Provides NLP and text analysis utilities for construction project descriptions.

This module handles text cleaning, keyword extraction, TF-IDF vectorization,
and project categorization for the Alberta Procurement analytics app.

Author: BCXV Construction Analytics
Date: 2025-12-08
Phase: 3 - ML & Text Processing
"""

import re
import string
from typing import List, Dict, Tuple, Optional, Set
from collections import Counter
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# Construction-specific stopwords (common words to ignore)
CONSTRUCTION_STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
    'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'must', 'can', 'project', 'work', 'services',
    'supply', 'provide', 'providing', 'including', 'various', 'other',
    'request', 'proposals', 'rfp', 'rfq', 'tender', 'invitation'
}

# Domain-specific keyword categories for construction projects
CONSTRUCTION_CATEGORIES = {
    'Road & Highway': {
        'road', 'highway', 'street', 'avenue', 'boulevard', 'lane', 'drive',
        'pavement', 'asphalt', 'paving', 'overlay', 'resurfacing', 'gravel',
        'chip seal', 'seal coat', 'crack seal', 'line painting', 'markings',
        'traffic', 'intersection', 'roundabout', 'sidewalk', 'curb', 'gutter'
    },
    'Bridge & Structure': {
        'bridge', 'culvert', 'overpass', 'underpass', 'trestle', 'viaduct',
        'abutment', 'pier', 'deck', 'span', 'beam', 'girder', 'rehabilitation',
        'replacement', 'structural'
    },
    'Water & Wastewater': {
        'water', 'wastewater', 'sewer', 'sanitary', 'storm', 'drainage',
        'treatment', 'plant', 'wwtp', 'wtp', 'lagoon', 'lift station',
        'pump station', 'reservoir', 'tank', 'main', 'watermain', 'pipeline',
        'utility', 'infrastructure', 'hydrant'
    },
    'Electrical & Lighting': {
        'electrical', 'lighting', 'streetlight', 'power', 'hvac', 'mechanical',
        'heating', 'ventilation', 'air conditioning', 'generator', 'transformer',
        'switchgear', 'panel', 'wiring', 'led', 'fixture'
    },
    'Building & Facility': {
        'building', 'facility', 'construction', 'renovation', 'retrofit',
        'addition', 'expansion', 'interior', 'exterior', 'roof', 'roofing',
        'siding', 'window', 'door', 'flooring', 'ceiling', 'wall', 'drywall',
        'paint', 'hvac', 'plumbing', 'fire alarm', 'sprinkler', 'elevator'
    },
    'Park & Recreation': {
        'park', 'playground', 'trail', 'pathway', 'recreation', 'arena',
        'rink', 'pool', 'splash pad', 'sports', 'field', 'turf', 'landscaping',
        'irrigation', 'benches', 'shelters', 'picnic', 'gazebo'
    },
    'Environmental': {
        'environmental', 'erosion', 'remediation', 'contamination', 'soil',
        'groundwater', 'wetland', 'habitat', 'restoration', 'reclamation',
        'decommission', 'cleanup', 'hazardous', 'asbestos', 'assessment'
    }
}


class TextProcessor:
    """
    Handles text cleaning, preprocessing, and feature extraction
    for construction project descriptions.
    """

    def __init__(self, use_tfidf: bool = True):
        """
        Initialize text processor.

        Args:
            use_tfidf: Whether to use TF-IDF vectorization (default: True)
        """
        self.use_tfidf = use_tfidf
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix: Optional[np.ndarray] = None
        self.documents: List[str] = []
        self.document_ids: List[str] = []

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text for processing.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text in lowercase without special characters
        """
        if not text or pd.isna(text):
            return ""

        # Convert to string and lowercase
        text = str(text).lower()

        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)

        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)

        # Remove reference numbers like AB-2025-05281
        text = re.sub(r'ab-\d{4}-\d{5}', '', text)

        # Remove special characters but keep spaces
        text = re.sub(r'[^a-z0-9\s-]', ' ', text)

        # Remove extra whitespace
        text = ' '.join(text.split())

        return text

    def remove_stopwords(self, text: str) -> str:
        """
        Remove common stopwords from text.

        Args:
            text: Text to process

        Returns:
            Text with stopwords removed
        """
        words = text.split()
        filtered_words = [w for w in words if w not in CONSTRUCTION_STOPWORDS and len(w) > 2]
        return ' '.join(filtered_words)

    def extract_keywords(self, text: str, top_n: int = 10) -> List[Tuple[str, int]]:
        """
        Extract top keywords from text using frequency analysis.

        Args:
            text: Text to analyze
            top_n: Number of top keywords to return

        Returns:
            List of (keyword, frequency) tuples
        """
        cleaned = self.clean_text(text)
        filtered = self.remove_stopwords(cleaned)

        # Count word frequencies
        words = filtered.split()
        counter = Counter(words)

        return counter.most_common(top_n)

    def categorize_project(self, text: str) -> Dict[str, float]:
        """
        Categorize project based on keyword matching.

        Args:
            text: Project description text

        Returns:
            Dictionary of {category: confidence_score}
        """
        cleaned = self.clean_text(text)
        words = set(cleaned.split())

        scores = {}
        for category, keywords in CONSTRUCTION_CATEGORIES.items():
            # Count matching keywords
            matches = words.intersection(keywords)
            # Confidence based on number of matches and keyword rarity
            if matches:
                score = len(matches) / len(keywords) * 100
                scores[category] = round(score, 2)

        # Return sorted by score
        return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))

    def get_top_category(self, text: str) -> Optional[str]:
        """
        Get the single most likely category for a project.

        Args:
            text: Project description text

        Returns:
            Category name or None if no match
        """
        scores = self.categorize_project(text)
        if scores:
            return list(scores.keys())[0]
        return None

    def preprocess_for_similarity(self, text: str) -> str:
        """
        Preprocess text specifically for similarity comparison.

        Args:
            text: Raw text

        Returns:
            Processed text ready for vectorization
        """
        cleaned = self.clean_text(text)
        filtered = self.remove_stopwords(cleaned)
        return filtered

    def fit_tfidf(self, documents: List[str], document_ids: List[str]) -> None:
        """
        Fit TF-IDF vectorizer on a corpus of documents.

        Args:
            documents: List of text documents
            document_ids: Corresponding document identifiers (e.g., reference numbers)
        """
        # Preprocess all documents
        processed_docs = [self.preprocess_for_similarity(doc) for doc in documents]

        # Initialize and fit TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=500,  # Limit vocabulary size
            min_df=2,  # Ignore terms that appear in less than 2 documents
            max_df=0.8,  # Ignore terms that appear in more than 80% of documents
            ngram_range=(1, 2),  # Include unigrams and bigrams
            stop_words=None  # We already removed stopwords
        )

        self.tfidf_matrix = self.vectorizer.fit_transform(processed_docs)
        self.documents = documents
        self.document_ids = document_ids

    def find_similar(
        self,
        query_text: str,
        top_n: int = 10,
        min_similarity: float = 0.1
    ) -> List[Tuple[str, float]]:
        """
        Find documents most similar to query text.

        Args:
            query_text: Text to find similar documents for
            top_n: Number of results to return
            min_similarity: Minimum similarity threshold (0-1)

        Returns:
            List of (document_id, similarity_score) tuples
        """
        if self.vectorizer is None or self.tfidf_matrix is None:
            raise ValueError("Must call fit_tfidf() before find_similar()")

        # Preprocess and vectorize query
        processed_query = self.preprocess_for_similarity(query_text)
        query_vector = self.vectorizer.transform([processed_query])

        # Compute cosine similarity
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()

        # Get top N most similar (excluding exact matches at 1.0)
        similar_indices = []
        for idx in similarities.argsort()[::-1]:
            sim = similarities[idx]
            if sim >= min_similarity and sim < 0.999:  # Exclude exact self-matches
                similar_indices.append((idx, sim))
                if len(similar_indices) >= top_n:
                    break

        # Return document IDs with scores
        results = [
            (self.document_ids[idx], float(score))
            for idx, score in similar_indices
        ]

        return results

    def extract_features(self, text: str) -> Dict[str, any]:
        """
        Extract comprehensive features from project text.

        Args:
            text: Project description

        Returns:
            Dictionary of extracted features
        """
        features = {}

        # Basic stats
        features['text_length'] = len(text)
        features['word_count'] = len(text.split())

        # Top keywords
        keywords = self.extract_keywords(text, top_n=5)
        features['top_keywords'] = [kw for kw, _ in keywords]

        # Categories
        categories = self.categorize_project(text)
        features['categories'] = categories
        features['top_category'] = self.get_top_category(text)

        # Specific feature flags
        features['has_bridge'] = 'bridge' in text.lower()
        features['has_road'] = any(kw in text.lower() for kw in ['road', 'highway', 'street'])
        features['has_water'] = any(kw in text.lower() for kw in ['water', 'sewer', 'wastewater'])
        features['has_building'] = any(kw in text.lower() for kw in ['building', 'construction', 'renovation'])

        return features


def create_combined_text(row: pd.Series) -> str:
    """
    Combine title and description for better text analysis.

    Args:
        row: DataFrame row with 'short_title' and 'description' columns

    Returns:
        Combined text string
    """
    title = str(row.get('short_title', ''))
    desc = str(row.get('description', ''))

    # Weight title more heavily by repeating it
    combined = f"{title} {title} {desc}"
    return combined


# Convenience function for quick similarity search
def quick_similarity_search(
    target_text: str,
    corpus_df: pd.DataFrame,
    text_column: str = 'combined_text',
    id_column: str = 'reference_number',
    top_n: int = 10
) -> pd.DataFrame:
    """
    Quick helper function to find similar documents.

    Args:
        target_text: Text to find similar documents for
        corpus_df: DataFrame containing documents
        text_column: Column name containing text
        id_column: Column name containing document IDs
        top_n: Number of results to return

    Returns:
        DataFrame with similar documents and similarity scores
    """
    processor = TextProcessor()

    # Fit on corpus
    processor.fit_tfidf(
        documents=corpus_df[text_column].tolist(),
        document_ids=corpus_df[id_column].tolist()
    )

    # Find similar
    results = processor.find_similar(target_text, top_n=top_n)

    # Create results DataFrame
    if results:
        result_ids = [r[0] for r in results]
        result_scores = [r[1] for r in results]

        # Filter original DataFrame
        similar_df = corpus_df[corpus_df[id_column].isin(result_ids)].copy()

        # Add similarity scores
        score_map = dict(results)
        similar_df['similarity_score'] = similar_df[id_column].map(score_map)

        # Sort by similarity
        similar_df = similar_df.sort_values('similarity_score', ascending=False)

        return similar_df
    else:
        return pd.DataFrame()
