# Méthodologie de calcul fiscal - Déclaration des plus-values crypto

## Document officiel pour l'administration fiscale

**Année fiscale** : 2025  
**Plateforme** : Binance  
**Méthode** : Flat tax (30%) sur les plus-values de cessions d'actifs numériques  
**Base légale** : Article 150 VH bis du Code général des impôts

---

## 1. Principe général

Conformément à la législation française, les plus-values réalisées lors de cessions d'actifs numériques (cryptomonnaies) sont imposables au taux forfaitaire de 30% (12,8% d'impôt sur le revenu + 17,2% de prélèvements sociaux).

La plus-value est calculée selon la **méthode du prix moyen pondéré d'acquisition**, qui prend en compte l'ensemble du portefeuille d'actifs numériques.

---

## 2. Définition des opérations

### 2.1 Dépôt (non imposable)

Un **dépôt** correspond au transfert d'euros depuis un compte bancaire vers la plateforme Binance, en vue d'acquérir des actifs numériques.

**Traitement fiscal** :
- Augmente le prix total d'acquisition du portefeuille
- Ne génère aucune plus-value imposable
- Le montant déposé s'ajoute au coût d'acquisition global

### 2.2 Retrait (imposable)

Un **retrait** correspond à la conversion d'actifs numériques en euros, suivie du transfert de ces euros vers un compte bancaire.

**Traitement fiscal** :
- Constitue une cession d'actifs numériques
- Génère une plus-value (ou moins-value) imposable
- Réduit proportionnellement le prix d'acquisition restant

---

## 3. Méthode de calcul de la valeur du portefeuille

### 3.1 Principe

La valeur du portefeuille d'actifs numériques est exprimée en **dollars américains (USD)**, puis convertie en **euros (EUR)** au taux de change historique du jour de l'opération.

### 3.2 Composition de la valeur du portefeuille

La valeur totale du portefeuille inclut :

1. **Actifs numériques** (Bitcoin, Ethereum, etc.)
   - Quantité détenue × Prix unitaire en USD

2. **Solde en euros fiat** sur la plateforme
   - Montant en EUR × Taux de change EUR/USD

3. **Stablecoins** (USDT, USDC, BUSD)
   - Montant (équivalence 1:1 avec USD)

### 3.3 Sources de données

**Pour les opérations récentes (< 30 jours)** :
- Utilisation des **snapshots officiels Binance** via l'API `get_account_snapshot()`
- Données réelles et vérifiables auprès de Binance

**Pour les opérations anciennes (> 30 jours)** :
- Utilisation des **prix historiques** via l'API Binance `get_historical_klines()`
- Balances actuelles valorisées aux prix historiques de la date de l'opération
- Méthode d'approximation documentée et traçable

### 3.4 Calcul spécifique par type d'opération

#### Pour un DÉPÔT

```
Valeur du portefeuille = Valeur des actifs au moment du dépôt + Montant déposé
```

**Justification** :
- Le montant déposé en euros est destiné à l'acquisition d'actifs numériques
- On considère la valeur du portefeuille après l'acquisition potentielle
- Cette méthode reflète la réalité économique de l'opération

**Exemple** :
- Portefeuille avant dépôt : 1 000 USD
- Dépôt : 50 EUR (≈ 58 USD au taux du jour)
- **Valeur du portefeuille** : 1 000 + 58 = **1 058 USD**

#### Pour un RETRAIT

```
Valeur du portefeuille AVANT retrait = Valeur des actifs au moment du retrait + Montant retiré
```

**Justification** :
- Le retrait implique une conversion préalable d'actifs numériques en euros
- Cette conversion peut avoir eu lieu quelques minutes ou heures avant le retrait
- On reconstitue la valeur du portefeuille AVANT la cession en ajoutant le montant retiré
- Cette méthode est prudente et reflète la valeur maximale du portefeuille

**Exemple** :
- Portefeuille au moment du retrait : 1 310 USD
- Retrait : 14 EUR (≈ 16 USD au taux du jour)
- **Valeur du portefeuille AVANT retrait** : 1 310 + 16 = **1 326 USD**

---

## 4. Calcul de la plus-value imposable

### 4.1 Formule officielle

Pour chaque retrait, la plus-value imposable est calculée selon la formule suivante :

```
Plus-value = Montant retiré - (Prix d'acquisition total × (Montant retiré / Valeur du portefeuille))
```

**Où** :
- **Montant retiré** : Montant en EUR effectivement retiré
- **Prix d'acquisition total** : Somme de tous les dépôts effectués, diminuée des prix d'acquisition correspondant aux retraits précédents
- **Valeur du portefeuille** : Valeur totale du portefeuille AVANT le retrait, en EUR

### 4.2 Exemple détaillé

**Situation** :
- Prix d'acquisition total : 77,60 EUR (somme des dépôts précédents)
- Retrait : 14,00 EUR
- Valeur du portefeuille AVANT retrait : 1 326 USD = 1 136 EUR (taux : 0,8578)

