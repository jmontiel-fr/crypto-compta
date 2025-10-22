# Générateur de Déclaration Fiscale Crypto - Binance

Programme de génération automatique de déclarations fiscales pour les opérations de cryptomonnaies sur Binance, conforme à la législation française.

## 📋 Description

Ce programme génère un rapport Excel détaillé des plus-values réalisées sur vos opérations de cryptomonnaies via Binance, calculées selon la méthode du **prix moyen pondéré d'acquisition** conformément à l'article 150 VH bis du Code général des impôts.

## ✨ Fonctionnalités

- ✅ Récupération automatique des opérations fiat (dépôts/retraits EUR) via l'API Binance
- ✅ Calcul des valeurs de portefeuille avec snapshots Binance et prix historiques
- ✅ Calcul automatique des plus-values selon la méthode fiscale française
- ✅ Génération de rapport Excel avec formules vérifiables
- ✅ Taux de change historiques officiels (BCE via Frankfurter)
- ✅ Support des balances EUR fiat, cryptos et stablecoins
- ✅ Traçabilité complète et transparence des calculs
- ✅ Option de génération PDF

## 📊 Rapport généré

Le rapport Excel contient :

| Colonne | Description | Type |
|---------|-------------|------|
| Date | Date de l'opération | Donnée |
| Type d'opération | Dépôt ou Retrait | Donnée |
| Montant en EUR | Montant de l'opération | Donnée |
| Valeur portefeuille USD | Valeur du portefeuille en USD | Donnée |
| Taux de change USD/EUR | Taux historique BCE | Donnée |
| Valeur portefeuille EUR | Valeur en EUR | **Formule** |
| Prix d'acquisition restant | Coût d'acquisition | **Formule** |
| Plus-value imposable | Gain imposable | **Formule** |
| Cumul plus-values | Total cumulé | **Formule** |

## 🚀 Installation

### Prérequis

- Python 3.8 ou supérieur
- Compte Binance avec API keys (lecture seule suffisante)

### Installation des dépendances

```bash
pip install -r requirements.txt
```

### Configuration

1. Créez un fichier `binance_keys` à la racine du projet :

```
BINANCE_API_KEY='votre_api_key'
BINANCE_SECRET_KEY='votre_secret_key'
```

2. Créez vos API keys sur Binance :
   - Connectez-vous à Binance
   - Allez dans "API Management"
   - Créez une nouvelle API key
   - **Permissions nécessaires** : Lecture seule (Read Only)
   - **Restrictions IP** : Recommandé pour la sécurité

## 📖 Utilisation

### Génération du rapport

```bash
# Rapport Excel uniquement
python generate_tax_report.py 2025

# Rapport Excel + PDF
python generate_tax_report.py 2025 --pdf
```

Le rapport sera créé dans le dossier `rapports/` :
- `Declaration_Fiscale_Crypto_2025.xlsx`
- `Declaration_Fiscale_Crypto_2025.pdf` (si option --pdf)

### Valeurs manuelles (optionnel)

Pour les opérations anciennes (> 30 jours), vous pouvez fournir des valeurs de portefeuille manuelles pour plus de précision.

Éditez le fichier `portfolio_values_manual.csv` :

```csv
# timestamp,portfolio_value_usd
1724943522000,22.85    # 2025-08-29 14:38:42 - Après dépôt 19.60 EUR
1724950579000,82.30    # 2025-08-29 16:36:19 - AVANT retrait 14.00 EUR
```

## 📐 Méthodologie de calcul

### Principe général

Le programme applique la **méthode du prix moyen pondéré d'acquisition** :

1. **Dépôts** : Augmentent le prix d'acquisition total
2. **Retraits** : Génèrent une plus-value proportionnelle

### Formule de calcul

```
Plus-value = Retrait - (Prix acquisition × (Retrait / Valeur portefeuille))
```

### Valeur du portefeuille

**Pour un DÉPÔT** :
```
Valeur = Actifs existants + Montant déposé (en USD)
```

**Pour un RETRAIT** :
```
Valeur AVANT retrait = Actifs au moment du retrait + Montant retiré (en USD)
```

### Sources de données

- **Snapshots Binance** (< 30 jours) : Données réelles et précises
- **Prix historiques** (> 30 jours) : Approximation avec balances actuelles
- **Taux de change** : BCE via API Frankfurter

## 📄 Documentation fiscale

Pour une explication détaillée de la méthodologie (présentable au fisc), consultez :

