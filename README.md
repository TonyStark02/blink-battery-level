# Blink Battery Level (Custom Component) — v2.0.6

Custom component Home Assistant pour exposer le **niveau de batterie (%)** des caméras Blink.

## Nouveautés v2
- ✅ **Config Flow UI** (plus besoin obligatoire de YAML)
- ✅ Compatibilité backward avec setup YAML
- ✅ Intervalle de scan configurable (60s à 3600s)

## Installation
1. Copier `custom_components/blink_battery_level` dans `config/custom_components/`
2. Redémarrer Home Assistant

## Configuration (recommandée: UI)
- Home Assistant → Settings → Devices & Services → Add Integration
- Chercher **Blink Battery Level**
- Renseigner email Blink, mot de passe, scan interval

## Configuration YAML (legacy, optionnel)

```yaml
sensor:
  - platform: blink_battery_level
    username: "TON_EMAIL_BLINK"
    password: "TON_MOT_DE_PASSE_BLINK"
    scan_interval: 600
```

## Entités créées
- `sensor.blink_<nom_camera>_battery`

## 2FA (SMS) — v2.0.6 (flow direct)
Le flow d’installation gère maintenant la 2FA **dans la même séquence UI**:
1. Saisie email + mot de passe
2. Si Blink demande un SMS, écran suivant direct pour saisir le code
3. Validation puis création de l’intégration

Le service `blink_battery_level.submit_2fa_code` reste disponible en secours si besoin.

## Limites connues
- Si Blink ne retourne pas le pourcentage pour un modèle caméra, le sensor reste `unknown`.
- Les entités `binary_sensor ... batterie` natives Blink peuvent coexister (état faible/ok).

## Troubleshooting
- Vérifier logs HA (`Settings > System > Logs`)
- En cas de 2FA, utiliser `blink_battery_level.submit_2fa_code`
- Vérifier que `blinkpy` est bien installé via requirements
