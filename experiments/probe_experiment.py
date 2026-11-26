"""6단계: 칸 수 4093 고정 체이닝 테이블, 적재율 0.25 ~ 4.
실행: make experiment  ->  experiments/results.csv, experiments/probe_graph.svg"""
import random

from experiments.common import M, print_table, run, write_csv, write_svg
from src.hash_table import HashTable

ALPHAS = [0.25, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, 3.5, 4]
TRIALS = 10

if __name__ == "__main__":
    random.seed(2024)
    rows = run({"chaining": lambda: HashTable(M, max_load=None)}, ALPHAS, TRIALS)
    write_csv(rows, "experiments/results.csv")
    write_svg(rows, "experiments/probe_graph.svg", [0.25, 1, 2, 3, 4], TRIALS)
    print_table(rows)
