#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère netlinking.json et audit.json (données Semrush Backlinks + Site Audit)
consommés par l'outil. Les données brutes sont embarquées ci-dessous (snapshot
du relevé) ; pour rafraîchir, ré-exécuter les rapports Semrush et remplacer les
blocs, ou brancher l'API. Domaine : leguide.ancv.com — base FR.
"""
import os, csv, io, json, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------- NETLINKING ----------
OVERVIEW = {
    "leguide.ancv.com": {"ascore": 53, "backlinks": 66373, "refdomains": 2686,
                          "follow": 51976, "nofollow": 14215, "text": 40426, "image": 14735},
    "ancv.com":        {"ascore": 53, "backlinks": 6221320, "refdomains": 7328,
                          "follow": 3824096, "nofollow": 2397677},
}

HISTORICAL = """date;backlinks_num;domains_num
1782878400;6221320;7328
1780286400;6660913;7005
1777608000;6832140;6956
1775016000;6881736;6811
1772341200;6909346;6771
1769922000;6940530;6652
1767243600;7006926;6670
1764565200;7023018;6800
1761969600;7001739;6866
1759291200;7257829;6809
1756699200;7442113;6857
1754020800;7474106;7018
1751342400;7488701;7008
1748750400;7461347;7014
1746072000;7700369;6989"""

REFDOMAINS = """domain;domain_score;backlinks_num;country
yahoo.com;100;49;us
bing.com;97;3;us
service-public.fr;92;4;fr
service-public.gouv.fr;88;8;fr
lefigaro.fr;87;2;
bfmtv.com;86;34;us
francetvinfo.fr;85;1;us
substack.com;85;1;
pagesjaunes.fr;84;1;
caf.fr;82;10;fr
marmiton.org;81;3;us
zendesk.com;81;2;us
20minutes.fr;80;1;us
sncf-connect.com;78;2;
actu.fr;76;15;
rtl.fr;76;2;us
boursorama.com;75;1;fr
economie.gouv.fr;75;3;
paris.fr;75;2;us
sfr.fr;75;1;fr
sudouest.fr;75;4;us
ledauphine.com;74;1;fr
tf1info.fr;74;7;gr
eatbu.com;73;2;us
leprogres.fr;71;1;fr
letelegramme.fr;71;1;
quechoisir.org;71;4;
nicematin.com;70;2;us
education.fr;68;6;us
femmeactuelle.fr;68;3;tr"""

ANCHORS = """anchor;domains_num;backlinks_num
chèques vacances;13;6815
<EmptyAnchor>;106;2444
utiliser vos chèques-vacances papiers et dématérialisés;435;2370
utiliser vos e-chèques-vacances sur l'application chèque-vacances connect;435;2370
demande d'échange de chèques-vacances ou de mise en recherche de titres perdus ou volés;405;2311
utiliser vos chèques-vacances;471;2273
telegram @seo_anomaly - seo backlinks, black-links, traffic boost, link indexing;360;2254
demande d'échange de chèques-vacances périmés ou de mise en recherche de titres perdus ou volés;442;2226
accéder au service en ligne open_in_new;440;2225
utiliser vos e-chèques-vacances;440;2222
ancv;60;1852
demander l'échange de votre coupon sport;447;1116
les coupons sport open_in_new;441;1109
tg @bhs_links - best seo links - https://t.me/bhs_links;279;1034
accessibilité : non conforme;1;967
les hébergements;1;908
les restaurants;1;908
🎈 nos guides voyage !;1;908
🎬 nos vidéos;1;908
> tout le réseau;1;907
le réseau;1;907
les loisirs sportifs;1;907
🍃 voyage 100% nature;1;907
ancv connect;12;899
🧳 nos idées week-ends;1;878"""

# pages du domaine recevant des backlinks (source_url = notre page)
PAGES = """source_url;backlinks_num;domains_num
https://leguide.ancv.com/account/trades/step-1;7009;635
https://leguide.ancv.com/;3589;324
https://leguide.ancv.com/enseignes-cvco;3181;686
https://leguide.ancv.com/ptl/recherche/list?filters%5Bproduits_acceptes%5D%5BCV%5D=CV&location&text&theme;2762;512
https://leguide.ancv.com/inspiration/notre-reseau-de-professionnel-du-tourisme;2248;165
https://leguide.ancv.com/page/coupon-sport-pour-vos-envies-sportives;1426;641
https://leguide.ancv.com/enseignes/hebergements;1020;9
https://leguide.ancv.com/notre-actualite;958;3
https://leguide.ancv.com/inspiration/que-faire-avec-le-cheque-vacances-connect;951;2
https://leguide.ancv.com/inspiration/conseils-aux-voyageurs;940;2
https://leguide.ancv.com/inspiration/activites-cheques-vacances;935;1
https://leguide.ancv.com/enseignes/restaurants;926;8
https://leguide.ancv.com/inspiration/voyage-nature;924;1
https://leguide.ancv.com/enseignes/arts-culture;923;5
https://leguide.ancv.com/inspiration/idee-de-week-end;923;2
https://leguide.ancv.com/inspiration/vacances-au-ski;923;1
https://leguide.ancv.com/enseignes/loisirs-sportifs;918;4
https://leguide.ancv.com/enseignes/voyage-transports;918;3
https://leguide.ancv.com/guides-regions;918;2
https://leguide.ancv.com/guides-voyages;913;1
https://leguide.ancv.com/inspiration/a-la-montagne;913;1
https://leguide.ancv.com/page/cheque-vacances-connect-le-format-digital;763;77
https://leguide.ancv.com/enseignes/arts-culture/billetterie-spectacles;331;139
https://leguide.ancv.com/inspiration/film-halloween;200;195
https://leguide.ancv.com/page/le-e-cheque-vacances-le-chequier-pour-regler-sur-internet;176;2
https://leguide.ancv.com/inspiration/films-cultes;172;171
https://leguide.ancv.com/inspiration/activites-couple;102;101
https://leguide.ancv.com/ptl/recherche/list;76;11
https://leguide.ancv.com/inspiration/lieux-insolites-teletravailler;58;1
https://leguide.ancv.com/inspiration/vacances-insolites-octobre;44;1
https://leguide.ancv.com/enseignes/hebergements/locations-vacances;43;2
https://leguide.ancv.com/inspiration/activite-bien-etre;43;1
https://leguide.ancv.com/inspiration/musee-archeologique;43;1
https://leguide.ancv.com/inspiration/cours-de-cuisine;42;1
https://leguide.ancv.com/inspiration/musee-a-visiter;42;1
https://leguide.ancv.com/inspiration/que-visiter-a-brest;28;1
https://leguide.ancv.com/inspiration/que-visiter-a-toulon;28;1
https://leguide.ancv.com/inspiration/que-visiter-au-havre;28;1
https://leguide.ancv.com/inspiration/que-visiter-grenoble;28;1
https://leguide.ancv.com/inspiration/visiter-caen;28;1
https://leguide.ancv.com/account/contact;24;13
https://leguide.ancv.com/inspiration/randonnee-en-ete;23;1
https://leguide.ancv.com/inspiration/village-autour-de-nice;23;3
https://leguide.ancv.com/inspiration/liste-materiel-journee-randonnee;22;1
https://leguide.ancv.com/inspiration/que-faire-autour-de-bordeaux;22;1
https://leguide.ancv.com/inspiration/que-faire-autour-de-la-rochelle;22;1
https://leguide.ancv.com/inspiration/que-faire-autour-de-marseille;22;3
https://leguide.ancv.com/inspiration/que-faire-la-rochelle;22;1
https://leguide.ancv.com/inspiration/vacances-insolites;21;1
https://leguide.ancv.com/inspiration/beaux-villages-autour-de-toulon;20;1
https://leguide.ancv.com/inspiration/que-faire-autour-de-nice;20;1
https://leguide.ancv.com/inspiration/visiter-verdun;20;3
https://leguide.ancv.com/inspiration/que-faire-en-paca;17;1
https://leguide.ancv.com/inspiration/region-grand-est-france;17;1
https://leguide.ancv.com/page/peut-utiliser-les-cheques-vacances-letranger;17;6
https://leguide.ancv.com/inspiration/cheque-vacances-massage;16;2
https://leguide.ancv.com/inspiration/week-end-pas-cher-europe;16;1
https://leguide.ancv.com/page/le-cheque-vacances-le-format-papier-classique;16;10
https://leguide.ancv.com/inspiration/challenge-24h-chrono;14;2
https://leguide.ancv.com/inspiration/week-end-en-amoureux;14;2
https://leguide.ancv.com/inspiration/journee-patrimoine-bretagne;13;1
https://leguide.ancv.com/inspiration/journee-patrimoine-nantes;13;1
https://leguide.ancv.com/inspiration/journees-du-patrimoine-bordeaux;13;1
https://leguide.ancv.com/inspiration/voyage-nature-famille;13;1
https://leguide.ancv.com/inspiration/balade-velo-lille;12;1
https://leguide.ancv.com/inspiration/balade-velo-strasbourg;12;1
https://leguide.ancv.com/inspiration/balade-velo-vendee;12;1
https://leguide.ancv.com/inspiration/journees-du-patrimoine-angers;12;1
https://leguide.ancv.com/inspiration/journees-du-patrimoine-lille;12;1
https://leguide.ancv.com/inspiration/preparer-sa-valise;12;2
https://leguide.ancv.com/inspiration/preparer-un-voyage;12;4
https://leguide.ancv.com/enseignes/hebergements/campings;11;5
https://leguide.ancv.com/inspiration/voyage-nature-sauvage;11;2
https://leguide.ancv.com/enseignes/hebergements/hotels;10;3
https://leguide.ancv.com/inspiration/cheque-vacances-lyon;10;1
https://leguide.ancv.com/inspiration/itineraire-velo-paris;10;1
https://leguide.ancv.com/inspiration/micro-aventure-paris;10;1
https://leguide.ancv.com/inspiration/que-faire-a-annecy;10;1"""

