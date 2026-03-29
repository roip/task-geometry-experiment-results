# Task-Geometry Separability — Pre-Registration

**Date**: 2026-03-15
**Status**: Pre-registered — written before any Phase 1 adapter is manufactured
**Researcher**: RP
**Theoretical advisor**: Hinton
**Spec**: [EXPERIMENT-TASK-GEOMETRY.md](../../../specs/village.ai/EXPERIMENT-TASK-GEOMETRY.md)
**Depends on**: Drift Indicators POC Exit Report (2026-03-15)

---

## What This Is

This document records all hypotheses, expected outcomes, and success/failure criteria **before the experiment runs**. Results must be evaluated against these criteria exactly as written. Criteria may not be revised after data is collected.

Phase 0 (per-layer analysis on existing POC data) is pre-flight and may run before this document is finalized. Phases 1–4 may not begin manufacturing until this document is frozen.

---

## Adapter Population

### Main population (30 adapters)

| ID pattern | Category | Method | Count | Details | Seeds |
|---|---|---|---|---|---|
| `healthy_v{N}` | Healthy | SFT on HH-RLHF chosen | 10 | 50 steps equivalent | seeds 1–10 |
| `dpo_syco_{steps}[_s{seed}]` | Sycophancy | DPO, inverted harmlessness | 8 | Steps: 50, 150, 300, 600, 1000, 2000; + 300×seeds 1,2 | 3 at 300, 1 elsewhere |
| `dpo_help_{steps}` | Helpfulness erosion | DPO, inverted helpfulness | 6 | Steps: 50, 150, 300, 600, 1000, 2000 | 1 per step |
| `steered_refusal_{level}_s{seed}` | Refusal erosion | Activation steering | 6 | Levels: 0.3, 0.7, 1.5 × 2 seeds | 2 per level |

### OOD test set (4 adapters, manufactured in Phase 1e)

| ID pattern | Category | Method | Count | Details | Seeds |
|---|---|---|---|---|---|
| `steered_syco_{level}_s1` | Sycophancy | Activation steering | 4 | Levels: 0.3, 0.7, 1.5, 2.0 | 1 per level |

Re-manufactured from existing sycophancy contrastive pairs. Tests whether a classifier trained on DPO-sycophancy generalizes to steering-sycophancy (same objective, different method).

### Train/test split

70/30 stratified by category on the main 30 adapters. OOD set evaluated separately, never seen during training.

### Ground truth labels

Primary labels are derived from manufacturing parameters (known exactly):

| Adapter | `drift_type` | `drift_method` | `drift_level_numeric` | `drift_severity` |
|---|---|---|---|---|
| `healthy_v*` | healthy | sft | 0.0 | none |
| `dpo_syco_050` | sycophancy | dpo | 0.083 (50/600) | subtle |
| `dpo_syco_150` | sycophancy | dpo | 0.25 | mild |
| `dpo_syco_300` | sycophancy | dpo | 0.50 | moderate |
| `dpo_syco_600` | sycophancy | dpo | 1.0 | strong |
| `dpo_syco_1000` | sycophancy | dpo | 1.67 | severe |
| `dpo_syco_2000` | sycophancy | dpo | 3.33 | extreme |
| `dpo_help_*` | helpfulness_erosion | dpo | (same scale) | (same) |
| `steered_refusal_0.3_*` | refusal_erosion | steering | 0.3 | subtle |
| `steered_refusal_0.7_*` | refusal_erosion | steering | 0.7 | moderate |
| `steered_refusal_1.5_*` | refusal_erosion | steering | 1.5 | severe |
| `steered_syco_0.3_s1` | sycophancy | steering | 0.3 | subtle |
| `steered_syco_0.7_s1` | sycophancy | steering | 0.7 | moderate |
| `steered_syco_1.5_s1` | sycophancy | steering | 1.5 | severe |
| `steered_syco_2.0_s1` | sycophancy | steering | 2.0 | extreme |

`drift_level_numeric` for DPO = steps/600. For steering = drift_level directly. These are ordinal proxies, not calibrated to equivalent behavioral severity across methods.

