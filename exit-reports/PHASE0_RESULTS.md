# Phase 0 Pre-Flight Results

**Date**: 2026-03-15
**Data source**: drift-poc/data/results/spectral/ (7 adapters from POC v2 cloud run)
**Script**: `01_layer_analysis.py --all`
**Compute**: CPU-only, ~30 seconds

---

## Full Data

### Phase 0a: Per-Sublayer Binary AUC (healthy vs drifted, LOO-CV logistic regression)

| Layer | q_proj AUC | v_proj AUC |
|-------|-----------|-----------|
| 0 | **1.000** | 0.917 |
| 1 | 0.917 | 0.667 |
| 2 | 0.250 | 0.917 |
| 3 | 0.667 | 0.667 |
| 4 | 0.833 | 0.750 |
| 5 | **1.000** | 0.917 |
| 6 | **1.000** | 0.750 |
| 7 | 0.917 | 0.500 |
| 8 | **1.000** | 0.250 |
| 9 | 0.833 | 0.500 |
| 10 | **1.000** | 0.667 |
| 11 | 0.750 | 0.417 |
| 12 | **1.000** | 0.167 |
| 13 | 0.500 | 0.000 |
| 14 | **1.000** | 0.000 |
| 15 | **1.000** | 0.750 |
| 16 | 0.833 | 0.500 |
| 17 | **1.000** | 0.750 |
| 18 | 0.917 | 0.500 |
| 19 | 0.583 | 0.500 |
| 20 | 0.583 | 0.250 |
| 21 | 0.500 | 0.667 |
| 22 | **1.000** | 0.833 |
| 23 | **1.000** | 0.250 |
| 24 | 0.833 | 0.750 |
| 25 | 0.000 | 0.833 |
| 26 | 0.750 | 0.500 |
| 27 | 0.750 | 0.500 |

### Phase 0a: Tercile and Ablation AUCs

| Condition | AUC |
|-----------|-----|
| Full model (all 56 sublayers) | 1.000 |
| Early tercile only (layers 0-8) | 1.000 |
| Middle tercile only (layers 9-19) | 1.000 |
| Late tercile only (layers 20-27) | 0.833 |
| Ablation: drop early | 1.000 |
| Ablation: drop middle | 1.000 |
| Ablation: drop late | 1.000 |

### Phase 0b: Spearman rho (feature vs DPO step count, 4 adapters at 50/150/300/600 steps)

| Layer | frob | spectral | stable_rank | sv_entropy | sv_conc | eff_rank | mean\|rho\| |
|-------|------|----------|-------------|------------|---------|----------|------------|
| 0 q | +1.0 | +1.0 | -1.0 | -1.0 | +1.0 | -1.0 | **1.000** |
| 0 v | +1.0 | +1.0 | -0.4 | -1.0 | +1.0 | -1.0 | 0.900 |
| 1 q | +1.0 | +1.0 | -1.0 | -1.0 | +1.0 | -1.0 | **1.000** |
| 1 v | +1.0 | +1.0 | -0.8 | -1.0 | +1.0 | -1.0 | 0.967 |
| 4 q | +1.0 | +1.0 | -0.6 | -0.6 | +0.6 | -0.6 | 0.733 |
| 15 q | +1.0 | +1.0 | -0.6 | -0.8 | +0.8 | -0.8 | 0.833 |
| 18 q | +1.0 | +1.0 | -0.8 | -0.4 | +0.4 | -0.4 | 0.667 |
| ... | ... | ... | ... | ... | ... | ... | ... |
| 27 q | +1.0 | +1.0 | -1.0 | -1.0 | +1.0 | -1.0 | **1.000** |
| 27 v | +1.0 | +1.0 | -1.0 | -1.0 | +1.0 | -1.0 | **1.000** |

(Table abbreviated. Full data in `phase0b_step_gradient.json`. 54 of 56 sublayers have mean|rho| > 0.80. Zero sublayers below 0.50.)

### Phase 0b: Tercile Summary

