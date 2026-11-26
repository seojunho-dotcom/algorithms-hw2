"""단축 URL 웹 서비스. 표준 모듈 http.server만 사용한다.

실행: make serve   (포트 8000)
      TABLE=linear make serve  -> 짧은 링크 이동에 선형 탐지 테이블을 쓴다
/       URL 입력 폼
/<코드>  원래 주소로 이동
/table  해시 테이블 보기 (?kind=chaining | linear)
"""
import html
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from src.hash_table import HashTable, LinearProbingTable, horner_trace
from src.shortener import Shortener

PORT = 8000
PRIMARY = os.environ.get("TABLE", "chaining")
# 같은 URL을 두 테이블에 모두 넣는다. 코드는 일련번호라 두 쪽이 같다.
SHORTENERS = {
    "chaining": Shortener(HashTable),
    "linear": Shortener(LinearProbingTable),
}
if PRIMARY not in SHORTENERS:
    raise SystemExit("TABLE must be 'chaining' or 'linear'")

CSS = """
body{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem;color:#111}
input[type=text]{width:100%;padding:.6rem;font-size:1rem;box-sizing:border-box}
button{padding:.6rem 1.2rem;font-size:1rem;margin-top:.6rem;cursor:pointer}
.err{color:#b91c1c}.mono{font-family:ui-monospace,monospace;font-size:.85rem;word-break:break-all}
.slot{display:flex;gap:.8rem;align-items:flex-start;padding:.5rem 0;border-top:1px solid #e5e7eb}
.idx{min-width:4.5rem;font-weight:600}.empty{color:#9ca3af}
.chain{display:flex;flex-wrap:wrap;gap:.4rem;align-items:flex-start}
.node{border:1px solid #6b7280;border-radius:6px;padding:.3rem .5rem;background:#f9fafb;max-width:34rem}
.arrow,.null{align-self:center;color:#4b5563}
details summary{cursor:pointer}table.trace{border-collapse:collapse;margin-top:.4rem}
table.trace td,table.trace th{border:1px solid #d1d5db;padding:.15rem .4rem;font-size:.8rem}
nav a{margin-right:1rem}
"""


def page(title, body):
    return (f"<!doctype html><html lang='ko'><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body>"
            f"<nav><a href='/'>단축기</a><a href='/table?kind=chaining'>/table 체이닝</a>"
            f"<a href='/table?kind=linear'>/table 선형 탐지</a></nav>{body}</body></html>")


def home_page(error=None, result=None):
    body = "<h1>URL 단축기</h1>"
    if error:
        body += f"<p class='err'>{html.escape(error)}</p>"
    if result:
        link = html.escape(result)
        body += f"<p>짧은 링크: <a href='{link}'>{link}</a></p>"
    body += ("<form method='post' action='/shorten'>"
             "<input type='text' name='url' placeholder='https://...' autofocus>"
             "<button type='submit'>줄이기</button></form>")
    return page("URL 단축기", body)


def trace_html(key, size):
    rows = "".join(
        f"<tr><td>{html.escape(ch)}</td><td>{code}</td><td>({before} &times; 31 + {code}) mod {size}</td>"
        f"<td>{after}</td></tr>" for ch, code, before, after in horner_trace(key, size))
    return ("<table class='trace'><tr><th>글자</th><th>코드</th><th>h ← (31·h + 코드) mod M</th><th>h</th></tr>"
            f"{rows}</table>")


def node_html(key, code, size, base, extra=""):
    link = f"{base}/{code}"
    final = horner_trace(key, size)[-1][3]
    return (f"<div class='node'><details><summary><span class='mono'>{html.escape(key)}</span><br>"
            f"코드 <b>{html.escape(code)}</b> · <span class='mono'>{html.escape(link)}</span> "
            f"· 해시 = <b>{final}</b>{extra}</summary>"
            f"<div>해시 계산 (M = {size}): 마지막 h가 칸 번호</div>{trace_html(key, size)}</details></div>")


def table_page(kind, base):
    sh = SHORTENERS[kind]
    t = sh.url_to_code
    label = "개별 체이닝" if kind == "chaining" else "선형 탐지"
    body = (f"<h1>해시 테이블 · {label}</h1>"
            f"<p>칸 수 M = {t.size} · 저장된 URL {len(t)}개 · 적재율 {t.load:.2f}"
            f"{' · (짧은 링크 이동에 쓰는 테이블)' if kind == PRIMARY else ''}</p>")
    if kind == "chaining":
        for idx, nodes in t.chains():
            if not nodes:
                body += f"<div class='slot'><div class='idx'>칸 {idx}</div><span class='empty'>비어 있음</span></div>"
                continue
            parts = []
            for key, code in nodes:
                parts.append(node_html(key, code, t.size, base))
                parts.append("<span class='arrow'>→</span>")
            parts.append("<span class='null'>NULL</span>")
            body += (f"<div class='slot'><div class='idx'>칸 {idx}<br><small>길이 {len(nodes)}</small></div>"
                     f"<div class='chain'>{''.join(parts)}</div></div>")
    else:
        for idx, slot in t.entries():
            if slot is None:
                body += f"<div class='slot'><div class='idx'>칸 {idx}</div><span class='empty'>비어 있음</span></div>"
                continue
            key, code = slot
            home = t.index(key)
            path = t.probe_path(key)
            extra = (f"<br>원래 칸 {home} → 실제 칸 {idx} · 들여다본 칸 {len(path)}개: "
                     + " → ".join(str(p) for p in path))
            note = "" if len(path) == 1 else f" <small>(충돌: 칸 {home}에서 밀려남)</small>"
            body += (f"<div class='slot'><div class='idx'>칸 {idx}{note}</div>"
                     f"<div class='chain'>{node_html(key, code, t.size, base, extra)}</div></div>")
    return page(f"/table {label}", body)


def base_url(headers):
    """GitHub 프록시 뒤에서는 Host가 아니라 X-Forwarded-*를 먼저 본다."""
    host = (headers.get("X-Forwarded-Host") or headers.get("Host") or f"localhost:{PORT}").split(",")[0].strip()
    proto = (headers.get("X-Forwarded-Proto") or "http").split(",")[0].strip()
    return f"{proto}://{host}"


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, text, ctype="text/html; charset=utf-8", headers=None):
        data = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/":
            self._send(200, home_page())
        elif url.path == "/table":
            kind = parse_qs(url.query).get("kind", ["chaining"])[0]
            if kind not in SHORTENERS:
                kind = "chaining"
            self._send(200, table_page(kind, base_url(self.headers)))
        else:
            target = SHORTENERS[PRIMARY].resolve(url.path.lstrip("/"))
            if target is None:
                self._send(404, page("없는 링크", "<h1>404</h1><p>없는 짧은 링크입니다.</p>"))
            else:
                self._send(302, "", headers={"Location": target})

    def do_POST(self):
        if urlparse(self.path).path != "/shorten":
            self._send(404, page("404", "<h1>404</h1>"))
            return
        length = min(int(self.headers.get("Content-Length") or 0), 10_000)
        form = parse_qs(self.rfile.read(length).decode("utf-8", "replace"))
        url = form.get("url", [""])[0]
        try:
            codes = {k: s.shorten(url) for k, s in SHORTENERS.items()}
        except ValueError as e:
            self._send(400, home_page(error=f"올바르지 않은 URL입니다 ({e})"))
            return
        self._send(200, home_page(result=f"{base_url(self.headers)}/{codes[PRIMARY]}"))


if __name__ == "__main__":
    print(f"serving on http://localhost:{PORT} (redirect table: {PRIMARY})")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
