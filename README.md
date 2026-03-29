# Task-Geometry Experiment Results

Public data release for the **task-geometry separability** experiment — alignment-drift detection via weight-space spectral features.

**Blog post:** [Task geometry phases 0–5: from drift POC to weights and harmfulness](https://roipaul.com/blog/task-geometry)

## What this experiment tests

Can weight-space geometry identify *which* fine-tuning objective drifted a model, not just that drift occurred? And does that geometric signature correlate with downstream behavioral harm?

**Model:** meta-llama/Llama-3.2-3B-Instruct, LoRA rank 8 on q_proj and v_proj.  
**Population:** 38 adapters (10 healthy SFT, 8 DPO inverted-harmlessness, 6 DPO inverted-helpfulness, 6 steering refusal-erosion, 4 OOD steering sycophancy).

## Key findings

- Within a DPO training regime, spectral features on LoRA weight deltas achieve AUC 1.00 for binary detection, 4-way objective classification, and all six pairwise comparisons.
- Ordinal severity ranking: Spearman rho > 0.95 across all three drift types.
- Cross-method generalization fails completely (AUC 0.00) — the detector learns "DPO-shaped change," not "bad change."
- q_proj encodes drift detection; v_proj encodes drift diagnosis (objective identity).
- PCA on weight deltas: PC1 is a pure objective axis (AUC 1.00), orthogonal to training duration.
- Geometry-to-behavior link: rho 0.72 between weight-space drift score and HEx-PHI attack success rate on 24 GPT-4o-verified adapters.

## Repository contents

```
PRE-REGISTRATION.md              — Pre-registered hypotheses (phases 0–4)
PRE-REGISTRATION-PHASE5-6.md     — Pre-registered hypotheses (phase 5)

exit-reports/
  EXPERIMENT-TASK-GEOMETRY-EXIT-REPORT.md  — Reviewed results (phases 0–4)
  PHASE5_EXIT_REPORT.md                   — Reviewed results (phase 5, harmfulness)
  PHASE0_RESULTS.md                       — Pre-flight analysis

results/
  spectral_feature_matrix.json    — Core dataset: per-layer spectral features, all 38 adapters
  manufacturing_labels.json       — Ground truth: adapter type, method, steps, severity
  binary_classification.json      — Healthy vs all-drifted classifier results
  multiclass_classification.json  — 4-way classifier results
  pairwise_separability.json      — All 6 pairwise AUC comparisons
  ordinal_correlation.json        — Spearman rho per drift type
  module_split_results.json       — q_proj vs v_proj vs both
  feature_split_results.json      — Magnitude vs shape vs all
  feature_importance.json         — Classifier coefficient analysis
  ood_evaluation.json             — Out-of-distribution (steering sycophancy) evaluation
  seed_variance.json              — Cross-seed reproducibility
  h3_revised_pca.json             — Weight-delta PCA (objective axis)
  h3_revised_probe_accuracy.json  — Activation-space probing
  h3_revised_alignment.json       — Weight-space vs activation-space alignment
  phase5_asr_matrix.json          — Per-adapter attack success rates (in harmfulness_eval/)
  phase5_spectral_drift_scores.json — Per-adapter drift probability
  phase5_correlation.json         — Geometry-behavior correlation
  *.png                           — Visualizations (UMAP, heatmaps, PCA scatter)

  spectral/                       — Per-adapter per-layer spectral feature JSONs
  harmfulness_eval/               — Per-adapter ASR summaries (HEx-PHI, AdvBench, StrongREJECT)
    gpt4o_calibration_hex-phi.json — GPT-4o calibration check
```

## What is NOT included

- **LoRA adapter weights** — the drifted adapters produce measurably more harmful outputs. The spectral features and ASR summaries are sufficient to verify all statistical claims.
- **Raw model responses** to harmful prompts — per-adapter summary statistics are included; response-level text is not.

## Citation

If you use this data, please cite the blog post and link to this repository.

## License

MIT
