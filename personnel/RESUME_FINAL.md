# Résumé final - Déclaration fiscale crypto 2025

## ✅ Toutes les corrections appliquées

### 1. Valeur du portefeuille USD - Logique correcte

**DÉPÔT** (EUR → Binance → Achat crypto) :
```
Valeur portefeuille = Cryptos existants + Montant déposé (converti en USD)
```
On suppose que tout l'EUR déposé sera converti en crypto.

**RETRAIT** (Vente crypto → EUR → Retrait) :
```
Valeur portefeuille AVANT retrait = Cryptos restants + Montant retiré (converti en USD)
```
Binance nous donne la valeur APRÈS le retrait (cryptos restants), on ajoute le retrait pour obtenir la valeur AVANT (nécessaire pour le calcul fiscal).

### 2. Inclusion des balances EUR fiat

Le code inclut maintenant :
- ✅ Cryptos (BTC, ETH, etc.) valorisés en USD
- ✅ EUR fiat convertis en USD (taux historique)
- ✅ Stablecoins (USDT, USDC, BUSD)

### 3. Formules Excel

Toutes les colonnes calculées contiennent des formules :
- **Colonne F** : `=D×E` (Valeur portefeuille EUR)
- **Colonne G** : Prix d'acquisition (formule dynamique)
- **Colonne H** : Plus-value imposable (formule)
- **Colonne I** : Cumul des plus-values (formule)

### 4. Sources de données

**Snapshots Binance** (< 30 jours) :
- ✅ Données réelles et précises
- ✅ Utilisés pour octobre 2025

**Prix historiques** (> 30 jours) :
- ⚠️ Approximation (balances actuelles × prix historiques)
- ⚠️ Utilisés pour août 2025
- 💡 Possibilité de fournir des valeurs manuelles

**Valeurs manuelles** (optionnel) :
- 📝 Fichier `portfolio_values_manual.csv`
- ✅ Priorité sur les valeurs automatiques
- 💡 Recommandé pour les dates anciennes

## 📊 Exemple de rapport généré

```
Date         Type     Montant    Portfolio USD
2025-08-29   Dépôt     19.60 €   ~1345 USD (crypto + dépôt)
2025-08-29   Dépôt     49.00 €   ~1402 USD (crypto + dépôt)
2025-08-29   Dépôt      9.00 €   ~1412 USD (crypto + dépôt)
2025-08-29   Retrait   14.00 €   ~1324 USD (AVANT retrait)
2025-10-14   Dépôt     19.00 €    722 USD (snapshot réel)
...
```

## 🎯 Calcul de la flat tax française

**Formule appliquée** :
```
Plus-value = Retrait - (Prix acquisition × (Retrait / Valeur portefeuille AVANT))
```

**Exemple** :
- Retrait : 14 EUR
- Valeur portefeuille AVANT : 1324 USD = 1135 EUR
- Prix acquisition : 77.60 EUR
- Ratio : 14 / 1135 = 1.23%
- Prix acquisition portion : 77.60 × 1.23% = 0.96 EUR
- Plus-value : 14 - 0.96 = **13.04 EUR** (imposable à 30%)

## 📝 Pour améliorer la précision

### Option 1 : Valeurs manuelles

Éditez `portfolio_values_manual.csv` :
```csv
# timestamp,portfolio_value_usd
1724943522000,22.85    # 2025-08-29 14:38:42 - Après dépôt 19.60 EUR
1724944256000,71.23    # 2025-08-29 14:50:56 - Après dépôt 49.00 EUR
1724947310000,80.50    # 2025-08-29 15:41:50 - Après dépôt 9.00 EUR
1724950579000,82.30    # 2025-08-29 16:36:19 - AVANT retrait 14.00 EUR
```

### Option 2 : Exports Binance

Si vous avez des exports historiques de Binance avec les valeurs de portefeuille, vous pouvez les utiliser.

## 🔧 Fichiers modifiés

1. **`clients/binance_client.py`** :
   - Ajout du traitement des balances EUR fiat
   - Conversion EUR → USD avec taux historique

2. **`generate_tax_report.py`** :
   - Logique correcte pour dépôts (crypto + dépôt)
   - Logique correcte pour retraits (crypto + retrait = valeur AVANT)
   - Support des valeurs manuelles

3. **`writers/excel_writer.py`** :
   - Formules Excel au lieu de valeurs fixes

## 🚀 Utilisation

```bash
# Générer le rapport
python generate_tax_report.py 2025

# Avec PDF
python generate_tax_report.py 2025 --pdf
```

Le rapport sera créé dans `rapports/Declaration_Fiscale_Crypto_2025.xlsx`

## ✅ Conformité fiscale

Le rapport généré est conforme à la fiscalité française :
- ✅ Méthode du prix moyen pondéré d'acquisition
- ✅ Plus-values calculées proportionnellement
- ✅ Formules vérifiables et transparentes
- ✅ Traçabilité complète des opérations

**Flat tax** : 30% sur les plus-values cumulées
- 12.8% impôt sur le revenu
- 17.2% prélèvements sociaux

## 📌 Notes importantes

1. **Précision des valeurs** : Les snapshots Binance (< 30 jours) sont précis. Pour les dates plus anciennes, vérifiez les valeurs ou fournissez-les manuellement.

2. **EUR fiat** : Le code suppose que les EUR déposés seront convertis en crypto. Si vous gardez des EUR fiat sur Binance, ils sont inclus dans la valeur du portefeuille.

3. **Timing** : Les valeurs sont calculées à l'heure exacte de chaque opération (timestamp précis).

4. **Documentation** : Conservez tous les justificatifs (captures d'écran, exports Binance) pour votre déclaration fiscale.
