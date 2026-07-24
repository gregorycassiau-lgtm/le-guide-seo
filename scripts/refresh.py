#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rafraîchit data.json à partir de l'API Semrush pour la liste de mots-clés
suivie (data/keywords.txt).

Métriques (volume, KD, intention, CPC) : API Semrush v4
  GET https://api.semrush.com/apis/v4/keywords/v1/metrics
  Auth : en-tête  Authorization: Apikey <clé>
  (Personal Access Token, onglet Subscription info > API units.)

Positions (position, position précédente, URL) : nécessitent que la campagne
de Suivi de position ait déjà collecté des données ET une clé compatible avec
l'API v3 Position Tracking. Tant que ce n'est pas disponible, les colonnes de
position restent nulles (« n/p »). Voir README.

Variables d'environnement :
  SEMRUSH_API_KEY   (obligatoire)  clé/PAT Semrush
  SEMRUSH_COUNTRY   (def: fr)      code pays (base Google)
  SEMRUSH_MONTH     (def: mois complet précédent, format YYYY-MM)
"""
import os, sys, csv, json, time, datetime, urllib.parse, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

METRICS_URL = "https://api.semrush.com/apis/v4/keywords/v1/metrics"

KEY = os.environ.get("SEMRUSH_API_KEY", "").strip()
COUNTRY = os.environ.get("SEMRUSH_COUNTRY", "fr").strip()
WORKERS = int(os.environ.get("SEMRUSH_WORKERS", "5"))

def default_month():
    t = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
    return t.strftime("%Y-%m")

MONTH = os.environ.get("SEMRUSH_MONTH", "").strip() or default_month()

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KW_FILE = os.path.join(ROOT, "data", "keywords.txt")
OUT = os.path.join(ROOT, "data.json")

INTENT_LABEL = {
    "INFORMATIONAL": "Informationnel",
    "NAVIGATIONAL": "Navigation",
    "COMMERCIAL": "Commercial",
    "TRANSACTIONAL": "Transactionnel",
}


def norm(s):
    return " ".join(s.strip().lower().split())


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


def keyword_metrics(keyword):
    """Retourne dict {vol,kd,intent,cpc} ou None."""
    q = urllib.parse.urlencode({"keyword": keyword, "country": COUNTRY, "month": MONTH})
    req = urllib.request.Request(
        METRICS_URL + "?" + q,
        headers={"Authorization": "Apikey " + KEY, "User-Agent": "ancv-seo-tracker/1.0",
                 "Accept": "application/json"},
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                d = json.loads(r.read().decode("utf-8", "replace")).get("data", {})
            intents = d.get("intents") or []
            intent = ", ".join(INTENT_LABEL.get(x, "") for x in intents if INTENT_LABEL.get(x))
            kd = d.get("keyword_difficulty")
            return {
                "vol": int(d.get("search_volume") or 0),
                "kd": int(kd) if kd not in (None, "") else None,
                "intent": intent,
                "cpc": round(float(d.get("cpc") or 0) / 100.0, 2),  # centimes -> unité
            }
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            if e.code == 404:            # pas de données pour ce mot-clé
                return {"vol": 0, "kd": None, "intent": "", "cpc": 0.0}
            if e.code in (429, 500, 502, 503) and attempt < 2:
                time.sleep(2 * (attempt + 1))
                continue
            sys.stderr.write("HTTP %s pour %r : %s\n" % (e.code, keyword, body[:120]))
            return None
        except Exception as e:
            if attempt < 2:
                time.sleep(1.5)
                continue
            sys.stderr.write("Erreur %r : %s\n" % (keyword, e))
            return None


def main():
    if not KEY:
        sys.exit("SEMRUSH_API_KEY manquante.")
    display = load_keywords()
    print("Mots-clés:", len(display), "| pays:", COUNTRY, "| mois:", MONTH)

    def work(item):
        raw, k = item
        m = keyword_metrics(raw) or {"vol": 0, "kd": None, "intent": "", "cpc": 0.0}
        return {
            "kw": raw, "vol": m["vol"], "kd": m["kd"], "intent": m["intent"], "cpc": m["cpc"],
            "pos": None, "prev": None, "diff": None, "url": "",
        }

    rows = []
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for r in ex.map(work, display):
            rows.append(r)
    ok = sum(1 for r in rows if r["vol"] or r["kd"])

    payload = {
        "generated": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "country": COUNTRY, "month": MONTH,
        "count": len(rows),
        "ranked": sum(1 for r in rows if r["pos"] is not None),
        "with_data": ok,
        "rows": rows,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print("OK — %d mots-clés avec données, écrit %s" % (ok, OUT))


if __name__ == "__main__":
    main()
