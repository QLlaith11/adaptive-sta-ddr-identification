# Adaptive-gain super-twisting observer for sensorless identification of differential-drive robots

Code, simulation results, and manuscript source for the letter *An Adaptive-Gain Super-Twisting Observer for Sensorless Identification of Differential-Drive Robots* (L. Alsheikh, Manara University).

**Problem.** A super-twisting observer can recover wheel speed from motor current (via the back-EMF term), but a constant-gain design needs a numerical bound on wheel acceleration. That bound depends on the chassis mass and inertia, which are the quantities the identification is meant to estimate, so the design is circular.

**Approach.** The bound is replaced by a qualitative boundedness assumption and a boundary-layer adaptive gain law. No plant parameter and no disturbance bound enters the gain law. The letter proves a finite-time gain-crossing result (Proposition III.2) and uses the standard adaptive-gain super-twisting convergence result (Theorem III.3, cited). Speed estimates feed a filtered recursive-least-squares identification of the effective-inertia entries α, β and the viscous coefficient b.

## Repository layout

```
paper/        LaTeX source (ieeeconf class), compiled PDF, figures
src/ddr_sta/  plant, observers (adaptive and constant-gain), RLS pipeline, excitation signals
experiments/  one script per experiment, verification scripts, run_all.sh
results/      JSON outputs used in the paper (raw per-run values)
docs/archive/ earlier development notes (see the note at the top of each file)
```

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd experiments
python3 verify_crossing.py          # Proposition III.2 check (seconds)
python3 exp_generalization.py --quick   # smoke test, writes to results/_quick/ (git-ignored)
python3 audit_statistics.py         # recompute every statistic in the paper from results/
```

Build the paper with `cd paper && make` (needs a TeX Live installation; the bibliography is inline, so no BibTeX step).

## Reproducing the paper

`experiments/run_all.sh [JOBS]` regenerates everything in about 25 minutes on one core.

| Paper item | Script | Output |
|---|---|---|
| Table I (60 random plants) | `exp_generalization.py` | `results/generalization.json` |
| Table II, Fig. 2 (six trajectories) | `exp_trajectory.py`, `make_paper_figures.py` | `results/trajectory.json` |
| Fig. 1 (tracking, adaptive gain) | `make_paper_figures.py` | `paper/fig_paper_tracking.pdf` |
| Discussion: noise sensitivity of b, bias, t-tests | `exp_noise_sweep.py`, `audit_statistics.py` | `results/noise_sweep/` |
| Discussion: operating range | `exp_speed.py` | `results/speed.json` |
| Proposition III.2, error-variable transform | `verify_crossing.py`, `verify_transform.py` | printed |
| Supplementary: end-to-end scenarios | `exp_end_to_end.py` | `results/end_to_end.json` |

Seeds are fixed, so the deterministic experiments reproduce exactly. Noise experiments share seeds between the adaptive and constant-gain observers (paired design); the noise sweep uses 12 trials per design at 2, 5 and 10 mA and 30 at 20 mA, and `audit_statistics.py` reports Welch two-sample tests.

## Scope and limitations

- Simulation only; there is no hardware validation.
- Integration uses a fixed step of 5×10⁻⁵ s and modest Monte Carlo sizes (4 to 30 trials per condition) to keep the full suite tractable. Absolute error magnitudes depend on the step size; comparisons within an experiment use identical settings.
- Theorem III.3 (time-varying-gain convergence) is cited from the adaptive super-twisting literature, with its hypotheses verified for this error dynamics; it is not re-proved here.
- The viscous-damping estimate is sensitive to current-sensor noise because the adaptive observer's speed estimate acquires a noise-dependent bias (discussed in the paper).
- The constant-gain observer in `core_sim.py` is a reference that uses the true acceleration bound; it is not deployable in the identification setting.

## Licenses and notices

- Code: MIT (`LICENSE`).
- `paper/ieeeconf.cls` is the IEEE conference template class, redistributed only so the paper builds; it is not covered by the MIT license.
- The manuscript text and figures in `paper/` are © 2026 L. Alsheikh and subject to the publisher's policies; they are not covered by the MIT license.
