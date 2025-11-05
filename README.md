# ParcimonIA 🔀💸

> Router OpenWebUI intelligent pour optimiser les coûts d'IA en choisissant automatiquement le meilleur modèle LLM

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)
[![Made in France](https://img.shields.io/badge/Made%20in-France-blue)](https://fr.wikipedia.org/wiki/France)

---

## 📋 Table des matières

- [Présentation](#-présentation)
- [Comment ça marche](#-comment-ça-marche)
- [Cas d'usage](#-cas-dusage)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Résumé financier](#-résumé-financier)
- [Licence](#-licence)

---

## 🎯 Présentation

**ParcimonIA** est un pipe OpenWebUI qui optimise automatiquement vos dépenses d'IA en sélectionnant le modèle le plus pertinent au meilleur coût. 

### Principe

Un nano‑modèle évalue la complexité de chaque requête, puis le routeur `gpt-5-nano` choisit intelligemment entre `gpt-5-mini` (économique) et `gpt-5` (performant) selon vos seuils, budget et politiques configurés.

### Objectif

**Réduire votre facture d'IA** tout en maintenant la qualité perçue par l'utilisateur, avec observabilité complète et mécanismes de fallback.

### Compatibilité

> **Note :** Le code est actuellement conçu pour être utilisé **nativement avec OpenAI** (GPT-5, GPT-5-mini, GPT-5-nano). Cependant, avec quelques modifications mineures du code (notamment au niveau des endpoints API et des paramètres de requête), ParcimonIA peut parfaitement fonctionner avec **d'autres fournisseurs de modèles** comme Anthropic Claude, Mistral AI, ou tout autre LLM compatible avec une API REST.

---

## ⚙️ Comment ça marche

ParcimonIA intercale un "scorer" léger avant chaque appel au modèle principal :

```
[Client] → [Scorer 🧮] → [Router 🔀] → [gpt-5-mini | gpt-5] → [Réponse]
```

### Workflow détaillé

1. **Réception** de la requête utilisateur
2. **Évaluation** par `gpt-5-nano` qui produit un score de complexité (`light` vs `heavy`)
3. **Routage** selon vos règles (seuils, budget, fallbacks) :
   - `light` → **gpt-5-mini** (économique, rapide)
   - `heavy` → **gpt-5** (raisonnement avancé, tâches complexes)
4. **Streaming** de la réponse avec logs détaillés (modèle choisi, score, coût estimé)
5. **Continuité** : si un modèle a déjà été fixé dans l'échange, le routeur le respecte automatiquement

---

## 💡 Cas d'usage

### Cas 1 — Traduction simple (économie automatique)

**Objectif** : Traduire un court paragraphe FR→EN sans mise en forme complexe.

**Prompt utilisateur :**
```
Traduis le texte suivant en anglais, sans changer le sens ni le ton: 
"J'adore les promenades matinales au bord de la Seine."
```

**Décision :**
- `gpt-5-nano` classe la tâche en **light** (faible besoin de raisonnement)
- Le routeur sélectionne **gpt-5-mini**

**Pourquoi c'est pertinent :**
La traduction littérale de courts textes est un cas "pattern-based" où mini offre une qualité perçue proche de gpt-5, pour un coût bien inférieur.

**Log simplifié :**
```yaml
score_complexité: 0.18 → classe: light
modèle: gpt-5-mini
tokens estimés: in=250, out=120
coût estimé: 0,00X €
latence: faible
```

**Économies :** ~90% par rapport à gpt-5 sur ce type de requête

---

### Cas 2 — Génération de code (horloge universelle Python)

**Objectif** : Générer un script robuste affichant l'heure UTC et locale, gérant fuseaux, formatage, arguments CLI et tests.

**Prompt utilisateur :**
```
Écris un script Python "universal_clock.py" qui:
- affiche l'heure UTC et l'heure locale
- accepte un argument --tz pour un fuseau IANA (ex: Europe/Paris)
- gère les erreurs de fuseau
- inclut une fonction main et un petit test docstring
```

**Décision :**
- `gpt-5-nano` classe la tâche en **heavy** (besoin de raisonnement/code structuré)
- Le routeur sélectionne **gpt-5**

**Pourquoi c'est pertinent :**
La génération de code correct avec gestion d'erreurs, interface CLI et tests nécessite plus de planification. GPT-5 couvre mieux les cas limites (TZ invalides, environnement sans tzdata, etc.) et produit une solution plus solide du premier coup, réduisant les itérations.

**Log simplifié :**
```yaml
score_complexité: 0.73 → classe: heavy
modèle: gpt-5
tokens estimés: in=600, out=550
coût estimé: 0,0Y €
latence: modérée
```

**Conclusion :** Pour le code, le raisonnement multi‑étapes, le design d'API ou les intégrations, gpt-5 réduit les allers‑retours et livre un résultat robuste.

---

## 🚀 Installation

### Prérequis

- [OpenWebUI](https://openwebui.com/) installé et configuré
- Clé API OpenAI valide

### Installation via l'interface OpenWebUI

1. **Ouvrez OpenWebUI**
   - Accédez au menu **Panneau d'administration**
   - Cliquez sur l'onglet **Fonctions**

2. **Ajoutez la fonction**
   - Cliquez sur **"Ajouter une fonction"**
   - Copiez/collez le contenu complet du fichier `.py` dans l'éditeur
   - Donnez un nom à la fonction : `ParcimonIA`

3. **Enregistrez**
   - Validez. Le pipe est créé et activé

4. **Configurez l'API**
   - Dans le menu **Vannes**, entrez votre clé d'API OpenAI

5. **Utilisez le pipe**
   - Dans le sélecteur de modèle (zone de chat), sélectionnez **"ParcimonIA"**
   - Discutez normalement, le routage se fait automatiquement !

---

## 🔧 Configuration

### Valves (paramètres configurables)

| Valve | Description | Valeur recommandée |
|-------|-------------|-------------------|
| **OpenAI API Key** | Votre clé d'API pour authentifier les appels | *Votre clé* |
| **OpenAI API Base** | URL de base de l'API | `https://api.openai.com/v1` |
| **Light Model** | Modèle pour tâches simples (traductions, reformulations, résumés) | `gpt-5-mini` |
| **Heavy Model** | Modèle pour tâches complexes (code, raisonnement, intégrations) | `gpt-5` |
| **Routing Model** | Modèle analyseur qui évalue la complexité | `gpt-5-nano` |
| **Debug Routing** | Affiche la réponse complète du routeur (dev/optimisation) | `false` (prod) |
| **Show Model Used** | Affiche quel modèle a été choisi au début de chaque réponse | `true` |
| **Keep Model In Conversation** | Maintient le même modèle tout au long d'un échange | `true` |

### Réglages recommandés (prêts à l'emploi)

```yaml
Light Model: gpt-5-mini
Heavy Model: gpt-5
Routing Model: gpt-5-nano
Debug Routing: false (en production)
Show Model Used: true
Keep Model In Conversation: true
```

### Astuces de forçage manuel

Vous pouvez forcer un modèle spécifique dans votre requête :

- **"Utilise ta capacité light."** → Force `gpt-5-mini`
- **"Utilise ta capacité heavy."** → Force `gpt-5`

---

## 💰 Résumé financier

### Bénéfice clé

**Économies sans friction** : le système décide automatiquement quand utiliser gpt-5-mini (simple) ou gpt-5 (complexe).

### Ordre de grandeur

- Si `gpt-5-mini` est **5–15× moins cher** que `gpt-5`
- Les tâches simples routées vers mini génèrent **80–93% d'économies** par requête
- Sur des centaines/milliers de requêtes simples par mois, l'écart devient **significatif**

### Exemple chiffré

Pour 370 tokens totaux (traduction simple) :
- **Avec gpt-5** : 0,20 €
- **Avec gpt-5-mini** : 0,02 €
- **Économie** : ~0,18 € soit **~90%**

> Les prix réels varient selon votre fournisseur. L'intérêt est de capter automatiquement ces économies sans effort.

### Message à retenir

Le gain principal est de **faire des économies sans effort** sur les tâches simples, tout en **sécurisant la qualité** sur les tâches exigeantes grâce au routage automatique.

---

## 📄 Licence

**Copyright (c) 2025 TBDwarf - Tommy RENAULT**

Ce projet est distribué sous la **Apache License, Version 2.0**.  
Voir le fichier [LICENSE](LICENSE) à la racine du dépôt pour le texte complet.

> Merci de conserver cet avis dans vos distributions :  
> *"ParcimonIA © TBDwarf - Tommy RENAULT — Licence Apache‑2.0."*

---

## 🎭 Pourquoi "ParcimonIA" ?

Le nom **ParcimonIA** est un jeu de mots qui fusionne deux concepts clés du projet :

- **Parcimonie** : qualité de celui qui dépense avec mesure, économie et sagesse.
- **IA** : Intelligence Artificielle, cœur technologique du projet.

**ParcimonIA** incarne ainsi une *IA parcimonieuse* : un système qui optimise intelligemment les ressources en ne mobilisant que la puissance de calcul strictement nécessaire pour chaque tâche.

---
## 🙏 Remerciements

Merci à la communauté OpenWebUI et à tous les contributeurs qui rendent ce projet possible.

**Contributions bienvenues !**

---

<div align="center">

**Fait avec ❤️ en France**

</div>
