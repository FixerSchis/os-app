"""Medicaments from the List of Medicaments table on the wiki Medicaments page.

Text is from https://www.orionspherelrp.co.uk/doku.php?id=medicaments, retrieved 13 Oct 2026.
effect holds rules shared by every mode. A roleplay effect listed after the last mode in a
table cell stays with that mode, as the table prints it.
"""

MEDICAMENT_DEFINITIONS = (
    {
        "name": "Med-serum",
        "summary": "Restores lost Body Hits",
        "effect": None,
        "modes": (
            ("RED", "After 10s, restores 1 lost Body Hit."),
            (
                "AMBER",
                "After 1min Rest, restores all lost Body Hits on 1 Location (or 3 GBH).",
            ),
            (
                "GREEN",
                "After 30min Rest, restores all lost Body Hits on all Locations (or all GBH).",
            ),
        ),
    },
    {
        "name": "Synthetic Platelets",
        "summary": "Prevents Death or Slows Bleeding",
        "effect": None,
        "modes": (
            ("TREAT", "Pauses your Death Count at the moment of application for 5min."),
            (
                "RESIST",
                "Your Death Count increases by +200s for 1hr. Roleplay Effect: If you have "
                "lost any Body Hits, you develop a mild headache.",
            ),
        ),
    },
    {
        "name": "Nano-Purgatives",
        "summary": "Treats Toxins & Diseases",
        "effect": "Treats one TOXIN or DISEASE when Duration Ends.",
        "modes": (
            ("GREEN", "Duration 4hr."),
            (
                "AMBER",
                "Duration 1hr. If you exert yourself, take KNOCKOUT (60). Lose 1 Body Hit on "
                "applied Location. RP-Effect: Discomfort.",
            ),
            (
                "RED",
                "Duration 15min. Cannot use skills/abilities. Lose all Body Hits. "
                "RP-Effect: Major Pain & Nausea.",
            ),
        ),
    },
    {
        "name": "Radiation Nanosponges",
        "summary": "Protects from or treats Radiation",
        "effect": None,
        "modes": (
            ("TREAT", "After 1hr of Rest, treats one RADIATION Condition."),
            (
                "RESIST",
                "Grants MAJOR RADIATION Protection for 1hr. Roleplay Effect: You feel "
                "slightly itchy.",
            ),
        ),
    },
    {
        "name": "Muscle Stims",
        "summary": "Strike with Force and Strength",
        "effect": (
            "Duration 1hr. You may make up to 1 free Call every 5min, depending on weapon: "
            "Small Melee - KNOCKOUT (5); Medium Melee - REPEL; Large Melee - REND. "
            "RP-Effect: You feel a desire to act impulsively. Extra doses taken while active "
            "add +1 free Call. If you take 2+ extra doses within duration, see a Ref at end."
        ),
        "modes": (),
    },
    {
        "name": "Nerve Stims",
        "summary": "Strike with Speed and Lethality",
        "effect": (
            "Duration 1hr. You may make up to 1 free Call every 5min, depending on weapon: "
            "Small Melee - LETHAL; Medium Melee - DISARM; Large Melee - STRIKEDOWN. "
            "RP-Effect: You feel the need to keep moving your body. Extra doses taken while "
            "active add +1 free Call. If you take 2+ extra doses within duration, see a Ref "
            "at end."
        ),
        "modes": (),
    },
    {
        "name": "Neural Regulator",
        "summary": "Mental Restorative or Suppressant",
        "effect": None,
        "modes": (
            ("TREAT", "Suppresses one Roleplay Effect you are currently under for 30min."),
            (
                "RESTORE",
                "By performing 10min of ritual/concentrated RP action immediately after use, "
                "restore all lost Psi/Will Points. If disturbed for >10s, the dose is wasted.",
            ),
        ),
    },
    {
        "name": "Cryptobiotic Trigger",
        "summary": "Enter or Leave a Protective State",
        "effect": None,
        "modes": (
            (
                "ACTIVATE",
                "After use, you may immediately enter a protective state. Gain MAJOR "
                "Protection from Hazards - TOXIC, HEAT, COLD, RADIATION, SPACE. Cannot use "
                "skills/abilities, move faster than a walk, speak louder than a whisper. "
                "RP-Effect: You feel sleepy, and cannot exert yourself. While exposed to "
                "Hazards, fall unconscious.",
            ),
            ("DEACTIVATE", "Remove the above effects after 5min."),
        ),
    },
    {
        "name": "Cellular Aegis",
        "summary": "Lessens Symptoms & Boosts Toughness",
        "effect": None,
        "modes": (
            (
                "TREAT",
                "Suppresses physical Roleplay Effects (eg. pain, exhaustion) for 1hr.",
            ),
            (
                "RESIST",
                "Gain +1 Locational Body Hit (or species equivalent GBH) for 1hr. RP-Effect: "
                "Your sense of touch is numbed, and you feel slightly disconnected from your "
                "body.",
            ),
        ),
    },
)