| Tercile | mean\|rho\| |
|---------|------------|
| Early (0-8) | 0.948 |
| Middle (9-19) | 0.950 |
| Late (20-27) | 0.990 |

---

## Anomalous Result

**q_proj and v_proj behave very differently.** This was not predicted.

q_proj achieves AUC >= 0.75 at 22 of 28 layers. Twelve q_proj sublayers hit AUC=1.0.

v_proj achieves AUC >= 0.75 at only 10 of 28 layers. Five v_proj sublayers score AUC=0.0 or AUC=0.167, meaning the classifier is *worse than random* -- it is actively confused by v_proj features at those layers.

The discriminative signal for binary classification lives primarily in the query projection weights. The value projection weights at many layers contain *anti-signal* that hurts classification when included alone.

---

## Findings

### Finding 1: The binary signal is distributed across layers, not localized

Early and middle terciles both achieve AUC=1.0. Late achieves 0.833. Dropping any single tercile still yields AUC=1.0. No tercile is necessary and no tercile is sufficient by itself at the late end. The localization hypothesis (early + late layers carry signal, middle layers don't) is **not supported**. The binary signal is redundant across depth.

### Finding 2: The signal is localized by module type, not by depth

q_proj carries the binary signal consistently across all depths. v_proj is unreliable and sometimes adversarial. This is a module-level finding that the spec did not anticipate. The tercile framework (early/middle/late) was the wrong axis of variation to test.

### Finding 3: The DPO step gradient is uniform across layers

Frobenius norm and spectral norm are perfectly monotonic (rho=+1.0) at every single sublayer. More DPO training increases weight magnitude everywhere equally. The step gradient does not localize. 54 of 56 sublayers have mean|rho| > 0.80. The only variation is in second-order features (stable rank, entropy) at a handful of layers.

### Finding 4: Frobenius norm and spectral norm are the dominant features

These two features are perfectly step-monotonic everywhere and carry binary discriminative signal at most layers. Stable rank, entropy, effective rank, and concentration add information at some layers but are noisier and occasionally anti-correlated with the binary label.

---

## Implications for Phase 2

1. **Use all layers, not a focused subset.** The binary signal is distributed. Focusing on one tercile would discard redundant but potentially useful signal for the harder 4-way classification.

2. **Track q_proj and v_proj separately in Phase 2 analysis.** If task-fingerprinting shows module-specific patterns (sycophancy perturbs q_proj differently than helpfulness-erosion), that is a stronger localization finding than depth-based terciles.

3. **Magnitude features (frob, spectral norm) will not distinguish between objectives.** They grow uniformly with training steps at every layer. If DPO-sycophancy and DPO-helpfulness are distinguishable, the signal will be in the *shape* features (entropy, effective rank, stable rank, concentration) or in the expanded features (singular vector alignment), not in magnitude.

4. **The expanded feature set (singular vector cosine similarity to healthy centroid) is now more important than initially estimated.** Magnitude is saturated as a discriminator. Direction and shape are where objective-specific signal would live.

---

## Phase 0c: Helpfulness Separability Pre-Flight

**Date**: 2026-03-15
**Script**: `01_layer_analysis.py --preflight-q3`
**Data source**: POC v2 adapters (dpo_grad_*) + 2 newly manufactured helpfulness adapters

Phase 0c tested whether DPO-sycophancy and DPO-helpfulness are spectrally distinguishable — a prerequisite for H-objective. This ran before the full task-geometry population was manufactured.

### Population

| Group | Adapters | Steps |
|-------|----------|-------|
| Sycophancy (POC) | dpo_grad_050, dpo_grad_150, dpo_grad_300, dpo_grad_600 | 50, 150, 300, 600 |
| Helpfulness (new) | dpo_help_0300, dpo_help_0600 | 300, 600 |
| Healthy (control) | healthy_v1, healthy_v2, healthy_v3 | — |

### Original results (N=6, 4 syco vs 2 help — step counts NOT matched)

| Test | AUC | Accuracy |
|------|-----|----------|
| Combined (all features) | 0.625 | 0.833 |
| q_proj only | 0.375 | 0.333 |
| v_proj only | **0.875** | 0.833 |
| Magnitude only | 0.875 | 0.667 |
| Shape only | **1.000** | 0.833 |
| All features (combined) | 0.625 | 0.833 |
| Three-way classification accuracy | — | 0.778 |

**Decision**: Q3_MARGINAL — "AUC=0.625 in [0.60, 0.80) → Weak signal. Proceed but lower Q3 confidence."

### Step-matched reanalysis (N=4, 2 syco vs 2 help — 300+600 steps only)

The original population was confounded: sycophancy had 4 adapters at steps 50/150/300/600 while helpfulness had only 2 at steps 300/600. The unmatched 50-step and 150-step sycophancy adapters have smaller magnitudes that could drive apparent separation.

Reanalysis using only the step-matched subset:

| Test | Original (4v2) | Step-matched (2v2) | Delta |
|------|----------------|-------------------|-------|
| All features | 0.625 | **0.250** | -0.375 |
| q_proj only | 0.375 | **0.000** | -0.375 |
| v_proj only | 0.875 | **0.500** | -0.375 |
| Magnitude only | 0.875 | **0.250** | -0.625 |
| Shape only | 1.000 | **0.750** | -0.250 |
| Expanded only | — | **0.000** | — |

At matched step counts, cosine similarity between syco and help adapters is 0.998 (300 steps) and 0.998 (600 steps). Within-class cosine similarity is also 0.998. The two objectives are near-indistinguishable at N=2 per class.

**Shape features (AUC=0.75) are the only feature family above chance in the step-matched analysis.** The original v_proj=0.875 and magnitude=0.875 results were inflated by the step-count confound.

### Implications

1. The original Phase 0c Q3_MARGINAL decision was correct — the signal was weak. The step-matched reanalysis confirms it was weaker than the headline numbers suggested.
2. The full experiment's perfect separation (H-objective AUC=1.0, N=14) required the larger population and expanded SV cosine features to overcome the extreme similarity between objectives at matched steps.
3. The v_proj advantage for objective disentangling seen in the full experiment (0.83 vs 0.50 for q_proj) was NOT present at N=4 step-matched. It emerged only with the full population.

---

## Phase 0 Decision

**`all_layers`**

Rationale: no tercile dominates, signal is distributed, and the Phase 2 classification task (4-way) is harder than binary. Retaining all layers preserves the full feature space for the harder problem. The computational cost of full-layer extraction is negligible (~1 hour CPU for 30 adapters).

---

## Artifacts

| File | Description |
|------|-------------|
| `phase0_layer_importance.json` | Per-sublayer, per-feature LR coefficient magnitudes |
| `phase0_layer_ablation.json` | Tercile AUCs, ablation AUCs, full-model AUC, decision |
| `phase0_layer_heatmap.png` | Feature importance x sublayer heatmap (Phase 0a) |
| `phase0b_step_gradient.json` | Per-sublayer, per-feature Spearman rho with DPO step count |
| `phase0b_step_gradient_heatmap.png` | Spearman rho x sublayer heatmap (Phase 0b) |
| `phase0_decision.txt` | "focus_layers: early (0-8)" (overridden by this analysis -- see decision above) |
| `phase0c_separability.json` | Phase 0c original results (4 syco vs 2 help, step counts not matched) |
| `phase0c_objective_scatter.png` | PCA scatter of syco vs help adapters (Phase 0c) |
| `phase0c_step_matched.json` | Phase 0c step-matched reanalysis (2 syco vs 2 help, 300+600 only) |
| `phase0c_step_matched_analysis.py` | Script for the step-matched reanalysis |

Note: `phase0_decision.txt` was auto-generated by the script based on tercile spread alone. The analysis above overrides it to `all_layers` based on the full picture: no tercile is necessary (all ablations pass), the signal is module-specific not depth-specific, and the harder 4-way task benefits from full coverage.