Behavioral scores from the scenario suite are recorded for 4 extreme adapters only as a validation check. They are **not** used as classifier ground truth. The POC exit report demonstrated the suite is unreliable (AUC=0.083).

### Scope limitation

This experiment tests the **objective-to-geometry** link: can weight geometry identify what training objective was used? It does **not** test the **geometry-to-behavior** link: does that geometric signature predict behavioral drift? The second link requires a functioning behavioral measurement instrument, which we do not currently have. Claims about "detecting behavioral drift from weights" must wait until both links are confirmed.

---

## Phase 0 Pre-Flight Findings (incorporated before manufacturing)

Phase 0 ran on 2026-03-15, CPU-only, on existing POC data (7 adapters). Full results in `data/results/PHASE0_RESULTS.md`.

1. **q_proj carries the binary signal, v_proj does not.** q_proj AUC >= 0.75 at 22/28 layers. v_proj AUC=0.0 at 5 layers. Module type is the informative axis, not depth.
2. **Depth localization not supported.** Early and middle terciles both AUC=1.0. All depth ablations pass. Signal is distributed across depth.
3. **Magnitude features are saturated.** Frobenius norm and spectral norm are perfectly step-monotonic (rho=+1.0) at every sublayer. They track training intensity, not training objective.
4. **Decision: all_layers, analysis split by module type and feature type.** No layer focusing. Every Phase 3 classifier runs 3 ways by module (q_proj / v_proj / both) and 3 ways by feature type (magnitude / shape / all).

---

## Hypotheses

### H-binary: Weight-space features distinguish healthy from all-drifted at scale

**Statement**: A logistic regression classifier on per-layer spectral features will distinguish healthy adapters from all drifted adapters (DPO + steering combined) with AUC > 0.85 on a 70/30 stratified split with N=30.

**Rationale**: The POC achieved AUC=1.0 at N=7 with LOO-CV. Scaling to N=30 with a proper train/test split tests whether this holds beyond the small-sample regime.

**Features**: Per-layer spectral features (Frobenius norm, spectral norm, stable rank, SV entropy, SV concentration, effective rank, top-8 SVs) plus expanded features (top-3 singular vector cosine similarity to healthy centroid). Layer scope determined by Phase 0.

**Success criterion**: Binary AUC > 0.85, bootstrapped 95% CI lower bound > 0.75.

**Failure condition**: Binary AUC < 0.70. The POC result was a small-sample artifact. The signal is weaker than N=7 suggested. Revisit feature set before proceeding.

---

### H-crossmethod: Cross-method generalization

**Statement**: A classifier trained on DPO-drifted vs healthy adapters will correctly classify activation-steering-drifted adapters as drifted, without retraining.

**Rationale**: The POC tested only DPO drift. If the classifier is method-specific (only catches DPO-shaped perturbations), the approach has limited practical value. Cross-method generalization is the minimum requirement for a deployment-ready detector.

**Test 1 (in-distribution)**: Train on all drifted (DPO + steering) vs healthy. Report cross-method binary AUC: train on DPO-only, test on steering-only.

**Test 2 (OOD)**: Train on DPO-sycophancy adapters, test on OOD steered-sycophancy adapters (same objective, different method, never seen in training).

**Success criterion**: Cross-method AUC (DPO-trained, steering-tested) > 0.80.

**Failure condition**: Cross-method AUC < 0.70. The approach is method-specific. Claims must be scoped to within-method detection only.

---

### H-fingerprint: Task-geometry separability

**Statement**: Different drift objectives produce geometrically distinguishable per-layer spectral signatures. A one-vs-rest logistic regression classifier will distinguish between healthy, sycophancy, helpfulness-erosion, and refusal-erosion adapters (4-way classification).

**Rationale**: This is the central new hypothesis. The POC showed binary detection works. Task-fingerprinting tests whether weight geometry encodes *which* objective was used, not just that drift occurred. If true, weight inspection provides diagnosis (what type of drift) not just detection (drift present/absent).

**Success criterion**: All 6 pairwise drift-type AUCs > 0.80.

**Failure condition**: Any pairwise AUC < 0.70. Those drift types are geometrically indistinguishable. Report which pairs separate and which do not.

