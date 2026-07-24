# Suivi de positionnement SEO — Le Guide ANCV

Tableau de bord en ligne pour suivre la campagne de mots-clés du projet Semrush
(position, évolution, URL positionnée, type de résultat SERP, tags, intention,
volume, difficulté KD), hébergé sur Netlify.

## Contenu du dépôt

```
index.html                     Interface (recherche, tri, filtres, export CSV)
data.json                      Données affichées (générées depuis l'export Semrush)
data/semrush_export.csv        Export « Position Tracking – Rankings overview » (SOURCE)
data/keywords.txt              Liste des mots-clés (régénérée depuis l'export)
scripts/build_from_csv.py      Génère data.json depuis l'export CSV  ← principal
scripts/refresh.py             (Optionnel) rafraîchit volume/KD/intention via l'API
netlify.toml                   Config Netlify (build = build_from_csv.py)
.github/workflows/weekly-update.yml   (Optionnel) refresh métriques via API
```

## Comment ça se met à jour

La **source de vérité est l'export Semrush** (`data/semrush_export.csv`), car lui
seul contient les **positions réelles suivies** (+ URL, type SERP, tags).

Boucle de mise à jour recommandée :

1. Dans Semrush → projet de Suivi de position → onglet **Rankings/Overview** →
   **Export** (CSV). Astuce : Semrush permet de **programmer cet export par e-mail**
   (hebdomadaire).
2. Remplacer `data/semrush_export.csv` par le nouvel export, puis committer/pousser.
3. Au déploiement, Netlify exécute `python3 scripts/build_from_csv.py` (voir
   `netlify.toml`), qui régénère `data.json`. Le site est à jour automatiquement.

> Le fichier d'export peut porter n'importe quel nom contenant `position_tracking`,
> `rankings` ou `semrush_export` : le script prend le plus récent dans `data/`.

## Mise en ligne (une seule fois)

### 1. Pousser sur GitHub
```bash
cd ancv-seo-tracker
git init && git add . && git commit -m "Init suivi SEO Le Guide ANCV"
git branch -M main
git remote add origin https://github.com/<votre-compte>/ancv-seo-tracker.git
git push -u origin main
```

### 2. Connecter à Netlify
**Add new site → Import an existing project → GitHub →** sélectionner le dépôt.
Réglages : *Build command* = `python3 scripts/build_from_csv.py`, *Publish directory* = `.`
(déjà dans `netlify.toml`). Netlify redéploie à chaque push.

### Rebuild en local
```bash
python3 scripts/build_from_csv.py       # régénère data.json depuis l'export
```

## (Optionnel) Rafraîchir volume / KD / intention via l'API

Utile pour actualiser les métriques entre deux exports **sans toucher aux positions**
(elles sont préservées). Nécessite une clé/PAT Semrush.

- Secret GitHub : `SEMRUSH_API_KEY` (Subscription info → API units).
- Manuel : onglet **Actions** → *Refresh métriques (API)* → **Run workflow**.
- Local :
  ```bash
  export SEMRUSH_API_KEY="votre_cle"
  python3 scripts/refresh.py
  ```

> ⚠️ Ne mettez jamais la clé en clair dans le code : uniquement en secret GitHub.
> Une clé exposée doit être régénérée.

Endpoint métriques : `GET /apis/v4/keywords/v1/metrics` (auth `Authorization: Apikey`),
base `fr` par défaut (variable `SEMRUSH_COUNTRY`).
