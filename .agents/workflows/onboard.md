---
description: "Sovereign Onboarding Agent — reads workspace state and produces a situation-aware startup brief for any new agent or human entering the workspace for the first time"
tags: [meta, onboarding, orientation]
---

# PAYLOAD LOCATION
view_file /home/jwils/blueprint-workflows/claude-commands/onboard.md

# IF PAYLOAD MISSING
If the file above cannot be read, HALT and report:
"PAYLOAD MISSING: onboard.md not found at the canonical path. The Sovereign Suite may not be installed. Ask the user for the correct path to blueprint-workflows/claude-commands/."
