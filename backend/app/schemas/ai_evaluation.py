from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class MetricScore(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1_score: float


class ClassPerformance(BaseModel):
    class_name: str
    precision: float
    recall: float
    f1_score: float
    support: int


class RulePerformance(BaseModel):
    rule_name: str
    precision: float
    recall: float
    f1_score: float
    support: int
    true_positives: int
    false_positives: int
    false_negatives: int


class ConfusionMatrixData(BaseModel):
    labels: List[str]
    matrix: List[List[int]]  # matrix[i][j] = actual label i, predicted label j


class SifClassificationMetrics(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    class_performance: List[ClassPerformance]


class LifeSavingRuleMetrics(BaseModel):
    accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    rule_performance: List[RulePerformance]
    confusion_matrix: ConfusionMatrixData


class AiEvaluationResponse(BaseModel):
    dataset_total_records: int
    evaluated_records_count: int
    pipeline_version: str
    model_name: str
    embedding_provider: str
    is_transformer_active: bool
    sif_classification: SifClassificationMetrics
    life_saving_rules: LifeSavingRuleMetrics