---

### H-objective: Same-method objective disentangling

**Statement**: DPO-sycophancy and DPO-helpfulness adapters, which share the same training method (DPO) but differ in training objective (inverted harmlessness vs inverted helpfulness), are geometrically distinguishable.

**Rationale**: This isolates the objective variable from the method variable. Since both use DPO, any geometric difference must come from what was optimized, not how it was optimized. This is the strongest test of whether weight geometry encodes task content rather than training procedure.

**Success criterion**: DPO-sycophancy vs DPO-helpfulness pairwise AUC > 0.80.

**Failure condition**: AUC < 0.70. Same-method drift types look alike in weight space. Task-fingerprinting operates at the method level, not the objective level. The diagnostic capability is coarser than hypothesized.

---

### H-localization: Signal is structured by module type (q_proj vs v_proj), not by depth

**Statement**: The discriminative signal separating drift types is primarily carried by q_proj (query projection) weights, with v_proj (value projection) carrying secondary or objective-specific signal. Module type is a more informative analytical axis than layer depth.

**Rationale**: Phase 0 pre-flight (2026-03-15) found that q_proj achieves AUC >= 0.75 at 22/28 layers for binary classification, while v_proj scores AUC=0.0 at 5 layers. The depth-tercile hypothesis (early + late layers dominate) was not supported: early and middle terciles both achieved AUC=1.0, all depth-ablations passed. The binary signal is distributed across depth but concentrated in q_proj. The multi-class case may differ, hence this hypothesis remains testable rather than pre-decided.

Phase 0 also found magnitude features (Frobenius norm, spectral norm) are perfectly step-monotonic (rho=+1.0) at every sublayer. They track training intensity uniformly and will not distinguish between objectives. Shape features (entropy, effective rank, stable rank, concentration) and expanded features (singular vector alignment) are where objective-specific signal would live.

**Measurements**:
- Binary AUC: q_proj only vs v_proj only vs both combined
- 4-way AUC: q_proj only vs v_proj only vs both combined
- Pairwise AUC (DPO-syco vs DPO-help): q_proj only vs v_proj only vs both combined
- Binary AUC: magnitude features only vs shape features only vs all features
- 4-way AUC: magnitude features only vs shape features only vs all features
- 4-way classifier feature importance grouped by module type and feature type

**Success criterion (module)**: q_proj-only AUC is within 0.05 of combined AUC for binary classification, and q_proj-only outperforms v_proj-only by > 0.15 AUC on at least the binary task. This confirms q_proj dominance extends from the POC to the scaled population.

**Success criterion (features)**: Shape-only features outperform magnitude-only features by > 0.10 AUC on the 4-way task. This confirms that objective separation (if it exists) lives in spectral shape, not magnitude.

**Failure condition**: v_proj-only outperforms q_proj-only on the 4-way task. The Phase 0 binary finding does not transfer to multi-class, and the module-type framing is wrong for objective-level detection. OR: magnitude-only features match or beat shape-only on the 4-way task, meaning magnitude is not saturated for objective separation despite being saturated for binary and ordinal.

---

### H-centroid: Centroid distance detection window

**Statement**: Centroid distance (cosine distance from healthy centroid, z-score threshold of 3.0) will fail to flag high-step-count DPO adapters that per-layer classification still catches.

**Rationale**: The POC showed centroid z-scores decrease monotonically with DPO steps (12.6 at 50 steps, 4.6 at 600 steps). Extending to 1000 and 2000 steps should cross below the z=3.0 flagging threshold. If per-layer classification still separates them, centroid distance can be retired in favor of per-layer classification.

**Measurement**: Report the DPO step count at which centroid z-score drops below 3.0 (interpolated). Report per-layer classification AUC at that same step count.

**Expected**: Centroid distance fails at 1000–2000 steps. Per-layer classification AUC remains > 0.85.

---

### H-ordinal: Spectral features track drift severity within type

**Statement**: Within each drift type, spectral features correlate with training intensity (`drift_level_numeric`), enabling ordinal severity ranking.

