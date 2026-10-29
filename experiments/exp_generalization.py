"""Table I: accuracy over random unseen plants, same observer constants, no retuning.
Runs plants [start, stop) and writes a part file; when all parts exist, the merged summary is written."""
import glob, json
import numpy as np
from common import parser, run_parallel, save, RESULTS

p = parser(__doc__)
p.add_argument('--n-plants', type=int, default=60)
p.add_argument('--start', type=int, default=0)
p.add_argument('--stop', type=int, default=None)
a = p.parse_args()
N, T = (4, 2.0) if a.quick else (a.n_plants, 4.0)
stop = N if a.stop is None else a.stop

rng = np.random.default_rng(42)
m = rng.uniform(1.0, 6.0, N)
Iz = rng.uniform(0.01, 0.08, N)
Jw = rng.uniform(5e-5, 2e-4, N)
rows = run_parallel([dict(plant=i, m=m[i], Iz=Iz[i], Jw=Jw[i], seed=i, T=T) for i in range(a.start, stop)], a.jobs)
save(f'generalization/part_{a.start:02d}_{stop:02d}.json', dict(runs=rows), a.quick)

if a.quick:
    raise SystemExit
allrows = sorted((r for f in glob.glob(str(RESULTS / 'generalization' / 'part_*.json')) for r in json.load(open(f))['runs']),
                 key=lambda r: r['plant'])
if len(allrows) == N:
    obs = np.array([r['obs_rms_pct'] for r in allrows])
    brng = np.random.default_rng(0)
    boot = np.array([obs[brng.integers(0, N, N)].mean() for _ in range(5000)])
    summ = {}
    for key, label in [('obs_rms_pct', 'Observer RMS error'), ('a_err', 'alpha error'),
                       ('beta_err_norm', 'beta error (normalized by alpha_true)'), ('v_err', 'b error')]:
        x = np.array([r[key] for r in allrows])
        summ[label] = dict(mean=float(x.mean()), std=float(x.std()), max_abs=float(np.abs(x).max()))
        print(f'{label:40s} mean={x.mean():7.3f} std={x.std():6.3f} max|.|={np.abs(x).max():6.3f}')
    ci = [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]
    print('bootstrap 95% CI of mean observer error:', ci)
    save('generalization.json', dict(summary=summ, bootstrap_ci_obs_mean=ci, runs=allrows))
else:
    print(f'{len(allrows)}/{N} plants done; run the remaining part to produce the merged summary')
