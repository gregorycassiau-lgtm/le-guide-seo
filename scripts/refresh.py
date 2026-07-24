#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rafraîchit data.json à partir de l'API Semrush pour la liste de mots-clés
suivie (data/keywords.txt).

Sources Semrush :
  - Analytics API (phrase_these + phrase_kdi) -> volume, CPC, intention, KD
    Fonctionne avec n'importe quelle clé API Analytics.
  - Position Tracking API (tracking_position_organic) -> position, position
    précédente, URL. Nécessite que la clé API ait accès au projet de suivi
    (SEMRUSH_PROJECT_ID). Optionnel : si non configuré ou inaccessible, les
    positions restent nulles.

Variables d'environnement :
  SEMRUSH_API_KEY      (obligatoire)  clé API Semrush
  SEMRUSH_DATABASE     (def: fr)      base régionale
  SEMRUSH_PROJECT_ID   (optionnel)    id du projet de suivi de position
  SEMRUSH_TRACK_URL    (def: *.ancv.com/*)  masque d'URL suivie
"""
import os, sys, csv, io, json, time, datetime, urllib.parse, urllib.request

API = "https://api.semrush.com/"
TRACK_API = "https://api.semrush.com/reports/v1/projects/{pid}/tracking/"

KEY = os.environ.get("SEMRUSH_API_KEY", "").strip()
DB = os.environ.get("SEMRUSH_DATABASE", "fr").strip()
PROJECT_ID = os.environ.get("SEMRUSH_PROJECT_ID", "").strip()
TRACK_URL = os.environ.get("SEMRUSH_TRACK_URL", "*.ancv.com/*").strip()

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KW_FILE = os.path.join(ROOT, "data", "keywords.txt")
OUT = os.path.join(ROOT, "data.json")

INTENT_LABEL = {"0": "Commercial", "1": "Informationnel", "2": "Navigation", "3": "Transactionnel"}


def norm(s):
    return " ".join(s.strip().lower().split())


def http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "ancv-seo-tracker/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def parse_semicolon(text):
    """Parse une réponse CSV Semrush (séparateur ;) en liste de dicts."""
    text = text.strip()
    if not text or text.lower().startswith("error"):
        return []
    rows = list(csv.reader(io.StringIO(text), delimiter=";"))
    if not rows:
        return []
    head = [h.strip() for h in rows[0]]
    out = []
    for r in rows[1:]:
        if len(r) != len(head):
            continue
        out.append(dict(zip(head, r)))
    return out


def load_keywords():
    display, seen = [], set()
    for line in open(KW_FILE, encoding="utf-8"):
        raw = line.strip()
        if not raw:
            continue
        k = norm(raw)
        if k in seen:
            continue
        seen.add(k)
        display.append((raw, k))
    return display


def batched(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def fetch_analytics(keys):
    """Retourne {norm_kw: {vol,kd,intent,cpc}} via phrase_these + phrase_kdi."""
    metrics = {}
    for batch in batched(keys, 90):
        phrase = ";".join(batch)
        # --- volume / cpc / intent ---
        for cols in ("Ph,Nq,Cp,In", "Ph,Nq,Cp"):
            q = urllib.parse.urlencode({
                "type": "phrase_these", "key": KEY, "phrase": phrase,
                "database": DB, "export_columns": cols,
            })
            try:
                rows = parse_semicolon(http_get(API + "?" + q))
            except Exception as e:
                rows = []
            if rows:
                for d in rows:
                    k = norm(d.get("Keyword", d.get("Ph", "")))
                    if not k:
                        continue
                    try:
                        vol = int(float(d.get("Search Volume", d.get("Nq", "0") or 0)))
                    except ValueError:
                        vol = 0
                    try:
                        cpc = float(d.get("CPC", d.get("Cp", "0") or 0))
                    except ValueError:
                        cpc = 0.0
                    intent = d.get("Intent", d.get("In", "")).strip()
                    metrics.setdefault(k, {}).update({"vol": vol, "cpc": cpc, "intent": intent})
                break  # cols worked, stop fallback loop
        # --- keyword difficulty ---
        q = urllib.parse.urlencode({
            "type": "phrase_kdi", "key": KEY, "phrase": phrase,
            "database": DB, "export_columns": "Ph,Kd",
        })
        try:
            rows = parse_semicolon(http_get(API + "?" + q))
        except Exception:
            rows = []
        for d in rows:
            k = norm(d.get("Keyword", d.get("Ph", "")))
            if not k:
                continue
            try:
                kd = round(float(d.get("Keyword Difficulty Index", d.get("Kd", "")) or 0))
            except ValueError:
                kd = None
            metrics.setdefault(k, {})["kd"] = kd if kd else None
        time.sleep(0.4)
    return metrics


def fetch_positions():
    """Retourne {norm_kw: {pos,prev,diff,url}} via Position Tracking, ou {}."""
    if not PROJECT_ID:
        return {}
    q = urllib.parse.urlencode({
        "key": KEY, "action": "report", "type": "tracking_position_organic",
        "url": TRACK_URL, "display_limit": 1000,
    })
    url = TRACK_API.format(pid=PROJECT_ID) + "?" + q
    try:
        rows = parse_semicolon(http_get(url))
    except Exception as e:
        sys.stderr.write("Tracking API indisponible: %s\n" % e)
        return {}
    pos = {}
    for d in rows:
        k = norm(d.get("Keyword", ""))
        if not k:
            continue
        try:
            p = int(d.get("Position", d.get("Ps", "0")) or 0)
        except ValueError:
            continue
        if p <= 0:
            continue
        if k not in pos or p < pos[k]["pos"]:
            def _int(x):
                try:
                    return int(x)
                except (ValueError, TypeError):
                    return None
            prev = _int(d.get("Previous Position", d.get("Pp")))
            pos[k] = {
                "pos": p, "prev": prev,
                "diff": (prev - p) if (prev is not None) else None,
                "url": d.get("Url", d.get("Ur", "")).strip(),
            }
    return pos


def intent_txt(s):
    if not s:
        return ""
    return ", ".join(p for p in (INTENT_LABEL.get(x.strip(), "") for x in s.split(",")) if p)


def main():
    if not KEY:
        sys.exit("SEMRUSH_API_KEY manquante.")
    display = load_keywords()
    keys = [k for _, k in display]
    print("Mots-clés:", len(keys))
    metrics = fetch_analytics(keys)
    print("Métriques récupérées:", len(metrics))
    positions = fetch_positions()
    print("Positions récupérées:", len(positions))

    rows = []
    for raw, k in display:
        m = metrics.get(k, {})
        p = positions.get(k)
        rows.append({
            "kw": raw,
            "vol": m.get("vol", 0),
            "kd": m.get("kd"),
            "intent": intent_txt(m.get("intent", "")),
            "cpc": m.get("cpc", 0.0),
            "pos": p["pos"] if p else None,
            "prev": p["prev"] if p else None,
            "diff": p["diff"] if p else None,
            "url": p["url"] if p else "",
        })

    payload = {
        "generated": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "database": DB,
        "count": len(rows),
        "ranked": sum(1 for r in rows if r["pos"] is not None),
        "rows": rows,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print("Écrit:", OUT)


if __name__ == "__main__":
    main()
