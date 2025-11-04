# Changelog

Tous les changements notables de ParcimonIA sont documentés dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

---

## [1.0.0] - 2025-01-04

### 🎉 Version initiale

Première version publique de ParcimonIA - Router intelligent pour OpenWebUI.

### ✨ Ajouté

#### Routage intelligent
- Évaluation automatique de la complexité des requêtes via `gpt-5-nano`
- Sélection dynamique entre `gpt-5-mini` (économique) et `gpt-5` (performant)
- Décision basée sur l'analyse sémantique de chaque requête utilisateur

#### Continuité conversationnelle
- Détection automatique du modèle utilisé dans les messages précédents
- Maintien du même modèle tout au long d'une conversation (configurable)
- Extraction intelligente via regex du modèle dans l'historique

#### Configuration flexible (Valves)
- Support de l'API OpenAI avec clé personnalisée
- Configuration des modèles light/heavy/routing
- Options de debug et d'affichage personnalisables
- Paramètre `KEEP_MODEL_IN_CONVERSATION` pour la continuité

#### Observabilité
- Affichage du modèle sélectionné au début de chaque réponse
- Mode debug détaillé avec prompt, réponse brute et analyse du routeur
- Logs de continuité indiquant si le modèle est réutilisé ou nouvellement analysé
- Tracking des erreurs avec détails techniques

#### Streaming
- Support natif du streaming OpenAI pour réponses en temps réel
- Gestion différenciée des paramètres `max_tokens` vs `max_completion_tokens`
- Détection automatique des modèles GPT-5 pour paramétrage approprié

#### Robustesse
- Gestion des erreurs HTTP avec messages explicites
- Fallback automatique vers `gpt-5-mini` en cas d'échec du routage
- Timeout configuré (30s pour routage, 600s pour génération)
- Validation des réponses API avec gestion des cas limites

### 🔧 Technique

- Framework : Pydantic pour validation des configurations
- API : Requests avec support streaming
- Compatibilité : OpenWebUI pipe architecture
- Langage : Python 3.8+

### 📝 Documentation

- README complet avec cas d'usage détaillés
- Exemples de logs et économies estimées
- Guide de configuration des Valves
- Instructions d'installation pas-à-pas

### 📜 Licence

- Projet sous licence Apache-2.0
- Copyright © 2025 TBDwarf - Tommy RENAULT

---

**Légende des types de changements :**
- `✨ Ajouté` : nouvelles fonctionnalités
- `🔧 Modifié` : changements de fonctionnalités existantes
- `🗑️ Déprécié` : fonctionnalités bientôt supprimées
- `🔥 Supprimé` : fonctionnalités retirées
- `🐛 Corrigé` : corrections de bugs
- `🔒 Sécurité` : corrections de vulnérabilités