TOXIC_MARKERS = ["telegram", "t.me", "seo backlinks", "black-links", "@seo", "@bhs",
                 "link indexing", "traffic boost", "best seo links"]

def parse(csvtext):
    return list(csv.DictReader(io.StringIO(csvtext.strip()), delimiter=";"))

def to_int(x):
    try: return int(str(x).strip())
    except: return 0

def build_netlinking():
    hist=[{"date": datetime.datetime.utcfromtimestamp(int(r["date"])).strftime("%Y-%m"),
           "backlinks": to_int(r["backlinks_num"]), "refdomains": to_int(r["domains_num"])}
          for r in parse(HISTORICAL)][::-1]
    refd=[{"domain": r["domain"], "ascore": to_int(r["domain_score"]),
           "backlinks": to_int(r["backlinks_num"]), "country": r.get("country","")}
          for r in parse(REFDOMAINS)]
    anchors=[]
    for r in parse(ANCHORS):
        a=r["anchor"]
        toxic=any(m in a.lower() for m in TOXIC_MARKERS)
        anchors.append({"anchor": a, "domains": to_int(r["domains_num"]),
                        "backlinks": to_int(r["backlinks_num"]), "toxic": toxic})
    pages={}
    for r in parse(PAGES):
        u=r["source_url"].split("?")[0].rstrip("/")
        bl=to_int(r["backlinks_num"]); rd=to_int(r["domains_num"])
        if u not in pages or bl>pages[u]["bl"]:
            pages[u]={"bl": bl, "rd": rd}
    ov=OVERVIEW["leguide.ancv.com"]
    return {
        "generated": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "domain": "leguide.ancv.com",
        "overview": OVERVIEW,
        "historical": hist,
        "refdomains": refd,
        "anchors": anchors,
        "toxic_backlinks": sum(a["backlinks"] for a in anchors if a["toxic"]),
        "pages": pages,
    }

