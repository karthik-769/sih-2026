import React, { useState, useEffect } from 'react';
import {
  Award,
  RefreshCw,
  TrendingUp,
  Shield,
  ShieldCheck,
  Target,
  BarChart3,
  Table,
  CheckCircle2,
  AlertTriangle,
  Flame,
  BrainCircuit,
  Layers,
  Activity,
} from 'lucide-react';
import { getAiEvaluationApi } from '../services/api';

export const AiAnalysisPage = () => {
  const [evaluationData, setEvaluationData] = useState(null);
  const [evaluationLoading, setEvaluationLoading] = useState(true);
  const [evaluationError, setEvaluationError] = useState('');

  const fetchEvaluation = async () => {
    setEvaluationLoading(true);
    setEvaluationError('');
    try {
      const data = await getAiEvaluationApi();
      setEvaluationData(data);
    } catch (err) {
      console.error('Failed to fetch AI evaluation metrics:', err);
      setEvaluationError('Failed to load evaluation metrics. Please ensure reports are available and backend is running.');
    } finally {
      setEvaluationLoading(false);
    }
  };

  useEffect(() => {
    fetchEvaluation();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Award className="w-6 h-6 text-indigo-600" />
            AI Safety Model Evaluation & Benchmark Intelligence
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Deterministic validation and quantitative benchmarking of the safety NLP pipeline against ground-truth incident records.
          </p>
        </div>

        <button
          onClick={fetchEvaluation}
          disabled={evaluationLoading}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold transition-all shadow-sm disabled:opacity-50 self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${evaluationLoading ? 'animate-spin' : ''}`} />
          {evaluationLoading ? 'Computing Metrics...' : 'Re-compute Evaluation'}
        </button>
      </div>

      {/* Top Model Info Card */}
      <div className="bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-white rounded-2xl p-6 shadow-md border border-slate-800">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/20 border border-indigo-400/30 text-indigo-200">
              <BrainCircuit className="w-3.5 h-3.5 text-indigo-400" />
              <span>AI Pipeline Model Verification & Performance Evaluation</span>
            </div>
            <h2 className="text-xl font-bold tracking-tight">
              Deterministic Safety NLP Pipeline Evaluation
            </h2>
            <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
              Evaluates AI predictions against ground-truth safety observations across SIF precursor classification, IOGP Life-Saving Rules mapping, and barrier intelligence.
            </p>
          </div>
        </div>

        {evaluationData && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6 pt-5 border-t border-slate-800 text-xs">
            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Evaluated Records</span>
              <span className="text-base font-bold font-mono text-white">
                {evaluationData.evaluated_records_count ?? 0} Reports
              </span>
            </div>

            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
              <span className="text-[11px] text-slate-400 block">Pipeline Version</span>
              <span className="text-base font-bold font-mono text-indigo-300">
                v{evaluationData.pipeline_version || '2.0.0'} ({evaluationData.model_name || 'Production'})
              </span>
            </div>

            <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60 col-span-2">
              <span className="text-[11px] text-slate-400 block">Semantic Embedding Provider</span>
              <span className="text-xs font-semibold text-emerald-300 truncate block">
                {evaluationData.embedding_provider || 'all-MiniLM-L6-v2 (Production)'}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Error Notice */}
      {evaluationError && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
          <span>{evaluationError}</span>
        </div>
      )}

      {/* Loading State */}
      {evaluationLoading && !evaluationData ? (
        <div className="p-12 text-center text-xs text-slate-500 bg-white rounded-xl border border-slate-200">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-600" />
          Computing evaluation against ground-truth validation records...
        </div>
      ) : evaluationData ? (
        <div className="space-y-6 animate-in fade-in">
          {/* SIF CLASSIFICATION METRICS */}
          {evaluationData.sif_classification && (
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <Flame className="w-5 h-5 text-rose-600" />
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
                      SIF Precursor Classification Performance
                    </h3>
                    <p className="text-[11px] text-slate-500">
                      True Positive, False Positive, Precision, Recall, and F1 Score calculated from actual inferences vs ground truth.
                    </p>
                  </div>
                </div>
                <span className="text-xs font-bold text-rose-700 bg-rose-50 border border-rose-200 px-2.5 py-1 rounded-lg">
                  F1 Score: {evaluationData.sif_classification.f1_score}%
                </span>
              </div>

              {/* Metric Summary Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-[11px] font-semibold text-slate-500 uppercase">Accuracy</span>
                  <div className="text-2xl font-black text-slate-900 mt-1">
                    {evaluationData.sif_classification.accuracy}%
                  </div>
                  <span className="text-[10px] text-slate-400">(TP + TN) / Total</span>
                </div>

                <div className="p-3.5 bg-indigo-50/50 rounded-xl border border-indigo-200">
                  <span className="text-[11px] font-semibold text-indigo-800 uppercase">Precision</span>
                  <div className="text-2xl font-black text-indigo-900 mt-1">
                    {evaluationData.sif_classification.precision}%
                  </div>
                  <span className="text-[10px] text-indigo-600">TP / (TP + FP)</span>
                </div>

                <div className="p-3.5 bg-purple-50/50 rounded-xl border border-purple-200">
                  <span className="text-[11px] font-semibold text-purple-800 uppercase">Recall</span>
                  <div className="text-2xl font-black text-purple-900 mt-1">
                    {evaluationData.sif_classification.recall}%
                  </div>
                  <span className="text-[10px] text-purple-600">TP / (TP + FN)</span>
                </div>

                <div className="p-3.5 bg-rose-50/50 rounded-xl border border-rose-200">
                  <span className="text-[11px] font-semibold text-rose-800 uppercase">F1 Score</span>
                  <div className="text-2xl font-black text-rose-900 mt-1">
                    {evaluationData.sif_classification.f1_score}%
                  </div>
                  <span className="text-[10px] text-rose-600">Harmonic Mean</span>
                </div>
              </div>

              {/* Confusion Counts & Class Performance */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                {/* Confusion Counts Matrix */}
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2 text-xs">
                  <h4 className="font-bold text-slate-800 flex items-center gap-1.5">
                    <Target className="w-4 h-4 text-slate-700" />
                    <span>SIF Binary Confusion Breakdown</span>
                  </h4>
                  <div className="grid grid-cols-2 gap-2 pt-1 font-mono text-[11px]">
                    <div className="p-2.5 bg-white rounded-lg border border-emerald-200">
                      <span className="text-slate-500 block text-[10px]">True Positives (TP)</span>
                      <span className="text-base font-bold text-emerald-700">
                        {evaluationData.sif_classification.true_positives}
                      </span>
                    </div>
                    <div className="p-2.5 bg-white rounded-lg border border-rose-200">
                      <span className="text-slate-500 block text-[10px]">False Positives (FP)</span>
                      <span className="text-base font-bold text-rose-700">
                        {evaluationData.sif_classification.false_positives}
                      </span>
                    </div>
                    <div className="p-2.5 bg-white rounded-lg border border-blue-200">
                      <span className="text-slate-500 block text-[10px]">True Negatives (TN)</span>
                      <span className="text-base font-bold text-blue-700">
                        {evaluationData.sif_classification.true_negatives}
                      </span>
                    </div>
                    <div className="p-2.5 bg-white rounded-lg border border-amber-200">
                      <span className="text-slate-500 block text-[10px]">False Negatives (FN)</span>
                      <span className="text-base font-bold text-amber-700">
                        {evaluationData.sif_classification.false_negatives}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Class Performance Table */}
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2 text-xs">
                  <h4 className="font-bold text-slate-800 flex items-center gap-1.5">
                    <Table className="w-4 h-4 text-slate-700" />
                    <span>Class Performance (SIF vs Non-SIF)</span>
                  </h4>
                  <div className="overflow-x-auto pt-1">
                    <table className="w-full text-left text-[11px]">
                      <thead>
                        <tr className="border-b border-slate-200 text-slate-500">
                          <th className="pb-1 font-semibold">Class</th>
                          <th className="pb-1 font-semibold">Precision</th>
                          <th className="pb-1 font-semibold">Recall</th>
                          <th className="pb-1 font-semibold">F1</th>
                          <th className="pb-1 font-semibold text-right">Support</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200">
                        {(evaluationData.sif_classification.class_performance || []).map((cp, idx) => (
                          <tr key={idx} className="hover:bg-slate-100/50">
                            <td className="py-2 font-medium text-slate-800">{cp.class_name}</td>
                            <td className="py-2 font-mono font-semibold text-slate-900">{cp.precision}%</td>
                            <td className="py-2 font-mono font-semibold text-slate-900">{cp.recall}%</td>
                            <td className="py-2 font-mono font-bold text-indigo-700">{cp.f1_score}%</td>
                            <td className="py-2 font-mono text-right text-slate-600">{cp.support}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* IOGP LIFE-SAVING RULES EVALUATION */}
          {evaluationData.life_saving_rules && (
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <Shield className="w-5 h-5 text-indigo-600" />
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
                      IOGP Life-Saving Rules Mapping Evaluation
                    </h3>
                    <p className="text-[11px] text-slate-500">
                      Rule-by-rule classification accuracy, macro metrics, and full multi-class confusion matrix.
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-indigo-800 bg-indigo-50 border border-indigo-200 px-2.5 py-1 rounded-lg">
                    Overall Accuracy: {evaluationData.life_saving_rules.accuracy}%
                  </span>
                  <span className="text-xs font-bold text-purple-800 bg-purple-50 border border-purple-200 px-2.5 py-1 rounded-lg">
                    Macro F1: {evaluationData.life_saving_rules.macro_f1}%
                  </span>
                </div>
              </div>

              {/* Rule-by-Rule Performance Table */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  Rule-by-Rule Performance Table
                </h4>
                <div className="overflow-x-auto rounded-xl border border-slate-200">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 text-[11px]">
                      <tr>
                        <th className="p-3">IOGP Life-Saving Rule</th>
                        <th className="p-3">Precision</th>
                        <th className="p-3">Recall</th>
                        <th className="p-3">F1 Score</th>
                        <th className="p-3">TP</th>
                        <th className="p-3">FP</th>
                        <th className="p-3">FN</th>
                        <th className="p-3 text-right">Support</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                      {(evaluationData.life_saving_rules.rule_performance || []).map((rp, idx) => (
                        <tr key={idx} className="hover:bg-slate-50/70 transition-colors">
                          <td className="p-3 font-sans font-bold text-slate-900 flex items-center gap-1.5">
                            <ShieldCheck className="w-3.5 h-3.5 text-indigo-600" />
                            <span>{rp.rule_name}</span>
                          </td>
                          <td className="p-3 font-semibold text-slate-900">{rp.precision}%</td>
                          <td className="p-3 font-semibold text-slate-900">{rp.recall}%</td>
                          <td className="p-3 font-black text-indigo-700">{rp.f1_score}%</td>
                          <td className="p-3 text-emerald-700 font-semibold">{rp.true_positives}</td>
                          <td className="p-3 text-rose-600 font-semibold">{rp.false_positives}</td>
                          <td className="p-3 text-amber-600 font-semibold">{rp.false_negatives}</td>
                          <td className="p-3 text-right font-sans text-slate-700">{rp.support}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Confusion Matrix (Actual vs Predicted) */}
              {evaluationData.life_saving_rules.confusion_matrix && (
                <div className="space-y-2 pt-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                    <BarChart3 className="w-4 h-4 text-indigo-600" />
                    <span>Confusion Matrix (Actual vs Predicted Life-Saving Rules)</span>
                  </h4>

                  <div className="overflow-x-auto p-4 bg-slate-50 rounded-xl border border-slate-200">
                    <table className="w-full text-center text-xs font-mono">
                      <thead>
                        <tr>
                          <th className="p-2 text-left font-sans text-[11px] text-slate-500 font-semibold">
                            Actual \ Predicted
                          </th>
                          {(evaluationData.life_saving_rules.confusion_matrix.labels || []).map((lbl, j) => (
                            <th key={j} className="p-2 text-[10px] font-bold text-slate-700 max-w-[100px] truncate" title={lbl}>
                              {lbl}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {(evaluationData.life_saving_rules.confusion_matrix.labels || []).map((rowLabel, i) => (
                          <tr key={i} className="border-t border-slate-200/80">
                            <td className="p-2 text-left font-sans font-bold text-slate-800 text-[11px] max-w-[140px] truncate" title={rowLabel}>
                              {rowLabel}
                            </td>
                            {(evaluationData.life_saving_rules.confusion_matrix.matrix?.[i] || []).map((count, j) => {
                              const isDiagonal = i === j;
                              return (
                                <td
                                  key={j}
                                  className={`p-2 font-bold rounded ${
                                    isDiagonal
                                      ? count > 0
                                        ? 'bg-emerald-100 text-emerald-900 border border-emerald-300'
                                        : 'text-slate-400'
                                      : count > 0
                                      ? 'bg-rose-100 text-rose-900 font-extrabold border border-rose-200'
                                      : 'text-slate-300'
                                  }`}
                                >
                                  {count}
                                </td>
                              );
                            })}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
};

export default AiAnalysisPage;