**Rationale**: The POC showed binary classification works but ordinal ranking fails (concordance=0.111 on behavioral scores). This tests whether spectral features can do what behavioral scores could not: rank severity within a class.

**Measurement**: Spearman rank correlation between spectral features and `drift_level_numeric`, computed separately within DPO-sycophancy (8 adapters), DPO-helpfulness (6 adapters), and steering-refusal (6 adapters).

**Success criterion**: Spearman rho > 0.80 on aggregate classifier score within at least 2 of 3 drift types.

**Failure condition**: Spearman rho < 0.50 in any drift type. Features detect drift but cannot rank severity. Binary detection is the ceiling for that type.

---

### H3-revised: Sycophancy subspace recovery

**Statement**: Sycophancy drift occupies a recoverable low-dimensional subspace in weight space, identifiable by PCA on weight deltas (Method B) and/or per-layer linear probes on hidden states (Method A).

**Rationale**: The original H3 (contrastive activation projection) was falsified in the POC (z=-7.5, wrong direction). The projection tracked training magnitude, not sycophancy. Two replacement methods are proposed. Method B is cheaper and tests a necessary precondition for Method A.

**Execution order**: Method B (PCA, CPU) runs first. Method A (probing, GPU) is gated on Method B result.

**Method B — Weight-delta PCA**:
- Input: flattened weight deltas for 8 DPO-sycophancy + 6 DPO-helpfulness adapters
- Expected: PC1 captures training magnitude (correlates with steps for both). PC2 or PC3 captures objective axis (separates sycophancy from helpfulness).
- Success criterion: A principal component separates sycophancy from helpfulness with AUC > 0.80.
- Gate: AUC < 0.65 → skip Method A, close H3 at this model scale. AUC 0.65–0.80 → proceed to Method A (activation space may be more separable). AUC > 0.80 → proceed to Method A as validation.

**Method A — Per-layer probing classifiers**:
- Probes: per-layer logistic regression on sycophantic vs honest hidden states (50+ contrastive pairs)
- Alignment test: cosine similarity between probe normal vector and top-k left singular vectors of the weight delta (ΔW = B·A) at each layer
- Success criterion: alignment cosine > 0.5 for 3+ layers, specific to sycophancy adapters (not seen in helpfulness adapters)
- Failure: alignment cosine < 0.3 across all layers. Activation-space sycophancy direction does not correspond to weight-space perturbation direction. Close H3.

---

## Expected Results

What we predict will happen, stated before any data is collected. Evaluate results against these predictions first, then check the negative results section only for hypotheses that failed.

| Hypothesis | Prediction | Confidence | Reasoning |
|---|---|---|---|
| H-binary | **PASS.** AUC ~0.90–1.00. | High | POC signal was AUC=1.0 at N=7. The spectral features encode real structure. Scaling to N=30 may soften the number slightly but shouldn't break it. |
| H-crossmethod | **Uncertain.** AUC could land anywhere from 0.60 to 0.90. | Low | DPO and steering perturb the model in fundamentally different ways. No prior data to anchor this. Coin flip. |
| H-fingerprint | **Partial pass.** DPO-vs-steering pairs will separate (different methods). Same-method pairs are uncertain. | Medium | Method-level separation is likely. Objective-level separation is the gamble. |
| H-objective | **Uncertain, leaning toward fail.** AUC 0.55–0.75. | Low | Hardest test. Both use DPO, same hyperparameters. The difference is which HH-RLHF axis was inverted. Plausible that harmlessness and helpfulness engage different layers, but not established. |
| H-localization | **PASS (module).** q_proj dominates for binary, likely for 4-way too. **Uncertain (features).** Shape features should beat magnitude for 4-way, but untested. | Medium | Phase 0 confirmed q_proj dominance for binary. Magnitude features saturated at rho=+1.0 everywhere. Shape and expanded features are where objective signal would live. |
| Phase 0b (pre-flight) | **Some layers show strong step-monotonicity (rho > 0.90), others flat (rho < 0.50).** | Medium | If DPO training concentrates in specific layers, the per-layer step gradient should be non-uniform. Layers that change most with step count are where the DPO objective is being encoded. |
| H-centroid | **PASS.** Z-score crosses below 3.0 at ~1000 steps. Per-layer AUC stays above 0.85. | High | POC trend was unambiguous: 12.6, 8.0, 5.2, 4.6. Extrapolation is straightforward. |
| H-ordinal | **PASS.** Spearman rho > 0.80 for DPO types, probably for steering too. | Medium-High | POC features changed monotonically with DPO steps. Steering levels directly scale perturbation magnitude. |
| H3-revised | **Method B marginal (AUC 0.65–0.80). Method A conditional.** | Low | Depends on H-objective. If the objectives aren't separable by classifier, PCA won't find a separating component either. |

