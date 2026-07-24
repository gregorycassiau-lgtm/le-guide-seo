#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère data.json à partir d'un export « Position Tracking - Rankings overview »
de Semrush (CSV). Cet export contient TOUT : position, URL positionnée, type de
résultat (SERP feature), tags, intention, volume, KD, CPC.

C'est la source recommandée : elle inclut les positions réelles suivies.

Usage :
  python scripts/build_from_csv.py [chemin_csv]
Par défaut, prend le CSV le plus récent dans data/ (nom contenant
« position_tracking » ou « semrush_export »).
"""
import os, sys, csv, glob, json, datetime, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "data.json")

INTENT = {"i": "Informationnel", "n": "Navigation", "c": "Commercial", "t": "Transactionnel"}
TYPE = {
    "organic": "Organique", "featured snippet": "Featured snippet",
    "site links": "Sitelinks", "local pack": "Local pack", "": "",
}


def find_csv():
    if len(sys.argv) > 1:
        return sys.argv[1]
    cands = glob.glob(os.path.join(DATA, "*.csv"))
    cands = [c for c in cands if re.search(r"position_tracking|semrush_export|rankings", os.path.basename(c), re.I)]
    if not cands:
        cands = glob.glob(os.path.join(DATA, "*.csv"))
    if not cands:
        sys.exit("Aucun CSV trouvé dans data/.")
    return max(cands, key=os.path.getmtime)


def to_int(x):
    try:
        return int(str(x).strip())
    except (ValueError, TypeError):
        return None


def to_float(x):
    try:
        return float(str(x).strip())
    except (ValueError, TypeError):
        return 0.0


def intent_txt(code):
    if not code:
        return ""
    return ", ".join(INTENT.get(c.strip(), "") for c in code.split("|") if INTENT.get(c.strip()))


def main():
    path = find_csv()
    lines = open(path, encoding="utf-8").read().splitlines()
    hi = next((i for i, l in enumerate(lines) if l.startswith("Keyword,")), 0)
    reader = list(csv.reader(lines[hi:]))
    hdr = reader[0]
    # repérage des colonnes par motif (les noms contiennent la date)
    def col(pattern, default=None):
        for i, h in enumerate(hdr):
            if re.search(pattern, h, re.I):
                return i
        return default
    c_kw = 0
    c_pos = col(r"_\d{8}$", 1)                    # position du jour
    c_type = col(r"_type$", 3)
    c_land = col(r"_landing$", 4)
    c_diff = col(r"_difference$", 5)
    c_tags = col(r"^Tags$", 7)
    c_int = col(r"^Intents$", 8)
    c_cpc = col(r"^CPC$", 9)
    c_vol = col(r"^Search Volume$", 10)
    c_kd = col(r"^Keyword Difficulty$", 11)

    rows, disp = [], []
    for r in reader[1:]:
        if len(r) <= c_kd or not r[c_kw].strip():
            continue
        kw = r[c_kw].strip()
        disp.append(kw)
        pos = to_int(r[c_pos]) if c_pos is not None else None
        diff = to_int(r[c_diff]) if c_diff is not None else 0
        prev = (pos + diff) if (pos is not None and diff not in (None,)) else None
        cpc = r[c_cpc].strip() if c_cpc is not None else ""
        rows.append({
            "kw": kw,
            "vol": to_int(r[c_vol]) or 0,
            "kd": to_int(r[c_kd]),
            "intent": intent_txt(r[c_int] if c_int is not None else ""),
            "cpc": 0.0 if cpc in ("", "n/a") else to_float(cpc),
            "pos": pos,
            "prev": prev if pos is not None else None,
            "diff": diff if pos is not None else None,
            "type": TYPE.get((r[c_type].strip().lower() if c_type is not None else ""), r[c_type].strip() if c_type is not None else ""),
            "tags": (r[c_tags].strip() if c_tags is not None else ""),
            "url": (r[c_land].strip() if c_land is not None else ""),
        })

    # période depuis l'entête méta
    period = ""
    for l in lines[:hi]:
        if l.lower().startswith("period:"):
            period = l.split(":", 1)[1].strip()
    ranked = sum(1 for r in rows if r["pos"] is not None)
    payload = {
        "generated": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "source": "Semrush Position Tracking (export)",
        "period": period,
        "count": len(rows),
        "ranked": ranked,
        "rows": rows,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    # met aussi à jour keywords.txt (pour un éventuel refresh API)
    with open(os.path.join(DATA, "keywords.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(disp) + "\n")
    print("OK — %d mots-clés (%d positionnés), période %s" % (len(rows), ranked, period))
    print("Écrit:", OUT)


if __name__ == "__main__":
    main()
