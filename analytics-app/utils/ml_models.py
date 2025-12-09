"""
Machine Learning Models Module
================================
Provides ML-powered bid prediction and project analysis.

Features:
- Bid amount prediction using Random Forest
- Feature engineering from project descriptions
- Model persistence and retraining
- Confidence intervals and prediction explanations

Author: BCXV Construction Analytics
Date: 2025-12-08
Phase: 3 - ML & Text Processing
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List, Optional
from pathlib import Path
import joblib
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score

from text_processing import TextProcessor


class BidPredictor:
    """
    Predicts likely winning bid amounts for construction projects
    using historical data and machine learning.
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize bid predictor.

        Args:
            model_path: Path to saved model file (optional)
        """
        self.model: Optional[RandomForestRegressor] = None
        self.region_encoder: Optional[LabelEncoder] = None
        self.category_encoder: Optional[LabelEncoder] = None
        self.feature_names: List[str] = []
        self.model_path = model_path
        self.is_trained = False

        # Text processor for feature extraction
        self.text_processor = TextProcessor()

        if model_path and Path(model_path).exists():
            self.load_model(model_path)

    def extract_features(self, row: pd.Series) -> Dict[str, float]:
        """
        Extract features from a project row for prediction.

        Args:
            row: DataFrame row with project information

        Returns:
            Dictionary of numeric features
        """
        features = {}

        # Text-based features
        combined_text = f"{row.get('short_title', '')} {row.get('description', '')}"
        text_features = self.text_processor.extract_features(combined_text)

        # Word count and length
        features['text_length'] = text_features['text_length']
        features['word_count'] = text_features['word_count']

        # Project type flags
        features['is_road_project'] = 1 if text_features['has_road'] else 0
        features['is_bridge_project'] = 1 if text_features['has_bridge'] else 0
        features['is_water_project'] = 1 if text_features['has_water'] else 0
        features['is_building_project'] = 1 if text_features['has_building'] else 0

        # Numeric features
        features['num_bidders'] = row.get('num_bidders', 5)  # Default to average

        # Region encoding (will be handled separately)
        features['region'] = row.get('region', 'Unknown')

        # Value estimate (if available)
        if 'actual_value' in row and pd.notna(row['actual_value']):
            features['estimated_value'] = row['actual_value']
        else:
            # Use average bid if available
            if 'average_bid' in row and pd.notna(row['average_bid']):
                features['estimated_value'] = row['average_bid']
            else:
                features['estimated_value'] = 1000000  # Default estimate

        return features

    def prepare_features(self, df: pd.DataFrame, fit_encoders: bool = False) -> pd.DataFrame:
        """
        Prepare feature matrix from DataFrame.

        Args:
            df: DataFrame with project information
            fit_encoders: Whether to fit label encoders (True for training)

        Returns:
            DataFrame with numeric features ready for ML
        """
        # Extract features for each row
        feature_dicts = []
        for idx, row in df.iterrows():
            features = self.extract_features(row)
            feature_dicts.append(features)

        features_df = pd.DataFrame(feature_dicts)

        # Encode region
        if fit_encoders:
            self.region_encoder = LabelEncoder()
            features_df['region_encoded'] = self.region_encoder.fit_transform(features_df['region'].fillna('Unknown'))
        else:
            if self.region_encoder:
                # Handle unseen regions
                known_regions = set(self.region_encoder.classes_)
                features_df['region_encoded'] = features_df['region'].apply(
                    lambda x: self.region_encoder.transform([x])[0] if x in known_regions else -1
                )
            else:
                features_df['region_encoded'] = 0

        # Drop non-numeric columns
        features_df = features_df.drop(['region'], axis=1)

        return features_df

    def train(self, training_data: pd.DataFrame, target_column: str = 'actual_value') -> Dict[str, float]:
        """
        Train the bid prediction model.

        Args:
            training_data: DataFrame with historical project data
            target_column: Column name containing actual award values

        Returns:
            Dictionary with training metrics
        """
        # Prepare features
        X = self.prepare_features(training_data, fit_encoders=True)
        y = training_data[target_column]

        # Remove rows with missing targets
        valid_mask = y.notna() & (y > 0)
        X = X[valid_mask]
        y = y[valid_mask]

        if len(X) < 10:
            raise ValueError("Insufficient training data. Need at least 10 samples.")

        # Store feature names
        self.feature_names = X.columns.tolist()

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Train Random Forest model
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )

        self.model.fit(X_train, y_train)
        self.is_trained = True

        # Evaluate
        train_preds = self.model.predict(X_train)
        test_preds = self.model.predict(X_test)

        metrics = {
            'train_mae': mean_absolute_error(y_train, train_preds),
            'test_mae': mean_absolute_error(y_test, test_preds),
            'train_r2': r2_score(y_train, train_preds),
            'test_r2': r2_score(y_test, test_preds),
            'n_samples': len(X),
            'n_features': len(self.feature_names)
        }

        # Cross-validation
        cv_scores = cross_val_score(
            self.model, X, y,
            cv=5,
            scoring='neg_mean_absolute_error'
        )
        metrics['cv_mae'] = -cv_scores.mean()
        metrics['cv_mae_std'] = cv_scores.std()

        return metrics

    def predict(
        self,
        project_data: pd.DataFrame,
        confidence_level: float = 0.9
    ) -> Dict[str, any]:
        """
        Predict winning bid amount for a project.

        Args:
            project_data: DataFrame with project information (single row or multiple)
            confidence_level: Confidence level for prediction interval

        Returns:
            Dictionary with prediction, confidence interval, and similar projects
        """
        if not self.is_trained or self.model is None:
            raise ValueError("Model must be trained before prediction")

        # Prepare features
        X = self.prepare_features(project_data, fit_encoders=False)

        # Make predictions
        predictions = self.model.predict(X)

        # Estimate prediction interval using individual tree predictions
        tree_predictions = np.array([tree.predict(X) for tree in self.model.estimators_])
        prediction_std = tree_predictions.std(axis=0)

        # Calculate confidence interval (assuming normal distribution)
        from scipy import stats
        z_score = stats.norm.ppf((1 + confidence_level) / 2)

        lower_bound = predictions - (z_score * prediction_std)
        upper_bound = predictions + (z_score * prediction_std)

        # Feature importance
        feature_importance = dict(zip(
            self.feature_names,
            self.model.feature_importances_
        ))

        # Sort by importance
        feature_importance = dict(sorted(
            feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        ))

        return {
            'predicted_value': predictions[0] if len(predictions) == 1 else predictions.tolist(),
            'lower_bound': lower_bound[0] if len(lower_bound) == 1 else lower_bound.tolist(),
            'upper_bound': upper_bound[0] if len(upper_bound) == 1 else upper_bound.tolist(),
            'prediction_std': prediction_std[0] if len(prediction_std) == 1 else prediction_std.tolist(),
            'confidence_level': confidence_level,
            'feature_importance': feature_importance
        }

    def save_model(self, filepath: str) -> None:
        """
        Save trained model to disk.

        Args:
            filepath: Path to save model
        """
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")

        model_data = {
            'model': self.model,
            'region_encoder': self.region_encoder,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained
        }

        joblib.dump(model_data, filepath)

    def load_model(self, filepath: str) -> None:
        """
        Load trained model from disk.

        Args:
            filepath: Path to saved model
        """
        model_data = joblib.load(filepath)

        self.model = model_data['model']
        self.region_encoder = model_data['region_encoder']
        self.feature_names = model_data['feature_names']
        self.is_trained = model_data['is_trained']


def quick_prediction(
    project_description: str,
    estimated_value: float,
    region: str,
    num_bidders: int,
    training_data: pd.DataFrame
) -> Dict[str, any]:
    """
    Quick helper function for bid prediction.

    Args:
        project_description: Project title and description
        estimated_value: Estimated project value
        region: Project region
        num_bidders: Expected number of bidders
        training_data: Historical data for training

    Returns:
        Prediction results dictionary
    """
    # Create project data row
    project_row = pd.DataFrame([{
        'short_title': project_description[:100],
        'description': project_description,
        'actual_value': estimated_value,
        'region': region,
        'num_bidders': num_bidders
    }])

    # Train model
    predictor = BidPredictor()
    predictor.train(training_data)

    # Make prediction
    result = predictor.predict(project_row)

    return result


def get_prediction_explanation(prediction_result: Dict) -> str:
    """
    Generate human-readable explanation of prediction.

    Args:
        prediction_result: Result dictionary from predict()

    Returns:
        Formatted explanation string
    """
    pred = prediction_result['predicted_value']
    lower = prediction_result['lower_bound']
    upper = prediction_result['upper_bound']
    conf = prediction_result['confidence_level']

    explanation = f"""
    **Predicted Winning Bid**: ${pred:,.0f}

    **{conf*100:.0f}% Confidence Interval**: ${lower:,.0f} - ${upper:,.0f}

    This means there is a {conf*100:.0f}% chance the winning bid will fall within this range
    based on similar historical projects.

    **Key Factors Influencing Prediction**:
    """

    # Add top features
    top_features = list(prediction_result['feature_importance'].items())[:5]
    for feat, importance in top_features:
        explanation += f"\n- {feat.replace('_', ' ').title()}: {importance*100:.1f}% importance"

    return explanation