**Calcul** :
1. Ratio de cession : 14,00 / 1 136 = 1,23%
2. Prix d'acquisition correspondant : 77,60 × 1,23% = 0,96 EUR
3. **Plus-value imposable** : 14,00 - 0,96 = **13,04 EUR**

**Mise à jour du prix d'acquisition** :
- Nouveau prix d'acquisition : 77,60 - 0,96 = 76,64 EUR

### 4.3 Cumul des plus-values

Les plus-values de tous les retraits de l'année sont cumulées pour déterminer l'assiette imposable totale.

**Impôt dû** :
```
Impôt = Cumul des plus-values × 30%
```

---

## 5. Taux de change

### 5.1 Source

Les taux de change EUR/USD sont obtenus via l'**API Frankfurter**, qui fournit les taux de change officiels de la Banque Centrale Européenne (BCE).

### 5.2 Date de référence

Le taux de change utilisé est celui du **jour de l'opération** (dépôt ou retrait).

### 5.3 Vérifiabilité

Tous les taux de change utilisés sont documentés dans le rapport Excel et peuvent être vérifiés sur le site officiel de la BCE.

---

## 6. Traçabilité et transparence

### 6.1 Rapport Excel

Le rapport généré contient :

1. **Colonnes de données brutes** :
   - Date de l'opération
   - Type d'opération (Dépôt/Retrait)
   - Montant en EUR
   - Valeur du portefeuille en USD
   - Taux de change EUR/USD

2. **Colonnes avec formules de calcul** :
   - Valeur du portefeuille en EUR (formule : USD × Taux)
   - Prix d'acquisition restant (formule dynamique)
   - Plus-value imposable (formule de calcul fiscal)
   - Cumul des plus-values (formule de somme)

### 6.2 Vérifiabilité

Toutes les formules Excel sont visibles et modifiables, permettant :
- La vérification des calculs par l'administration fiscale
- La correction manuelle si nécessaire
- La transparence totale de la méthodologie

### 6.3 Sources de données

Les données proviennent exclusivement de :
1. **API Binance officielle** (opérations et valeurs de portefeuille)
2. **API Frankfurter / BCE** (taux de change)

Toutes les données sont horodatées et traçables.

---

## 7. Conformité légale

### 7.1 Base légale

- **Article 150 VH bis du CGI** : Régime d'imposition des plus-values sur actifs numériques
- **BOI-RPPM-PVBMC-30-10** : Doctrine administrative sur les actifs numériques

### 7.2 Méthode de calcul

La méthode du **prix moyen pondéré d'acquisition** est conforme aux instructions fiscales :
- Prise en compte de l'ensemble du portefeuille
- Calcul proportionnel de la plus-value
- Traçabilité de chaque opération

### 7.3 Déclaration

Les plus-values calculées sont à déclarer :
- **Formulaire 2086** : Déclaration des plus-values sur actifs numériques
- **Formulaire 2042 C** : Déclaration complémentaire des revenus

---

## 8. Conservation des justificatifs

### 8.1 Documents à conserver

- Rapport Excel généré par ce programme
- Historique des opérations Binance (exports officiels)
- Captures d'écran des valeurs de portefeuille (si disponibles)
- Relevés bancaires des virements (dépôts et retraits)

### 8.2 Durée de conservation

**6 ans** à compter de la date de la déclaration fiscale, conformément aux obligations légales.

---

## 9. Limitations et approximations

### 9.1 Valeurs historiques

Pour les opérations de plus de 30 jours, les valeurs de portefeuille sont calculées par approximation (balances actuelles × prix historiques).

**Impact** : Peut entraîner des écarts si le portefeuille a significativement changé depuis.

**Solution** : Possibilité de fournir des valeurs manuelles via le fichier `portfolio_values_manual.csv`.

### 9.2 Timing des conversions

Pour les retraits, le moment exact de la conversion crypto → EUR n'est pas toujours connu avec précision.

**Méthode retenue** : Ajout du montant retiré à la valeur du portefeuille au moment du retrait, ce qui constitue une approximation prudente de la valeur AVANT retrait.

---

## 10. Contact et support

Pour toute question concernant cette méthodologie ou les calculs effectués :

**Programme** : Binance Tax Report Generator  
**Version** : 1.0  
**Date** : 2025  
**Licence** : Open Source

---

## Attestation

Je soussigné(e), déclare que les informations contenues dans ce rapport sont exactes et conformes aux données fournies par la plateforme Binance et aux taux de change officiels de la Banque Centrale Européenne.

Les calculs ont été effectués conformément à la législation fiscale française en vigueur et selon la méthode du prix moyen pondéré d'acquisition.

**Date** : _______________  
**Signature** : _______________

---

*Ce document constitue une annexe explicative à la déclaration fiscale et peut être fourni à l'administration fiscale sur demande.*
