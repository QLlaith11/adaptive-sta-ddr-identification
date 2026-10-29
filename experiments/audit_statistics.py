"""Recompute every statistic quoted in the paper from results/*.json (Welch two-sample tests, ddof=1)."""
import json, pathlib
import numpy as np
from scipy import stats

R = pathlib.Path(__file__).resolve().parents[1] / 'results'


def load(n):
    return json.load(open(R / n))


def col(rows, key, **flt):
    return np.array([r[key] for r in rows if all(r[k] == v for k, v in flt.items())])


print('=== Table I (generalization) ===')
g = load('generalization.json')
for k, v in g['summary'].items():
    print(f"{k:42s} mean={v['mean']:7.3f}  std={v['std']:6.3f}  max|.|={v['max_abs']:6.3f}")
print('bootstrap 95% CI, mean observer error:', [round(c, 3) for c in g['bootstrap_ci_obs_mean']])

print('\n=== Noise sweep: adaptive vs constant-gain (Welch t, adaptive - constant) ===')
import glob
ns = [r for f in sorted(glob.glob(str(R / 'noise_sweep' / '*.json'))) for r in json.load(open(f))['runs']]
for s in sorted({r['sigma_mA'] for r in ns}):
    ad = [r for r in ns if r['sigma_mA'] == s and r['observer'] == 'adaptive']
    fx = [r for r in ns if r['sigma_mA'] == s and r['observer'] == 'fixed']
    line = f'sigma={s:4.0f} mA n={len(ad):2d}'
    for key, lab in [('a_err', 'alpha'), ('beta_err_pct', 'beta'), ('v_err', 'b')]:
        x = np.array([r[key] for r in ad]); y = np.array([r[key] for r in fx])
        if len(x) > 1:
            t, pv = stats.ttest_ind(x, y, equal_var=False)
            line += f' | {lab}: ad={x.mean():8.2f} fx={y.mean():8.2f} t={t:8.1f}'
        else:
            line += f' | {lab}: ad={x.mean():8.2f} fx={y.mean():8.2f}'
    ba = np.array([r['bias_R'] for r in ad]); bf = np.array([r['bias_R'] for r in fx])
    line += f' | bias[rad/s] ad={ba.mean():+.3f}  fx={bf.mean():+.3f}'
    print(line)

print('\n=== Speed sweep (adaptive, 5 mA) ===')
sp = load('speed.json')['runs']
for s in sorted({r['u_scale'] for r in sp}):
    rr = [r for r in sp if r['u_scale'] == s]
    print(f"u_scale={s:5.2f} speed~{np.mean([r['speed_scale'] for r in rr]):7.2f} rad/s | obsRMS={np.mean([r['obs_rms_pct'] for r in rr]):6.3f}%"
          f" alpha={np.mean([r['a_err'] for r in rr]):7.3f}% beta={np.mean([r['beta_err_pct'] for r in rr]):7.3f}% b={np.mean([r['v_err'] for r in rr]):8.2f}%")

print('\n=== Table II (trajectories) ===')
tj = load('trajectory.json')
for t in sorted({r['traj'] for r in tj['monte_carlo']}, key=lambda s: ['common_mode', 'min_differential', 'multisine', 'prbs', 'chirp', 'figure_eight'].index(s)):
    rr = [r for r in tj['monte_carlo'] if r['traj'] == t]
    c = [r for r in tj['conditioning'] if r['traj'] == t][0]
    print(f"{t:17s} alpha={np.mean([r['a_err'] for r in rr]):8.3f} beta={np.mean([r['beta_err_pct'] for r in rr]):8.3f} "
          f"b={np.mean([r['v_err'] for r in rr]):8.3f} obsRMS={np.mean([r['obs_rms_pct'] for r in rr]):7.3f} "
          f"sigma_min={c['sigma_min']:.2e} cond={c['cond']:.3g}")
