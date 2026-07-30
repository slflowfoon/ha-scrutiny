<p align="center">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./logos/MonkeyRush.png">
  <img alt="Monkey Rush Logo" src="./logos/MonkeyRush.png" width="212">
</picture>
</p>
<p align=center>
<img src=https://img.shields.io/badge/HACS-Default-orange.svg>
<img src="https://img.shields.io/maintenance/yes/2026.svg">
<img src=https://img.shields.io/badge/version-1.1.0-blue>
<img alt="Issues" src="https://img.shields.io/github/issues/slflowfoon/ha-scrutiny?color=0088ff">
    <p align=center style="font-weight:bold">
      Imports stats from Scrutiny to Home Assistant
    </p>
</p>

## Entities

The integration creates:

- One temperature sensor for each drive returned by Scrutiny.
- `event.scrutiny_smart_attribute_degraded`, which fires when one or more
  SMART attributes on a drive move to a worse status.

The event groups simultaneous changes for one drive in the
`degraded_attributes` list. Each item includes the SMART attribute ID, display
name, old and new statuses, Scrutiny's reason, and whether Scrutiny marks the
attribute as critical. Existing statuses are used as the startup baseline and
do not generate events when Home Assistant restarts.