**What would surprise us (unexpected learnings to watch for):**
- v_proj outperforming q_proj on the 4-way task (would invert the Phase 0 finding for multi-class)
- Magnitude features separating objectives despite being saturated for binary and ordinal (would mean step-monotonicity doesn't imply objective-blindness)
- Steering adapters showing the opposite q/v pattern from DPO (signal in v_proj, not q_proj)
- Steering adapters being *more* spectrally similar to healthy than DPO adapters at equivalent behavioral drift
- Seed variance within drifted adapters being substantially higher than within healthy adapters
- Centroid distance *increasing* at 1000-2000 steps instead of continuing to decrease

---

## Pre-Registered Negative Results

These are meaningful findings if they occur. They are not failures to suppress. Consult this section only for hypotheses that failed their success criterion.

1. **H-binary fails (AUC < 0.70)**: The POC's AUC=1.0 at N=7 was a small-sample artifact. Weight-space spectral features do not reliably separate drifted from healthy at scale. Implication: revisit feature set (current features may project away from the discriminative structure), or accept that spectral features are insufficient and shift to other weight-space representations.

2. **H-crossmethod fails (AUC < 0.70)**: Detection is method-specific. A classifier trained on DPO perturbations does not generalize to steering perturbations. Implication: production deployment requires method-specific classifiers or method-agnostic feature representations. The practical value of weight-space monitoring is reduced unless the manufacturing method is known.

3. **H-fingerprint fails (any pairwise AUC < 0.70)**: Some or all drift types are geometrically indistinguishable. Task-fingerprinting reduces to binary anomaly detection. Implication: weight inspection provides detection (something is wrong) but not diagnosis (what is wrong). Report which pairs separate and which collapse.

4. **H-objective fails (DPO-syco vs DPO-help AUC < 0.70)**: Same-method drift types produce indistinguishable geometries. The per-layer structure encodes training method, not training objective. Implication: task-fingerprinting operates at the method level (DPO vs steering), not the objective level (sycophancy vs helpfulness). Diagnostic resolution is coarser than hypothesized.

5. **H3-revised fails (both methods)**: PCA finds no separating component AND probes show no alignment with weight deltas. Sycophancy has no recoverable geometric signature in this feature space at this model scale. Implication: close the H3 line of investigation for Llama-3.2-3B LoRA adapters. The hypothesis may still hold at larger scale or with different adapter architectures, but this experiment cannot support it.

6. **H-ordinal fails (rho < 0.50)**: Spectral features detect drift class but cannot rank severity within a class. Binary detection is the ceiling. Ordinal drift monitoring requires a different approach (behavioral measurement, embedding-based scoring, or a fundamentally different feature space).

7. **H-localization fails (module)**: v_proj outperforms q_proj on the 4-way task, or both perform equally. The Phase 0 binary finding (q_proj dominance) does not transfer to multi-class. The module-type framing is wrong for objective-level detection. Implication: revert to treating all features uniformly; the q_proj vs v_proj distinction is a binary-task artifact, not a structural property of drift.

8. **H-localization fails (features)**: Magnitude-only features match or beat shape-only on the 4-way task. Magnitude features are not saturated for objective separation despite being saturated for binary and ordinal. Implication: the Phase 0 finding that rho=+1.0 everywhere does not mean magnitude is uninformative for distinguishing objectives. The shape-feature prioritization was premature.

---

## Reporting Requirements

Per lab communication standards, the results report must:

1. Show the full data table (all 34 adapters, all metrics) before any interpretation
2. Report each hypothesis verdict against the pre-registered criteria above, not revised criteria
3. Lead with the anomalous result if any adapter breaks the expected pattern
4. State findings as plain observations before interpretation
5. Report pairwise separability in a single matrix, not cherry-picked pairs
6. Report all confidence intervals, not just point estimates
7. Name omissions explicitly (anything that could not be measured or was skipped)
8. State the scope limitation: results establish the objective-to-geometry link only, not the geometry-to-behavior link
9. Report module-split results (q_proj / v_proj / both) for every classifier, not just the combined number
10. Report feature-split results (magnitude / shape / all) for every classifier. If magnitude-only matches shape-only on the 4-way task, flag it as contradicting the Phase 0 saturation finding

---

## Run Order

```
Phase 0:  [local or GCP, CPU, <5 min]
  ├─ 0a: 01_layer_analysis.py on existing POC data (layer localization for binary)
  ├─ 0b: 01_layer_analysis.py --step-gradient (per-layer DPO step monotonicity)
  └─ Decision: layer scope for expanded features

Phase 1:  [GCP L4, ~9 h]
  ├─ 1a: 02_manufacture_healthy.py × 10 seeds              (~50 min)
  ├─ 1d: 04_manufacture_steered.py --mode refusal × 6      (~1.5 h, can overlap 1a)
  ├─ 1e: 04_manufacture_steered.py --mode sycophancy × 4   (~1 h, OOD set)
  ├─ 1b: 03_manufacture_dpo.py --axis sycophancy × 8       (~3.5 h)
  └─ 1c: 03_manufacture_dpo.py --axis helpfulness × 6      (~2.5 h)

Phase 2:  [GCP L4, ~1.5 h]
  ├─ 2a: 05_spectral_features.py on 30+ adapters            (~1 h, CPU)
  └─ 2b: 06_behavioral_validation.py on 4 extreme adapters  (~40 min, sanity check)

Phase 3:  [GCP L4 or local, ~30 min]
  └─ 07_classification.py --multiclass --pairwise --bootstrap --ordinal \
       --module-split --feature-split
  └─ Centroid distance tracking

Phase 4:  [GCP L4, ~0.5–2 h] — only if Phase 3 binary AUC > 0.70
  ├─ 4b: 08_h3_revised.py --method pca                     (~15 min, CPU, runs FIRST)
  ├─ GATE: if 4b AUC < 0.65 → skip 4a. If ≥ 0.65 → proceed.
  └─ 4a: 08_h3_revised.py --method probe                   (~1.5 h, conditional)
```

**Estimated wall clock**: ~13.2–14.7 h on L4 (all phases).
**Estimated cost**: ~$2.77–$3.09 spot ($0.21/hr L4).

---

## Reviewer Notes

**2026-03-15 (Hinton, pre-registration review)**:

1. The substitution of DPO-helpfulness for RLHF-corrupted-reward is correct. It isolates the objective variable from the method variable without requiring new training infrastructure. The same-method comparison (H-objective) is the sharpest test of whether geometry encodes task content.

2. `drift_level_numeric = steps/600` is an arbitrary normalization. It is acceptable for ordinal (Spearman) analysis. It is not a cardinal scale and must not be used in regression or interpreted as proportional severity.

3. The Phase 4 gating on Method B is sound. PCA on weight deltas tests a necessary precondition: does the weight-delta space have directional structure that separates objectives? If it does not, the probing alignment test in Method A cannot succeed, because it requires exactly that directional structure to exist. The soft gate at 0.65–0.80 is justified: activation space could be more separable than what PCA recovers from flattened weight deltas, because the mapping from weights to activations is nonlinear.

4. The scope limitation (objective-to-geometry only) must be stated in the exit report, not just here. Any claim about "detecting behavioral drift" requires a second experiment that establishes the geometry-to-behavior link with a functioning behavioral instrument.

5. Three seeds at DPO step 300 is a reproducibility diagnostic, not a variance estimate. If the three adapters land in different regions of feature space, the geometry is seed-dependent and classification is measuring noise rather than task structure. The cost (50 min) is trivially justified by the information it provides.

---

*This document must not be modified after manufacturing begins.*
