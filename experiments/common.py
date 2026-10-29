"""Shared helpers for the experiment scripts."""
import argparse, json, pathlib, sys, time
from concurrent.futures import ProcessPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from ddr_sta.runner import run_task  # noqa: E402

RESULTS = ROOT / 'results'


def parser(desc):
    p = argparse.ArgumentParser(description=desc)
    p.add_argument('--jobs', type=int, default=1, help='parallel worker processes')
    p.add_argument('--quick', action='store_true',
                   help='short smoke-test run (T=2 s, few trials); writes to results/_quick/')
    return p


def run_parallel(tasks, jobs=1):
    t0 = time.time()
    if jobs <= 1:
        outs = [run_task(t) for t in tasks]
    else:
        with ProcessPoolExecutor(max_workers=jobs) as ex:
            outs = list(ex.map(run_task, tasks, chunksize=1))
    print(f'{len(tasks)} runs in {time.time() - t0:.0f} s')
    return [{**t, **o} for t, o in zip(tasks, outs)]


def save(name, payload, quick=False):
    path = RESULTS / ('_quick' if quick else '') / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(payload, f, indent=1)
    print('saved', path)