📘 **[METHODOLOGIE_CALCUL_FISCAL.md](METHODOLOGIE_CALCUL_FISCAL.md)**

Ce document contient :
- Principe général et base légale
- Définition des opérations
- Méthode de calcul détaillée
- Exemples chiffrés
- Traçabilité et conformité
- Modèle d'attestation

## 🔍 Vérification des calculs

Toutes les formules Excel sont visibles et modifiables :

1. Ouvrez le rapport Excel
2. Cliquez sur une cellule calculée (colonnes F, G, H, I)
3. La formule s'affiche dans la barre de formule
4. Vous pouvez vérifier et modifier si nécessaire

## 📊 Exemple de résultat

```
📊 Summary:
   Total Deposits:     €939.60
   Total Withdrawals:  €14.00
   Total Taxable Gains: €13.04

Impôt dû (30%) : €3.91
```

## ⚠️ Limitations

### Valeurs historiques

Pour les opérations de plus de 30 jours, les snapshots Binance ne sont plus disponibles. Le programme utilise alors une approximation (balances actuelles × prix historiques).

**Solution** : Fournir des valeurs manuelles via `portfolio_values_manual.csv`

### Timing des conversions

Pour les retraits, le moment exact de la conversion crypto → EUR n'est pas toujours connu. Le programme utilise une méthode prudente en ajoutant le montant retiré à la valeur du portefeuille.

## 📁 Structure du projet

```
.
├── generate_tax_report.py          # Script principal
├── binance_keys                     # Vos API keys (à créer)
├── portfolio_values_manual.csv     # Valeurs manuelles (optionnel)
├── requirements.txt                 # Dépendances Python
├── README.md                        # Ce fichier
├── METHODOLOGIE_CALCUL_FISCAL.md   # Documentation fiscale détaillée
├── clients/                         # Clients API
│   ├── binance_client.py
│   └── frankfurter_client.py
├── calculators/                     # Calculateurs
│   ├── flat_tax_calculator.py
│   └── portfolio_calculator.py
├── writers/                         # Générateurs de rapports
│   ├── excel_writer.py
│   └── pdf_writer.py
├── config/                          # Configuration
│   └── config.py
├── utils/                           # Utilitaires
│   └── logger.py
├── logs/                            # Logs d'exécution
└── rapports/                        # Rapports générés
```

## 🔒 Sécurité

- ✅ API keys stockées localement (jamais transmises)
- ✅ Permissions lecture seule suffisantes
- ✅ Pas de stockage de données sensibles
- ✅ Code open source et auditable

## 📝 Déclaration fiscale

### Formulaires à remplir

1. **Formulaire 2086** : Déclaration des plus-values sur actifs numériques
2. **Formulaire 2042 C** : Déclaration complémentaire des revenus

### Montant à déclarer

Le **cumul des plus-values** (dernière ligne du rapport Excel) est à reporter sur le formulaire 2086.

### Impôt

**Flat tax de 30%** :
- 12,8% impôt sur le revenu
- 17,2% prélèvements sociaux

### Conservation des documents

Conservez pendant **6 ans** :
- Le rapport Excel généré
- Les exports Binance
- Les relevés bancaires
- La documentation méthodologique

## 🆘 Support

### Problèmes courants

**"No fiat operations found"**
- Vérifiez que vous avez bien des opérations EUR en 2025
- Vérifiez les permissions de vos API keys

**"Rate limit exceeded"**
- Attendez quelques minutes
- Binance limite le nombre de requêtes API

**Valeurs incohérentes**
- Pour les dates anciennes, fournissez des valeurs manuelles
- Vérifiez les logs dans `logs/tax_report_YYYY.log`

### Logs

Les logs détaillés sont disponibles dans :
```
logs/tax_report_2025.log
```

## 📜 Licence

Ce projet est open source. Vous êtes libre de l'utiliser, le modifier et le distribuer.

## ⚖️ Avertissement

Ce programme est fourni à titre informatif. L'utilisateur reste responsable de l'exactitude de sa déclaration fiscale. En cas de doute, consultez un expert-comptable ou un conseiller fiscal.

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Signaler des bugs
- Proposer des améliorations
- Soumettre des pull requests

## 📞 Contact

Pour toute question ou suggestion, ouvrez une issue sur le dépôt du projet.

---

**Version** : 1.0  
**Dernière mise à jour** : Octobre 2025  
**Conformité** : Article 150 VH bis du CGI
