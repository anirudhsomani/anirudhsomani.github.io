"""Adds any new Ken stories to the Writing list on index.html.
Existing rows are never rewritten, so hand edits to titles stay. Keeps the newest 5."""
import re, sys, urllib.request, html
from datetime import datetime

URL = "https://the-ken.com/writers/anirudh-s-somanigmail-com/"
PAGE = "index.html"
KEEP = 5

def fetch():
    if len(sys.argv) > 1:
        return open(sys.argv[1], encoding="utf-8", errors="ignore").read()
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (site updater)"})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")

def stories(src):
    out = []
    for m in re.finditer(r'data-article-published-date="(\d\d)-(\d\d)-(\d\d)".*?<a href="([^"]+)".*?class="article-title"><span>(.*?)</span>', src, re.S):
        yy, mm, dd, url, title = m.groups()
        title = html.unescape(re.sub(r"<[^>]+>", "", title)).strip()
        title = title.replace("\u2019", "'").replace("\u2018", "'").replace("\u2014", ", ").replace("  ", " ")
        d = datetime(2000 + int(yy), int(mm), int(dd))
        label = "Ka-Ching, The Ken" if "/kaching/" in url else "The Ken"
        out.append((d, url, title, label))
    return out

def row(d, url, title, label):
    return ('      <a class="row" href="%s" target="_blank" rel="noopener"><div class="top"><span class="t">%s</span>'
            '<span class="d">%s</span></div><p class="s">%s</p></a>') % (url, html.escape(title, quote=False), d.strftime("%b %Y"), label)

def main():
    page = open(PAGE, encoding="utf-8").read()
    m = re.search(r"(<!-- KEN:START -->\n)(.*?)(<!-- KEN:END -->)", page, re.S)
    if not m:
        print("markers not found"); return
    block = m.group(2)
    have = set(re.findall(r'href="([^"]+)"', block))
    rows = [(l, None) for l in block.strip("\n").split("\n") if l.strip()]
    found = sorted(stories(fetch()), key=lambda s: s[0], reverse=True)
    if not found:
        print("no stories parsed; leaving page alone"); return
    newest_have = None
    new = [s for s in found if s[1] not in have]
    # only add stories newer than the oldest one already shown
    dates = []
    for l, _ in rows:
        dm = re.search(r'<span class="d">(\w{3} \d{4})</span>', l)
        if dm: dates.append(datetime.strptime(dm.group(1), "%b %Y"))
    cutoff = min(dates) if dates else datetime(1900, 1, 1)
    new = [s for s in new if s[0] >= cutoff]
    if not new:
        print("no new stories"); return
    merged = [(s[0], row(*s)) for s in new]
    for l, _ in rows:
        dm = re.search(r'<span class="d">(\w{3} \d{4})</span>', l)
        merged.append((datetime.strptime(dm.group(1), "%b %Y") if dm else datetime(1900, 1, 1), l))
    merged.sort(key=lambda x: x[0], reverse=True)
    body = "\n".join(l for _, l in merged[:KEEP]) + "\n"
    page = page[:m.start(2)] + body + page[m.end(2):]
    open(PAGE, "w", encoding="utf-8").write(page)
    print("added %d new stor%s" % (len(new), "y" if len(new) == 1 else "ies"))

if __name__ == "__main__":
    main()
