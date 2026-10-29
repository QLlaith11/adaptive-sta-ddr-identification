"""Adaptive vs constant-gain (oracle) observer under current-sensor noise: accuracy and speed-estimate bias.
One noise level per call -> results/noise_sweep/sigma_<s>mA<tag>.json. Seeds are shared between the two
observers (paired design). sigma = 0 is deterministic, so a single run is used."""
from common import parser, run_parallel, save

p = parser(__doc__)
p.add_argument('--sigma-mA', type=float, default=5.0)
p.add_argument('--n-trials', type=int, default=20)
p.add_argument('--seed0', type=int, default=200)
p.add_argument('--tag', default='')
a = p.parse_args()
s = a.sigma_mA
n_tr, T = (2, 2.0) if a.quick else (a.n_trials, 4.0)
tasks = [dict(sigma_i=s / 1000.0, sigma_mA=s, observer=obs, seed=a.seed0 + k, T=T)
         for obs in ('adaptive', 'fixed') for k in range(1 if s == 0 else n_tr)]
save(f'noise_sweep/sigma_{s:g}mA{a.tag}.json', dict(runs=run_parallel(tasks, a.jobs)), a.quick)
