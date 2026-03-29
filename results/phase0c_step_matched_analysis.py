"""
Phase 0c Step-Matched Analysis

Re-runs the Phase 0c syco-vs-help separability test using ONLY the
step-matched adapters (300 and 600 steps) to remove the confound from
unmatched 50/150 step adapters in the sycophancy group.

Population: 4 adapters (2 syco @ 300,600  vs  2 help @ 300,600)
"""

import json
import numpy as np
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

RESULTS_DIR = Path(__file__).parent

SYCO_IDS = ["dpo_grad_300", "dpo_grad_600"]
HELP_IDS = ["dpo_help_0300", "dpo_help_0600"]

MAGNITUDE_FEATURES_PER_LAYER = 2   # frobenius_norm, spectral_norm
SHAPE_FEATURES_PER_LAYER = 4       # stable_rank, sv_entropy, sv_concentration, effective_rank
TOP_K_PER_LAYER = 8
EXPANDED_PER_LAYER = 3              # top-3 SV cosine similarity
N_LAYERS = 56

BASE_FEATURES = (MAGNITUDE_FEATURES_PER_LAYER + SHAPE_FEATURES_PER_LAYER + TOP_K_PER_LAYER) * N_LAYERS
MAGNITUDE_INDICES = []
SHAPE_INDICES = []
for layer in range(N_LAYERS):
    base = layer * (MAGNITUDE_FEATURES_PER_LAYER + SHAPE_FEATURES_PER_LAYER + TOP_K_PER_LAYER)
    MAGNITUDE_INDICES.extend([base, base + 1])
    SHAPE_INDICES.extend([base + 2, base + 3, base + 4, base + 5])

Q_PROJ_LAYERS = list(range(0, N_LAYERS, 2))
V_PROJ_LAYERS = list(range(1, N_LAYERS, 2))

FEATURES_PER_LAYER_BASE = MAGNITUDE_FEATURES_PER_LAYER + SHAPE_FEATURES_PER_LAYER + TOP_K_PER_LAYER
FEATURES_PER_LAYER_EXPANDED = EXPANDED_PER_LAYER

def get_module_indices(layer_indices, n_base, n_expanded):
    base_idx = []
    for l in layer_indices:
        start = l * FEATURES_PER_LAYER_BASE
        base_idx.extend(range(start, start + FEATURES_PER_LAYER_BASE))
    exp_idx = []
    for l in layer_indices:
        start = n_base + l * FEATURES_PER_LAYER_EXPANDED
        exp_idx.extend(range(start, start + FEATURES_PER_LAYER_EXPANDED))
    return base_idx + exp_idx


def load_feature_matrix():
    with open(RESULTS_DIR / "spectral_feature_matrix.json") as f:
        data = json.load(f)
    return {entry["adapter_id"]: np.array(entry["feature_vector"]) for entry in data}


def loo_auc(X, y):
    """Leave-one-out AUC for binary classification."""
    n = len(y)
    if n < 4:
        scores = np.zeros(n)
        for i in range(n):
            mask = np.ones(n, dtype=bool)
            mask[i] = False
            X_train, y_train = X[mask], y[mask]
            X_test = X[i:i+1]
            if len(np.unique(y_train)) < 2:
                scores[i] = 0.5
                continue
            scaler = StandardScaler()
            X_train_s = scaler.fit_transform(X_train)
            X_test_s = scaler.transform(X_test)
            clf = LogisticRegression(max_iter=5000, solver="lbfgs", C=1.0)
            clf.fit(X_train_s, y_train)
            scores[i] = clf.predict_proba(X_test_s)[0, 1]
        if len(np.unique(y)) < 2:
            return float("nan")
        return roc_auc_score(y, scores)
    else:
        scores = np.zeros(n)
        for i in range(n):
            mask = np.ones(n, dtype=bool)
            mask[i] = False
            X_train, y_train = X[mask], y[mask]
            X_test = X[i:i+1]
            if len(np.unique(y_train)) < 2:
                scores[i] = 0.5
                continue
            scaler = StandardScaler()
            X_train_s = scaler.fit_transform(X_train)
            X_test_s = scaler.transform(X_test)
            clf = LogisticRegression(max_iter=5000, solver="lbfgs", C=1.0)
            clf.fit(X_train_s, y_train)
            scores[i] = clf.predict_proba(X_test_s)[0, 1]
        return roc_auc_score(y, scores)


def loo_accuracy(X, y):
    """Leave-one-out accuracy."""
    n = len(y)
    correct = 0
    for i in range(n):
        mask = np.ones(n, dtype=bool)
        mask[i] = False
        X_train, y_train = X[mask], y[mask]
        X_test = X[i:i+1]
        if len(np.unique(y_train)) < 2:
            continue
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)
        clf = LogisticRegression(max_iter=5000, solver="lbfgs", C=1.0)
        clf.fit(X_train_s, y_train)
        if clf.predict(X_test_s)[0] == y[i]:
            correct += 1
    return correct / n


