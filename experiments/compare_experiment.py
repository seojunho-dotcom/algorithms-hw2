"""과제: 개별 체이닝 vs 선형 탐지, 같은 키 · 같은 크기(M=4093), 적재율 0.1 ~ 0.9.
실행: make compare  ->  experiments/compare_results.csv, experiments/compare_graph.svg"""
import random

from experiments.common import M, print_table, run, write_csv, write_svg
from src.hash_table import HashTable, LinearProbingTable

ALPHAS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
TRIALS = 20

if __name__ == "__main__":
    random.seed(2024)
    methods = {
        "chaining": lambda: HashTable(M, max_load=None),
        "linear": lambda: LinearProbingTable(M, max_load=None),
    }
    rows = run(methods, ALPHAS, TRIALS)
    write_csv(rows, "experiments/compare_results.csv")
    write_svg(rows, "experiments/compare_graph.svg", [0.1, 0.3, 0.5, 0.7, 0.9], TRIALS, fail_log=True)
    print_table(rows)
