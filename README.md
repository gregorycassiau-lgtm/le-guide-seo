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
| `SEMRUSH_API_KEY` | Votre clé / PAT Semrush (Subscription info → API units) | Oui |
| `SEMRUSH_COUNTRY` | Code pays, ex. `fr` (défaut : `fr`) | Non |
| `SEMRUSH_MONTH` | Mois `YYYY-MM` (défaut : mois complet précédent) | Non |

> ⚠️ **Ne mettez jamais la clé en clair dans le code ou le README** : utilisez
> uniquement les secrets GitHub. Une clé exposée dans un dépôt doit être régénérée.

## Rafraîchissement

- **Automatique** : tous les lundis à 06:00 UTC (voir le cron dans le workflow).
- **Manuel** : onglet **Actions** du dépôt → *Rafraîchissement hebdomadaire Semrush*
  → **Run workflow**.
- **En local** (ne pas committer la clé) :
  ```bash
  export SEMRUSH_API_KEY="votre_cle"
  python scripts/refresh.py
  ```

## Sources de données

- **Keyword Metrics API v4** (`/apis/v4/keywords/v1/metrics`, auth `Authorization: Apikey`) :
  volume, KD, intention, CPC — un appel par mot-clé. Fonctionne avec un Personal
  Access Token Semrush.
- **Positions** (position, position précédente, URL) : non encore exposées par
  l'API v4. Elles se rempliront quand l'API de Suivi de position sera branchée
  (campagne ayant collecté des données + clé compatible). En attendant : « n/p ».

Base de données : `fr` (Google France). Modifiable via la variable `SEMRUSH_DATABASE`.
