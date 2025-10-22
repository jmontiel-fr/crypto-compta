# Solution : Valeurs historiques du portefeuille

## Le problème

Pour calculer correctement la flat tax française, nous avons besoin de la **valeur du portefeuille crypto en USD** à chaque date d'opération :

- **Pour les DÉPÔTS** : Valeur du portefeuille APRÈS avoir acheté des cryptos avec les EUR déposés
- **Pour les RETRAITS** : Valeur du portefeuille AVANT d'avoir vendu des cryptos pour obtenir des EUR

## Flux des opérations

### Dépôt
```
EUR (banque) → Compte Fiat EUR Binance → Achat crypto → Portefeuille crypto
                                                         ↑
                                                    On mesure ici
```

### Retrait
```
Portefeuille crypto → Vente crypto → Compte Fiat EUR Binance → EUR (banque)
↑
On mesure ici (AVANT la vente)
```

## Pourquoi c'est difficile ?

1. **Snapshots Binance limités** : L'API `get_account_snapshot()` ne garde que les 30 derniers jours
2. **Trades crypto** : Entre les dépôts/retraits fiat, vous faites des trades qui changent la valeur du portefeuille
3. **Prix fluctuants** : La valeur des cryptos change constamment

## Solutions disponibles

### Solution 1 : Snapshots Binance (automatique, précis)

✅ **Fonctionne pour** : Les 30 derniers jours  
✅ **Précision** : Excellente (données réelles de Binance)  
❌ **Limitation** : Pas disponible pour les dates anciennes

**Résultat actuel** :
- Octobre 2025 : ✅ Snapshots disponibles (699 USD, 698 USD, etc.)
- Août 2025 : ❌ Pas de snapshots (utilise approximation incorrecte)

### Solution 2 : Valeurs manuelles (manuel, précis)

Pour les dates sans snapshot, vous pouvez fournir les valeurs manuellement.

**Comment obtenir ces valeurs ?**

1. **Via l'interface Binance** :
   - Allez dans votre historique de compte
   - Trouvez la date de l'opération
   - Notez la valeur totale du portefeuille en USD

2. **Via un export Binance** :
   - Exportez l'historique de votre compte
   - Cherchez les valeurs de portefeuille aux dates concernées

3. **Via vos propres notes** :
   - Si vous avez pris des captures d'écran
   - Si vous avez un fichier de suivi personnel

**Fichier à remplir** : `portfolio_values_manual.csv`

```csv
# Format: timestamp,portfolio_value_usd
1724943522000,22.85    # 2025-08-29 14:38:42 - Après dépôt de 19.60 EUR
1724944256000,71.23    # 2025-08-29 14:50:56 - Après dépôt de 49.00 EUR
1724947310000,80.50    # 2025-08-29 15:41:50 - Après dépôt de 9.00 EUR
1724950579000,82.30    # 2025-08-29 16:36:19 - AVANT retrait de 14.00 EUR
```

### Solution 3 : Approximation (automatique, imprécis)

❌ **Problème actuel** : Utilise les balances ACTUELLES avec les prix historiques

Cela donne des valeurs complètement fausses car :
- Vous avez peut-être acheté plus de cryptos depuis
- Les cryptos que vous aviez en août ne sont peut-être plus les mêmes

**Exemple du problème** :
```
Août : Dépôt 19.60 EUR → Achat 0.0003 BTC
Valeur réelle en août : ~22 USD

Aujourd'hui : Vous avez 0.015 BTC (après d'autres achats)
Approximation : 0.015 BTC × prix août = 1322 USD ❌ FAUX
```

## Recommandation

### Pour une déclaration fiscale correcte

1. **Utilisez les snapshots automatiques** pour octobre (déjà fait ✅)

2. **Fournissez les valeurs manuelles** pour août :
   - Éditez `portfolio_values_manual.csv`
   - Ajoutez les 4 valeurs manquantes
   - Relancez le script

3. **Si vous ne trouvez pas les valeurs exactes** :
   - Utilisez une estimation raisonnable
   - Documentez votre méthode d'estimation
   - Conservez les preuves (captures d'écran, exports)

### Valeurs à fournir pour août 2025

```
Date/Heure           Type     Montant   Valeur à fournir
2025-08-29 14:38:42  Dépôt    19.60 €   Portefeuille APRÈS achat crypto
2025-08-29 14:50:56  Dépôt    49.00 €   Portefeuille APRÈS achat crypto
2025-08-29 15:41:50  Dépôt     9.00 €   Portefeuille APRÈS achat crypto
2025-08-29 16:36:19  Retrait  14.00 €   Portefeuille AVANT vente crypto
```

## Prochaines étapes

1. Retrouvez les valeurs historiques de votre portefeuille pour août
2. Remplissez `portfolio_values_manual.csv`
3. Relancez : `python generate_tax_report.py 2025`
4. Vérifiez que les valeurs sont cohérentes

## Note importante

Pour les **dépôts**, si vous avez acheté des cryptos immédiatement après le dépôt :
- Valeur ≈ Montant déposé (converti en USD)
- Exemple : Dépôt 19.60 EUR ≈ 22-23 USD (selon taux de change)

Pour les **retraits**, la valeur doit être celle du portefeuille AVANT la vente des cryptos.
