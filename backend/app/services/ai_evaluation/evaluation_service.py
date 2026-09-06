import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.safety_report import SafetyReport
from app.models.ai_analysis import AiAnalysis
from app.ai.pipeline import AiAnalysisPipeline
from app.ai.similarity.service import SemanticEmbeddingProvider
from app.schemas.ai_evaluation import (
    MetricScore,
    ClassPerformance,
    RulePerformance,
    ConfusionMatrixData,
    SifClassificationMetrics,
    LifeSavingRuleMetrics,
    AiEvaluationResponse,
)

logger = logging.getLogger(__name__)


class AiEvaluationService:
    """
    NLP & AI Evaluation Engine for Safety Intelligence.
    Computes genuine, non-fabricated performance metrics:
    - SIF Classification: TP, TN, FP, FN, Precision, Recall, F1, Accuracy, Class breakdown
    - IOGP Life-Saving Rules: Accuracy, Macro Precision, Macro Recall, Macro F1, Rule-by-rule metrics, Confusion Matrix
    - Pipeline Metadata: active model version & embedding provider status.
    """

    def __init__(self, pipeline: Optional[AiAnalysisPipeline] = None):
        self.pipeline = pipeline or AiAnalysisPipeline()

    def evaluate(self, db: Session) -> AiEvaluationResponse:
        """
        Runs comprehensive evaluation against ground-truth labeled reports in the database,
        falling back to live evaluation on standard benchmark dataset if DB has insufficient labels.
        """
        # 1. Fetch DB reports with ground truth and AI analysis
        records = (
            db.query(SafetyReport, AiAnalysis)
            .outerjoin(AiAnalysis, SafetyReport.id == AiAnalysis.report_id)
            .all()
        )

        total_db_records = len(records)
        
        # Ground truth pairs: (actual_sif, pred_sif, actual_lsr, pred_lsr)
        eval_pairs: List[Tuple[bool, bool, Optional[str], Optional[str]]] = []

        for r, ai in records:
            # Check if ground truth SIF label is available
            actual_sif = None
            if r.is_sif is not None:
                actual_sif = bool(r.is_sif)
            elif r.fatality_potential is not None and r.incident_type in ["NEAR_MISS", "UNSAFE_ACT", "UNSAFE_CONDITION"]:
                # Near-miss with fatality potential is a SIF precursor
                actual_sif = bool(r.fatality_potential)

            if actual_sif is None and not r.life_saving_rule:
                continue

            if not ai:
                continue

            pred_sif = bool(ai.sif_precursor or ai.sif_detected or (ai.sif_level in ["HIGH", "CRITICAL"]))
            actual_lsr = r.life_saving_rule.strip() if r.life_saving_rule else None
            pred_lsr = ai.life_saving_rule.strip() if ai.life_saving_rule else None

            if actual_sif is not None or actual_lsr is not None:
                eval_pairs.append((actual_sif if actual_sif is not None else False, pred_sif, actual_lsr, pred_lsr))

        # 2. If fewer than 20 labeled records in DB, augment with live benchmark evaluation
        if len(eval_pairs) < 20:
            try:
                from samples.generate_oil_dataset import generate_oil_dataset
                benchmark_data = generate_oil_dataset(count=200, target_sif_density=0.20)
                for item in benchmark_data:
                    full_text = f"{item['task']}. {item['description']}"
                    # Inference with ZERO ground-truth context
                    res = self.pipeline.process(full_text, context={
                        "job_role": item["job_role"],
                        "task": item["task"],
                        "incident_type": item["incident_type"],
                    })
                    actual_sif = bool(item["is_sif"])
                    pred_sif = bool(res.sif_precursor or res.sif_detected or (res.sif_level in ["HIGH", "CRITICAL"]))
                    actual_lsr = item.get("life_saving_rule")
                    pred_lsr = res.life_saving_rule
                    eval_pairs.append((actual_sif, pred_sif, actual_lsr, pred_lsr))
            except Exception as e:
                logger.warning(f"Could not load benchmark dataset for evaluation: {e}")

        evaluated_count = len(eval_pairs)

        # 3. Compute SIF Classification Metrics
        tp = sum(1 for actual, pred, _, _ in eval_pairs if actual is True and pred is True)
        fp = sum(1 for actual, pred, _, _ in eval_pairs if actual is False and pred is True)
        tn = sum(1 for actual, pred, _, _ in eval_pairs if actual is False and pred is False)
        fn = sum(1 for actual, pred, _, _ in eval_pairs if actual is True and pred is False)

        sif_total = tp + fp + tn + fn
        sif_acc = round(((tp + tn) / max(sif_total, 1)) * 100.0, 1)
        sif_prec = round((tp / max(tp + fp, 1)) * 100.0, 1) if (tp + fp) > 0 else 0.0
        sif_rec = round((tp / max(tp + fn, 1)) * 100.0, 1) if (tp + fn) > 0 else 0.0
        sif_f1 = round((2 * sif_prec * sif_rec / max(sif_prec + sif_rec, 0.001)), 1) if (sif_prec + sif_rec) > 0 else 0.0

        # Class Performance: SIF Precursors vs Non-SIF Reports
        non_sif_prec = round((tn / max(tn + fn, 1)) * 100.0, 1) if (tn + fn) > 0 else 0.0
        non_sif_rec = round((tn / max(tn + fp, 1)) * 100.0, 1) if (tn + fp) > 0 else 0.0
        non_sif_f1 = round((2 * non_sif_prec * non_sif_rec / max(non_sif_prec + non_sif_rec, 0.001)), 1) if (non_sif_prec + non_sif_rec) > 0 else 0.0

        class_perf = [
            ClassPerformance(
                class_name="SIF Precursor (Positive)",
                precision=sif_prec,
                recall=sif_rec,
                f1_score=sif_f1,
                support=tp + fn,
            ),
            ClassPerformance(
                class_name="Non-SIF Observation (Negative)",
                precision=non_sif_prec,
                recall=non_sif_rec,
                f1_score=non_sif_f1,
                support=tn + fp,
            ),
        ]

        sif_metrics = SifClassificationMetrics(
            accuracy=sif_acc,
            precision=sif_prec,
            recall=sif_rec,
            f1_score=sif_f1,
            true_positives=tp,
            false_positives=fp,
            true_negatives=tn,
            false_negatives=fn,
            class_performance=class_perf,
        )

        # 4. Compute IOGP Life-Saving Rules Metrics & Confusion Matrix
        lsr_pairs = [(act_lsr, pred_lsr or "Unmapped") for _, _, act_lsr, pred_lsr in eval_pairs if act_lsr]
        lsr_total = len(lsr_pairs)

        lsr_correct = sum(1 for act, pred in lsr_pairs if act == pred)
        lsr_acc = round((lsr_correct / max(lsr_total, 1)) * 100.0, 1)

        # Get unique rule names present
        all_rules_set = sorted(list({act for act, _ in lsr_pairs} | {pred for _, pred in lsr_pairs if pred != "Unmapped"}))
        if not all_rules_set:
            all_rules_set = ["Energy Isolation", "Confined Space", "Work at Height", "Line of Fire", "Hot Work"]

        rule_performances: List[RulePerformance] = []
        precisions: List[float] = []
        recalls: List[float] = []
        f1s: List[float] = []

        for rule in all_rules_set:
            r_tp = sum(1 for act, pred in lsr_pairs if act == rule and pred == rule)
            r_fp = sum(1 for act, pred in lsr_pairs if act != rule and pred == rule)
            r_fn = sum(1 for act, pred in lsr_pairs if act == rule and pred != rule)
            r_supp = sum(1 for act, _ in lsr_pairs if act == rule)

            r_prec = round((r_tp / max(r_tp + r_fp, 1)) * 100.0, 1) if (r_tp + r_fp) > 0 else 0.0
            r_rec = round((r_tp / max(r_tp + r_fn, 1)) * 100.0, 1) if (r_tp + r_fn) > 0 else 0.0
            r_f1 = round((2 * r_prec * r_rec / max(r_prec + r_rec, 0.001)), 1) if (r_prec + r_rec) > 0 else 0.0

            if r_supp > 0 or (r_tp + r_fp) > 0:
                precisions.append(r_prec)
                recalls.append(r_rec)
                f1s.append(r_f1)

            rule_performances.append(
                RulePerformance(
                    rule_name=rule,
                    precision=r_prec,
                    recall=r_rec,
                    f1_score=r_f1,
                    support=r_supp,
                    true_positives=r_tp,
                    false_positives=r_fp,
                    false_negatives=r_fn,
                )
            )

        # Sort rule performance by support
        rule_performances.sort(key=lambda x: x.support, reverse=True)

        macro_prec = round(sum(precisions) / max(len(precisions), 1), 1) if precisions else 0.0
        macro_rec = round(sum(recalls) / max(len(recalls), 1), 1) if recalls else 0.0
        macro_f1 = round(sum(f1s) / max(len(f1s), 1), 1) if f1s else 0.0

        # Build 2D Confusion Matrix
        # Top 6 most prominent rules for clean visual representation
        top_matrix_labels = [rp.rule_name for rp in rule_performances[:6]]
        if "Other / Unmapped" not in top_matrix_labels:
            top_matrix_labels.append("Other / Unmapped")

        matrix_2d: List[List[int]] = []
        for act_label in top_matrix_labels:
            row: List[int] = []
            for pred_label in top_matrix_labels:
                count = 0
                for act, pred in lsr_pairs:
                    mapped_act = act if act in top_matrix_labels else "Other / Unmapped"
                    mapped_pred = pred if pred in top_matrix_labels else "Other / Unmapped"
                    if mapped_act == act_label and mapped_pred == pred_label:
                        count += 1
                row.append(count)
            matrix_2d.append(row)

        confusion_matrix = ConfusionMatrixData(
            labels=top_matrix_labels,
            matrix=matrix_2d,
        )

        lsr_metrics = LifeSavingRuleMetrics(
            accuracy=lsr_acc,
            macro_precision=macro_prec,
            macro_recall=macro_rec,
            macro_f1=macro_f1,
            rule_performance=rule_performances,
            confusion_matrix=confusion_matrix,
        )

        # 5. Model & Provider Status
        is_transformer = SemanticEmbeddingProvider._is_transformer
        embedding_provider_name = (
            "SentenceTransformer (all-MiniLM-L6-v2) Dense Embeddings"
            if is_transformer
            else "Domain-Specific Feature Vector Provider (Deterministic Fallback)"
        )

        return AiEvaluationResponse(
            dataset_total_records=total_db_records,
            evaluated_records_count=evaluated_count,
            pipeline_version=self.pipeline.VERSION,
            model_name=self.pipeline.MODEL_NAME,
            embedding_provider=embedding_provider_name,
            is_transformer_active=is_transformer,
            sif_classification=sif_metrics,
            life_saving_rules=lsr_metrics,
        )


ai_evaluation_service = AiEvaluationService()
