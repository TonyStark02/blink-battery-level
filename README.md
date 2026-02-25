# Blink Battery Level (Custom Component) — v2.0.5

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

## 2FA (SMS) — v2.0.5
Si Blink demande un code SMS, l'intégration crée automatiquement une **notification persistante** dans Home Assistant.

Ensuite, dans Home Assistant:
- Outils de développement → **Actions**
- Action: `blink_battery_level.submit_2fa_code`
- Données: `{ "code": "123456" }`

La notification est supprimée automatiquement après validation du code.
Tu peux aussi préciser `entry_id` si plusieurs comptes Blink sont configurés.

## Limites connues
- Si Blink ne retourne pas le pourcentage pour un modèle caméra, le sensor reste `unknown`.
- Les entités `binary_sensor ... batterie` natives Blink peuvent coexister (état faible/ok).

## Troubleshooting
- Vérifier logs HA (`Settings > System > Logs`)
- En cas de 2FA, utiliser `blink_battery_level.submit_2fa_code`
- Vérifier que `blinkpy` est bien installé via requirements
