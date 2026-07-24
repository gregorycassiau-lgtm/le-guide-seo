# Suivi de positionnement SEO — Le Guide ANCV

Tableau de bord en ligne pour suivre une liste de mots-clés (volume, difficulté KD,
intention, position, position précédente, URL positionnée), avec **mise à jour
automatique hebdomadaire** via GitHub Actions + hébergement Netlify.

## Contenu du dépôt

```
index.html                     Interface (recherche, tri, filtres, export CSV)
data.json                      Données affichées (régénérées chaque semaine)
data/keywords.txt              Liste de mots-clés suivie (une par ligne)
scripts/refresh.py             Récupère les données Semrush et régénère data.json
netlify.toml                   Config Netlify (site statique)
.github/workflows/weekly-update.yml   Rafraîchissement auto tous les lundis 06:00 UTC
```

Pour modifier la liste suivie : éditer `data/keywords.txt` (une ligne = un mot-clé),
committer. Le prochain rafraîchissement prend la nouvelle liste en compte.

## Mise en ligne (une seule fois)

### 1. Pousser sur GitHub
```bash
cd ancv-seo-tracker
git init
git add .
git commit -m "Init suivi SEO Le Guide ANCV"
git branch -M main
git remote add origin https://github.com/<votre-compte>/ancv-seo-tracker.git
git push -u origin main
```

### 2. Connecter à Netlify (déploiement continu)
Sur Netlify : **Add new site → Import an existing project → GitHub →** sélectionner
le dépôt. Réglages de build : *Publish directory* = `.`, *Build command* = vide.
Netlify redéploiera automatiquement à chaque push (donc à chaque mise à jour hebdo).

### 3. Configurer la clé API Semrush (pour le rafraîchissement auto)
Dans GitHub : **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Valeur | Obligatoire |
|---|---|---|
| `SEMRUSH_API_KEY` | Votre clé API Semrush (Analytics) | Oui |
| `SEMRUSH_PROJECT_ID` | ID du projet de Suivi de position ANCV | Non* |

\* Sans `SEMRUSH_PROJECT_ID`, les colonnes **volume / KD / intention** sont remplies
pour toute la liste, mais **position / position précédente** restent vides (« n/p »).
Avec un `SEMRUSH_PROJECT_ID` auquel la clé API a accès, les positions réelles suivies
sont récupérées automatiquement.

> L'ID du projet est le premier nombre dans l'URL de la campagne Semrush :
> `https://fr.semrush.com/tracking/landscape/<PROJECT_ID>_<CAMPAIGN_ID>.html`
> La clé API doit appartenir au **compte Semrush propriétaire** de ce projet.

## Rafraîchissement

- **Automatique** : tous les lundis à 06:00 UTC (voir le cron dans le workflow).
- **Manuel** : onglet **Actions** du dépôt → *Rafraîchissement hebdomadaire Semrush*
  → **Run workflow**.
- **En local** :
  ```bash
  SEMRUSH_API_KEY=xxxx SEMRUSH_PROJECT_ID=xxxx python scripts/refresh.py
  ```

## Sources de données

- **Analytics API** (`phrase_these`, `phrase_kdi`) : volume, CPC, intention, KD —
  fonctionne avec toute clé API Analytics.
- **Position Tracking API** (`tracking_position_organic`) : position, position
  précédente, URL — nécessite l'accès au projet via la clé API.

Base de données : `fr` (Google France). Modifiable via la variable `SEMRUSH_DATABASE`.
