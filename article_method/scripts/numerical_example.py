"""
Reproducible script for the illustrative numerical example
(Section 7 of the PATHCAST method paper).

Computes the analytical fundamental matrix N, absorption matrix B,
expected lead time, and the corresponding Monte Carlo estimates on
the six-state SDLC chain described in the paper.

Run: python3 numerical_example.py
"""

import numpy as np

np.set_printoptions(precision=4, suppress=True)

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------
# State order: 0=backlog, 1=in_progress, 2=review, 3=testing,
#              4=done (absorbing), 5=cancelled (absorbing)
STATES = ["backlog", "in_progress", "review", "testing", "done", "cancelled"]
TRANSIENT, ABSORBING = STATES[:4], STATES[4:]

# Per-state mean sojourn in days (transient states only)
d_bar = np.array([3.0, 4.0, 2.0, 3.0])

# Transition matrix P (row-stochastic)
P = np.array([
    [0.0, 0.9, 0.0, 0.0, 0.0, 0.1],  # backlog     -> in_progress | cancel
    [0.0, 0.0, 0.8, 0.0, 0.0, 0.2],  # in_progress -> review     | cancel
    [0.0, 0.3, 0.0, 0.6, 0.1, 0.0],  # review      -> in_prog | test | done
    [0.0, 0.2, 0.0, 0.0, 0.8, 0.0],  # testing     -> in_prog | done
    [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],  # done (absorbing)
    [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],  # cancelled (absorbing)
])
assert np.allclose(P.sum(axis=1), 1.0), "P is not row-stochastic"

# -----------------------------------------------------------------------------
# Analytical computation
# -----------------------------------------------------------------------------
Q, R = P[:4, :4], P[:4, 4:]
N = np.linalg.inv(np.eye(4) - Q)        # fundamental matrix
B = N @ R                                # absorption probabilities
exp_lt = N @ d_bar                       # expected lead time per starting state

# Quasi-stationary distribution (time-share among transient states)
pi_0 = np.array([1.0, 0.0, 0.0, 0.0])    # start at backlog
qs = (pi_0 @ N) * d_bar
qs /= qs.sum()

# -----------------------------------------------------------------------------
# Monte Carlo cross-validation
# -----------------------------------------------------------------------------
def simulate(P, d_bar, M=10_000, K_max=1000, seed=42):
    rng = np.random.default_rng(seed)
    lt, oc = [], []
    for _ in range(M):
        s, T, k = 0, 0.0, 0
        while s < 4 and k < K_max:
            T += rng.exponential(d_bar[s])
            s = rng.choice(6, p=P[s])
            k += 1
        if s >= 4:
            lt.append(T)
            oc.append(s)
    return np.array(lt), np.array(oc)


if __name__ == "__main__":
    print("=== Analytical ===")
    print("Q =\n", Q)
    print("R =\n", R)
    print("N = (I-Q)^-1 =\n", N)
    print("B = NR =\n", B)
    print(f"\nE[LT | backlog]   = {exp_lt[0]:.4f}")
    print(f"P(Done | backlog) = {B[0,0]:.4f}")
    print(f"P(Cancel | backlog) = {B[0,1]:.4f}")
    print("\nQuasi-stationary (time-share):")
    for s, p in zip(TRANSIENT, qs):
        print(f"  {s:12s} = {p:.4f}")

    print("\n=== Monte Carlo (M=10,000, seed=42) ===")
    lt, oc = simulate(P, d_bar)
    print(f"E[LT]       = {lt.mean():.4f}")
    print(f"Q_0.50      = {np.quantile(lt, 0.50):.4f}")
    print(f"Q_0.85      = {np.quantile(lt, 0.85):.4f}")
    print(f"Q_0.95      = {np.quantile(lt, 0.95):.4f}")
    print(f"P(Done)     = {(oc == 4).mean():.4f}")
    print(f"P(Cancel)   = {(oc == 5).mean():.4f}")
