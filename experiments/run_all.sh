#!/usr/bin/env bash
# Reproduce every number and figure in the paper. Usage: ./run_all.sh [JOBS]
# Wall-clock on a single core: roughly 25 minutes (use JOBS = number of cores to go faster).
# Each step writes its own result file, so an interrupted run can be resumed at the failed step.
set -e
cd "$(dirname "$0")"
JOBS=${1:-1}
python3 verify_crossing.py
python3 verify_transform.py
python3 exp_trajectory.py --jobs "$JOBS"                                   # Table II, Fig. 2
python3 exp_generalization.py --jobs "$JOBS" --start 0 --stop 30           # Table I
python3 exp_generalization.py --jobs "$JOBS" --start 30 --stop 60
python3 exp_end_to_end.py --jobs "$JOBS"                                   # supplementary
python3 exp_speed.py --jobs "$JOBS"                                        # operating-range statement
for s in 0 2 5 10; do python3 exp_noise_sweep.py --jobs "$JOBS" --sigma-mA $s --n-trials 12; done
python3 exp_noise_sweep.py --jobs "$JOBS" --sigma-mA 20 --n-trials 10 --seed0 200 --tag _a   # 30 trials at 20 mA
python3 exp_noise_sweep.py --jobs "$JOBS" --sigma-mA 20 --n-trials 10 --seed0 210 --tag _b
python3 exp_noise_sweep.py --jobs "$JOBS" --sigma-mA 20 --n-trials 10 --seed0 220 --tag _c
python3 make_paper_figures.py                                              # Figs. 1-2
python3 audit_statistics.py                                                # all statistics quoted in the paper