def run_analysis():
    features = load_feature_matrix()

    all_ids = SYCO_IDS + HELP_IDS
    missing = [aid for aid in all_ids if aid not in features]
    if missing:
        print(f"ERROR: missing adapters: {missing}")
        return

    X = np.array([features[aid] for aid in all_ids])
    y = np.array([0] * len(SYCO_IDS) + [1] * len(HELP_IDS))  # 0=syco, 1=help
    n_total = X.shape[1]
    n_base = BASE_FEATURES

    print("=" * 70)
    print("  Phase 0c Step-Matched Analysis: DPO-syco vs DPO-help")
    print("  Controlling for step count confound")
    print("=" * 70)
    print(f"\n  Sycophancy:  {SYCO_IDS}")
    print(f"  Helpfulness: {HELP_IDS}")
    print(f"  N = {len(all_ids)} (2 vs 2), steps = [300, 600] both groups")
    print(f"  Features: {n_total} total ({n_base} base + {n_total - n_base} expanded)")
    print(f"  Method: Leave-One-Out CV, Logistic Regression")

    results = {}

    # Combined (all features)
    auc_all = loo_auc(X, y)
    acc_all = loo_accuracy(X, y)
    results["combined_all"] = {"auc": auc_all, "accuracy": acc_all}
    print(f"\n  --- All features (n={n_total}) ---")
    print(f"  AUC = {auc_all:.4f}   Accuracy = {acc_all:.4f}")

    # Module split
    q_idx = get_module_indices(Q_PROJ_LAYERS, n_base, n_total - n_base)
    v_idx = get_module_indices(V_PROJ_LAYERS, n_base, n_total - n_base)

    auc_q = loo_auc(X[:, q_idx], y)
    acc_q = loo_accuracy(X[:, q_idx], y)
    auc_v = loo_auc(X[:, v_idx], y)
    acc_v = loo_accuracy(X[:, v_idx], y)
    results["q_proj"] = {"auc": auc_q, "accuracy": acc_q}
    results["v_proj"] = {"auc": auc_v, "accuracy": acc_v}

    print(f"\n  --- Module split ---")
    print(f"  q_proj:  AUC = {auc_q:.4f}   Accuracy = {acc_q:.4f}")
    print(f"  v_proj:  AUC = {auc_v:.4f}   Accuracy = {acc_v:.4f}")

    # Feature split
    mag_idx = MAGNITUDE_INDICES
    shape_idx = SHAPE_INDICES

    auc_mag = loo_auc(X[:, mag_idx], y)
    acc_mag = loo_accuracy(X[:, mag_idx], y)
    auc_shape = loo_auc(X[:, shape_idx], y)
    acc_shape = loo_accuracy(X[:, shape_idx], y)

    exp_idx = list(range(n_base, n_total))
    auc_exp = loo_auc(X[:, exp_idx], y)
    acc_exp = loo_accuracy(X[:, exp_idx], y)

    results["magnitude"] = {"auc": auc_mag, "accuracy": acc_mag}
    results["shape"] = {"auc": auc_shape, "accuracy": acc_shape}
    results["expanded"] = {"auc": auc_exp, "accuracy": acc_exp}

    print(f"\n  --- Feature split ---")
    print(f"  magnitude: AUC = {auc_mag:.4f}   Accuracy = {acc_mag:.4f}")
    print(f"  shape:     AUC = {auc_shape:.4f}   Accuracy = {acc_shape:.4f}")
    print(f"  expanded:  AUC = {auc_exp:.4f}   Accuracy = {acc_exp:.4f}")

    # Raw feature distance (cosine similarity between step-matched pairs)
    print(f"\n  --- Raw cosine similarity (step-matched pairs) ---")
    from numpy.linalg import norm
    for steps, s_id, h_id in [("300", SYCO_IDS[0], HELP_IDS[0]),
                                ("600", SYCO_IDS[1], HELP_IDS[1])]:
        s_vec = features[s_id]
        h_vec = features[h_id]
        cos_sim = np.dot(s_vec, h_vec) / (norm(s_vec) * norm(h_vec))
        l2_dist = norm(s_vec - h_vec)
        print(f"  {steps} steps: cos_sim = {cos_sim:.4f}   L2 = {l2_dist:.4f}")

    # Within-class similarity
    syco_cos = np.dot(features[SYCO_IDS[0]], features[SYCO_IDS[1]]) / (
        norm(features[SYCO_IDS[0]]) * norm(features[SYCO_IDS[1]]))
    help_cos = np.dot(features[HELP_IDS[0]], features[HELP_IDS[1]]) / (
        norm(features[HELP_IDS[0]]) * norm(features[HELP_IDS[1]]))
    print(f"\n  Within-class cosine similarity:")
    print(f"  syco 300 vs 600:  {syco_cos:.4f}")
    print(f"  help 300 vs 600:  {help_cos:.4f}")

    print(f"\n{'=' * 70}")

    # Save results
    output = {
        "description": "Phase 0c step-matched reanalysis (300+600 steps only)",
        "sycophancy_adapters": SYCO_IDS,
        "helpfulness_adapters": HELP_IDS,
        "n_samples": len(all_ids),
        "steps_used": [300, 600],
        "confound_controlled": True,
        "results": results,
    }
    out_path = RESULTS_DIR / "phase0c_step_matched.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Saved: {out_path}")


if __name__ == "__main__":
    run_analysis()
