# Blink Battery Level (Custom Component)

Custom component Home Assistant pour exposer le **niveau de batterie (%)** des caméras Blink.

## Ce que ça fait
- Se connecte à l’API Blink via `blinkpy`
- Crée un `sensor` par caméra avec le pourcentage batterie (quand disponible)
- Met à jour périodiquement

## Installation (HACS manual/custom)
1. Copier `custom_components/blink_battery_level` dans ton dossier Home Assistant `config/custom_components/`
2. Redémarrer Home Assistant

## Configuration (configuration.yaml)

```yaml
sensor:
  - platform: blink_battery_level
    username: "TON_EMAIL_BLINK"
    password: "TON_MOT_DE_PASSE_BLINK"
    # Optionnel
    scan_interval: 600
```

> Remarque: si ton compte Blink utilise de la 2FA stricte, la connexion peut nécessiter adaptation (PIN challenge). Ce composant est une base pratique pour exposer le pourcentage quand l’API le renvoie.

## Entités créées
- `sensor.blink_<nom_camera>_battery_level`

## Troubleshooting
- Vérifier les logs HA: `Settings > System > Logs`
- Vérifier que `blinkpy` est installable dans l’environnement HA
- Si `battery` est absent côté API Blink, le sensor passe en `unknown`
