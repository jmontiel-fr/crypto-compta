# Logique finale confirmée - Calcul des valeurs de portefeuille

## ✅ Logique implémentée

### Pour les DÉPÔTS

```
Valeur portefeuille = Valeur actuelle (cryptos + EUR fiat) + Montant déposé (en USD)
```

**Explication** :
- On récupère la valeur du portefeuille au moment du dépôt
- On ajoute le montant déposé (converti en USD)
- On suppose que l'EUR déposé sera converti en crypto

**Code** :
```python
deposit_usd = operation.amount_eur / exchange_rate
portfolio_value_usd = portfolio_value_usd_raw + deposit_usd
```

### Pour les RETRAITS

```
Valeur portefeuille AVANT = Valeur actuelle (cryptos + EUR fiat) + Montant retiré (en USD)
```

**Explication** :
- On récupère la valeur du portefeuille au moment du retrait
- Cette valeur inclut les cryptos restants + EUR fiat restant
- On ajoute le montant EUR retiré (converti en USD)
- On obtient une estimation de la valeur AVANT le retrait
- **Avantage** : On ne fait pas d'hypothèse sur le moment exact de la conversion crypto → EUR

**Code** :
```python
withdrawal_usd = operation.amount_eur / exchange_rate
portfolio_value_usd = portfolio_value_usd_raw + withdrawal_usd
```

## 🎯 Pourquoi cette approche est correcte

### Problème résolu
On ne sait pas exactement quand la conversion crypto → EUR fiat a été faite :
- Peut-être quelques minutes avant le retrait
- Peut-être quelques heures avant
- Peut-être juste avant

### Solution
En prenant la valeur du portefeuille **au moment du retrait** et en ajoutant le montant retiré, on obtient une bonne approximation de la valeur AVANT le retrait, quelle que soit la date exacte de la conversion.

### Exemple concret

**Scénario** :
1. Vous avez 0.02 BTC + 0.5 ETH = 1310 USD
2. Vous vendez pour obtenir 14 EUR fiat sur Binance
3. Quelques heures plus tard, vous retirez ces 14 EUR
4. Au moment du retrait : portefeuille = 0.015 BTC + 0.4 ETH = 1310 USD (environ)

**Calcul** :
- Valeur au moment du retrait : 1310 USD
- Montant retiré : 14 EUR ≈ 16.32 USD
- Valeur AVANT retrait : 1310 + 16.32 = **1326.32 USD**

Cette valeur est utilisée pour calculer la plus-value fiscale.

## 📊 Composants de la valeur du portefeuille

La valeur récupérée par `get_portfolio_value_usd()` inclut :

1. **Cryptos** (BTC, ETH, etc.) :
   - Quantité × Prix en USD (historique ou actuel)

2. **EUR fiat** sur Binance :
   - Montant EUR × Taux EUR/USD (historique)

3. **Stablecoins** (USDT, USDC, BUSD) :
   - Montant (1:1 avec USD)

## ✅ Conformité fiscale française

Cette méthode est conforme au calcul de la flat tax française :

**Formule** :
```
Plus-value = Retrait - (Prix acquisition × (Retrait / Valeur portefeuille AVANT))
```

**Exemple** :
- Retrait : 14 EUR
- Valeur portefeuille AVANT : 1326 USD = 1136 EUR
- Prix acquisition : 77.60 EUR
- Ratio : 14 / 1136 = 1.23%
- Prix acquisition portion : 77.60 × 1.23% = 0.96 EUR
- **Plus-value** : 14 - 0.96 = **13.04 EUR** (imposable à 30%)

## 🔍 Précision des valeurs

### Snapshots Binance (< 30 jours)
- ✅ **Très précis** : Données réelles de Binance
- ✅ Inclut cryptos + EUR fiat + stablecoins
- ✅ Prix historiques exacts

### Prix historiques (> 30 jours)
- ⚠️ **Approximation** : Balances actuelles × Prix historiques
- ⚠️ Peut être imprécis si vous avez beaucoup tradé depuis
- 💡 **Solution** : Fournir des valeurs manuelles via `portfolio_values_manual.csv`

## 📝 Recommandations

1. **Pour les opérations récentes** : Les snapshots Binance sont suffisamment précis

2. **Pour les opérations anciennes** : 
   - Vérifiez les valeurs générées
   - Si nécessaire, fournissez des valeurs manuelles
   - Conservez les justificatifs (captures d'écran, exports)

3. **Pour la déclaration fiscale** :
   - Vérifiez le cumul des plus-values
   - Conservez le rapport Excel généré
   - Documentez votre méthode de calcul

## 🎯 Conclusion

La logique implémentée est **correcte et pragmatique** :
- ✅ Ne fait pas d'hypothèse sur le timing exact des conversions
- ✅ Utilise les données réelles de Binance quand disponibles
- ✅ Conforme à la fiscalité française
- ✅ Transparente et vérifiable (formules Excel)