# ---------- SITE AUDIT ----------
AUDIT_SCORE=80; PAGES_CRAWLED=332; AUDIT_DATE="2026-07-18"
# checks de maillage interne (vert = 0 problème)
INTERNAL_CHECKS=[
    {"id":213,"title":"Pages avec un seul lien interne","count":0},
    {"id":212,"title":"Profondeur de clic > 3","count":0},
    {"id":8,"title":"Liens internes cassés","count":0},
    {"id":108,"title":"Trop de liens sur la page","count":0},
    {"id":123,"title":"Liens internes en nofollow","count":0},
    {"id":207,"title":"Pages orphelines (sitemap)","count":0},
    {"id":206,"title":"Pages orphelines (Analytics)","count":0},
]
# autres problèmes on-page / technique (count>0)
ISSUES=[
    {"title":"Pages en erreur 4xx","count":25,"sev":"error"},
    {"title":"Balises title en double","count":2,"sev":"error"},
    {"title":"Liens externes cassés","count":10,"sev":"warning"},
    {"title":"Méta-descriptions manquantes","count":261,"sev":"warning"},
    {"title":"Faible ratio texte/HTML","count":261,"sev":"warning"},
    {"title":"Underscores dans l'URL","count":256,"sev":"warning"},
    {"title":"Pages non compressées","count":261,"sev":"warning"},
    {"title":"JS/CSS non compressés","count":2088,"sev":"warning"},
    {"title":"JS/CSS non minifiés","count":261,"sev":"warning"},
    {"title":"Faible nombre de mots","count":13,"sev":"warning"},
    {"title":"Plusieurs balises H1","count":259,"sev":"notice"},
    {"title":"Liens sans texte d'ancre","count":41,"sev":"notice"},
]
FOURXX="""url
https://leguide.ancv.com/ptl/voyages_transports/transports_maritimes/labaladeuzh_baladeenmer/808047001001
https://leguide.ancv.com/ptl/restauration/restauration/restaurant_les_grottes/627094001001
https://leguide.ancv.com/ptl/restauration/restauration/restaurant_le_moulin_du_gapeau/766701001001
https://leguide.ancv.com/ptl/restauration/restauration/restaurant_le_bouchon_nivernais/604150001001
https://leguide.ancv.com/ptl/restauration/restauration/restaurant_la_fine_heure/357279001001
https://leguide.ancv.com/ptl/restauration/restauration/la_bouillabaisse_port_de_la_madrague_presqu_ile_de_giens/72568100100
https://leguide.ancv.com/ptl/restauration/restauration/gabrielle/755732001001
https://leguide.ancv.com/ptl/restauration/restauration/brasserie_georges_1836/022058001001
https://leguide.ancv.com/ptl/restauration/restauration/a_merendella_citadina/687434001001
https://leguide.ancv.com/ptl/loisirs_sportifs/sports_nautiques/as_gerardmer_canoe_kayak/633091001001
https://leguide.ancv.com/ptl/loisirs_sportifs/sports_aquatiques/pole_plongee_normandie/301374001001
https://leguide.ancv.com/ptl/loisirs_sportifs/sports_aquatiques/ecole_plongee_ile_rousse/373844001001
https://leguide.ancv.com/ptl/loisirs_sportifs/sports_a_roulettes/club_cycliste_team_cote_de_granit_rose/713229001001
https://leguide.ancv.com/ptl/hebergement/location_de_vacances/location_meublee_mozziconacci_michel/425592001001
https://leguide.ancv.com/ptl/hebergement/hotellerie_plein_air/camping_auberge_les_ranchisses/029900001001
https://leguide.ancv.com/ptl/hebergement/hotellerie/hotel_restaurant_thalamer_novotel/063796001001
https://leguide.ancv.com/ptl/hebergement/hotellerie/aux_balcons_du_sancy/378545001001
https://leguide.ancv.com/ptl/arts_culture_decouverte/structure_de_loisirs/virtualtimeparischatelet_jeuxescapegamesenrealitevirtuelle/795584001001
https://leguide.ancv.com/ptl/arts_culture_decouverte/spectacles/fete_des_remparts/058169001001
https://leguide.ancv.com/ptl/arts_culture_decouverte/sitenaturel_urbain/la_cite_de_la_mer/181639001001
https://leguide.ancv.com/ptl/arts_culture_decouverte/sitenaturel_urbain/champagne_a._viot_et_fils/767380001001
https://leguide.ancv.com/ptl/arts_culture_decouverte/parcs_animaliers/marineland/061072001001
https://leguide.ancv.com/ptl/arts_culture_decouverte/monuments/nimes_romaine/100734008008
https://leguide.ancv.com/ptl/arts_culture_decouverte/monuments/chateau_et_domaine_national_de_chambord/415454001001
https://leguide.ancv.com/ptl/arts_culture_decouverte/expos_et_musees/la_grande_saline/427534001001"""

def build_audit():
    fourxx=[r["url"] for r in parse(FOURXX)]
    return {
        "generated": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "domain": "leguide.ancv.com",
        "audit_date": AUDIT_DATE,
        "score": AUDIT_SCORE,
        "pages_crawled": PAGES_CRAWLED,
        "internal_checks": INTERNAL_CHECKS,
        "issues": ISSUES,
        "errors_4xx": fourxx,
    }

def main():
    nl=build_netlinking(); au=build_audit()
    json.dump(nl, open(os.path.join(ROOT,"netlinking.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(au, open(os.path.join(ROOT,"audit.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    print("netlinking.json:", len(nl["pages"]), "pages,", len(nl["refdomains"]), "refdomains,", len(nl["anchors"]), "ancres")
    print("audit.json:", len(au["errors_4xx"]), "pages 4xx,", len(au["issues"]), "problèmes")

if __name__=="__main__":
    main()
