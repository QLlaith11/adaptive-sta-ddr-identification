"""Effect of the operating wheel-speed range on accuracy (fixed 5 mA sensor noise)."""
from common import parser, run_parallel, save

p = parser(__doc__)
p.add_argument('--n-trials', type=int, default=4)
a = p.parse_args()
scales = [0.1, 0.25, 0.5, 1.0, 2.0, 3.5]
n_tr, T = (2, 2.0) if a.quick else (a.n_trials, 4.0)
if a.quick:
    scales = [0.25, 1.0]
tasks = [dict(u_scale=s, sigma_i=0.005, seed=300 + k, T=T) for s in scales for k in range(n_tr)]
save('speed.json', dict(n_trials=n_tr, runs=run_parallel(tasks, a.jobs)), a.quick)
