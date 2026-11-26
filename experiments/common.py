"""실험 공통: 키 만들기, 이론값, CSV, SVG 그래프 (표준 라이브러리만)."""
import csv
import math
import random
import string

M = 4093
FAIL_QUERIES = 2000

COLORS = {"chaining": "#2563eb", "linear": "#d97706"}
LABELS = {"chaining": "개별 체이닝 (비교한 노드 수)", "linear": "선형 탐지 (들여다본 칸 수)"}


def make_keys(n, tag):
    """tag(.com / .net)로 끝을 달리해서 저장한 키와 없는 키가 겹치지 않는다."""
    chars = string.ascii_letters + string.digits
    out = []
    for i in range(n):
        s = "".join(random.choice(chars) for _ in range(random.randint(20, 40)))
        out.append(f"https://www.{s}{i}.{tag}")
    return out


def theory(method, a):
    """(성공 탐색, 실패 탐색) 이론값."""
    if method == "chaining":
        return 1 + a / 2, a
    return (1 + 1 / (1 - a)) / 2, (1 + 1 / (1 - a) ** 2) / 2


def measure(make_table, present, absent):
    t = make_table()
    for i, k in enumerate(present):
        t.put(k, i)
    for i, k in enumerate(present):  # 저장한 키는 모두 찾아야 한다
        value, _ = t.search(k)
        assert value == i, "stored key not found"
    s = sum(t.search(k)[1] for k in present) / len(present)
    f = sum(t.search(k)[1] for k in absent) / len(absent)
    return s, f


def run(methods, alphas, trials):
    """methods: {이름: 테이블 만드는 함수}. 같은 키를 모든 방식에 쓴다."""
    rows = []
    for a in alphas:
        n = round(a * M)
        acc = {m: [0.0, 0.0] for m in methods}
        for _ in range(trials):
            present = make_keys(n, "com")
            absent = make_keys(FAIL_QUERIES, "net")
            for m, make_table in methods.items():
                s, f = measure(make_table, present, absent)
                acc[m][0] += s / trials
                acc[m][1] += f / trials
        for m in methods:
            ts, tf = theory(m, n / M)
            rows.append({"method": m, "alpha": round(n / M, 4), "n": n,
                         "success_exp": round(acc[m][0], 4), "success_theory": round(ts, 4),
                         "fail_exp": round(acc[m][1], 4), "fail_theory": round(tf, 4)})
    return rows


def write_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def print_table(rows):
    print(f"{'방식':<9}{'α':>6}{'성공(실험)':>11}{'성공(이론)':>11}{'실패(실험)':>11}{'실패(이론)':>11}")
    for r in rows:
        print(f"{r['method']:<9}{r['alpha']:>6.2f}{r['success_exp']:>11.3f}{r['success_theory']:>11.3f}"
              f"{r['fail_exp']:>11.3f}{r['fail_theory']:>11.3f}")


def _panel(x0, y0, w, h, title, rows, key, fail_log, xticks):
    alphas = [r["alpha"] for r in rows]
    span = max(alphas) - min(alphas)
    xlo, xhi = min(alphas) - 0.05 * span, max(alphas) + 0.05 * span
    ys = [r[key + s] for r in rows for s in ("_exp", "_theory")]
    log = fail_log and key == "fail"
    if log:
        lo, hi = 0.05, 10 ** math.ceil(math.log10(max(ys)))
        ticks = [t for t in (0.1, 1, 10, 100, 1000) if lo <= t <= hi]
    else:
        lo, hi = 0, math.ceil(max(ys))
        ticks = list(range(0, hi + 1, max(1, hi // 5)))

    def px(a):
        return x0 + (a - xlo) / (xhi - xlo) * w

    def py(v):
        if log:
            return y0 + h - (math.log10(max(v, lo)) - math.log10(lo)) / (math.log10(hi) - math.log10(lo)) * h
        return y0 + h - (v - lo) / (hi - lo) * h

    o = [f'<text x="{x0 + w / 2}" y="{y0 - 14}" text-anchor="middle" font-size="15" font-weight="600">{title}</text>']
    for t in ticks:
        o.append(f'<line x1="{x0}" x2="{x0 + w}" y1="{py(t):.1f}" y2="{py(t):.1f}" stroke="#d1d5db"/>')
        o.append(f'<text x="{x0 - 8}" y="{py(t) + 4:.1f}" text-anchor="end" font-size="12">{t:g}</text>')
    for a in xticks:
        o.append(f'<text x="{px(a):.1f}" y="{y0 + h + 18}" text-anchor="middle" font-size="12">{a:g}</text>')
    o.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="none" stroke="#6b7280"/>')
    o.append(f'<text x="{x0 + w / 2}" y="{y0 + h + 38}" text-anchor="middle" font-size="13">적재율 α</text>')
    for m in COLORS:
        mr = [r for r in rows if r["method"] == m]
        if not mr:
            continue
        pts = " ".join(f'{px(r["alpha"]):.1f},{py(r[key + "_theory"]):.1f}' for r in mr)
        o.append(f'<polyline points="{pts}" fill="none" stroke="{COLORS[m]}" stroke-width="2" stroke-dasharray="6 4"/>')
        for r in mr:
            o.append(f'<circle cx="{px(r["alpha"]):.1f}" cy="{py(r[key + "_exp"]):.1f}" r="4" fill="{COLORS[m]}"/>')
    return "\n".join(o)


def write_svg(rows, path, xticks, trials, fail_log=False):
    W, H = 960, 470
    methods = [m for m in COLORS if any(r["method"] == m for r in rows)]
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
             'font-family="sans-serif" fill="#111827"><rect width="100%" height="100%" fill="#ffffff"/>',
             _panel(70, 50, 380, 290, "성공 탐색 (평균 비용)", rows, "success", fail_log, xticks),
             _panel(540, 50, 380, 290, "실패 탐색 (평균 비용" + (", 로그 축)" if fail_log else ")"),
                    rows, "fail", fail_log, xticks)]
    y = 405
    for i, m in enumerate(methods):
        x = 70 + i * 330
        parts.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{COLORS[m]}"/>'
                     f'<text x="{x + 10}" y="{y + 4}" font-size="12">{LABELS[m]}</text>')
    parts.append(f'<circle cx="730" cy="{y}" r="4" fill="#6b7280"/><text x="740" y="{y + 4}" font-size="12">점 = 실험값</text>')
    parts.append(f'<line x1="820" x2="850" y1="{y}" y2="{y}" stroke="#6b7280" stroke-width="2" stroke-dasharray="6 4"/>'
                 f'<text x="858" y="{y + 4}" font-size="12">이론값</text>')
    parts.append(f'<text x="70" y="445" font-size="12" fill="#4b5563">M = {M}, 적재율마다 {trials}회 평균, '
                 f'실패 탐색 {FAIL_QUERIES}회, 무작위 URL</text></svg>')
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
