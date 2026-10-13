"""Exotic substances from the Known lists on the wiki Exotic Particles, Reagents, and Biotics pages.

Text is from https://www.orionspherelrp.co.uk/doku.php?id=exotic_particles,
https://www.orionspherelrp.co.uk/doku.php?id=exotic_reagents, and
https://www.orionspherelrp.co.uk/doku.php?id=exotic_biotics, retrieved 13 Oct 2026.
Each row is (name, used on, effect, duration). Fermite's duration reads "Medicament" on the wiki;
it is stored as "As Medicament" to match the other medicament reagents.
"""

EXOTIC_PARTICLES = (
    (
        "Dampened Vibrons",
        "Energy Fields",
        "Protects from Minor Heat Environments",
        "1 hour/all Hits lost",
    ),
    (
        "Excited Vibrons",
        "Energy Fields",
        "Protects from Minor Cold Environments",
        "1 hour/all Hits lost",
    ),
    (
        "Kappa Particles",
        "Energy Fields",
        "Adds ability to gain 5 minutes RADIATION protection",
        "2 hours",
    ),
    (
        "Locke Ion Plasma",
        "Energy Fields",
        "Protects from Minor Toxic Environments",
        "1 hour/all Hits lost",
    ),
    ("Magneto-gravitons", "Scanners", "Empowers sampling attempts", "1 day"),
    ("Multiphasic Bosons", "Weapons", "Adds ability to strike for THROUGH with charges", "2 hours"),
    (
        "Quark Plasma",
        "Devices",
        "Allows an item to use its powers without spending charges, but it becomes Broken when "
        "the duration expires",
        "5 minutes",
    ),
    ("Rastan Particles", "Devices", "-1 charges to use item's abilities (minimum 1)", "2 hours"),
    ("Resonant Neutrons", "Scanners", "Empowers detection devices and survey attempts", "1 day"),
    ("Shredder Particles", "Weapons", "Adds ability to strike for REND with charges", "2 hours"),
    ("Soarix Particles", "Scanners", "Empowers examine attempts", "1 day"),
    ("Yurian Lattice Plasma", "Devices", "Doubles charge capacity of item", "1 day"),
)

EXOTIC_REAGENTS = (
    ("Active Gallium", "Characters", "Grants Minor Toxic Environment protection", "30 minutes"),
    ("Arcigolite", "Medicaments", "Doubles all medicaments durations", "As Medicament"),
    ("Dirac Crystals", "Energy Fields", "Adds 1 hit to Energy Fields", "2 hours"),
    ("Fermite", "Medicaments", "Halves all medicaments durations", "As Medicament"),
    ("Fusible Polymer", "Armour", "Adds 1 hit to Armour", "1 day"),
    (
        "Insulation Film",
        "Armour",
        "Protects from Minor Cold and Minor Heat Environments",
        "2 hours",
    ),
    ("Lead Amalgam", "Armour", "Provides Minor RADIATION protection", "1 hour"),
    ("Notum", "Devices", "Adds ability to resist SUNDER with charges", "1 day"),
    (
        "Omnicatalyst",
        "Medicaments",
        "Increases effectiveness (doubles non-duration numbers)",
        "As Medicament",
    ),
    (
        "Spectrum Inhibitor",
        "Medicaments",
        "Decreases effectiveness (halves non-duration numbers)",
        "As Medicament",
    ),
)

EXOTIC_BIOTICS = (
    ("Dreamfruit", "Characters", "Increases Psi Points or Will Points maximum by 1", "1 day"),
    (
        "Fornaxian Spore Cap",
        "Characters",
        "Grants the ability to strike for 1 powerful attack in melee",
        "1 day or until used",
    ),
    (
        "Glowfish Toxin",
        "Characters",
        "You can act while on 0 hits. While on 0 hits, you are dying",
        "2 hours",
    ),
    ("Incheon Serpent Venom", "Characters", "Empowers roleplay effects that affect you", "1 day"),
    (
        "Lingas Pepper",
        "Characters",
        "Protects from Major Cold Environments, makes character Vulnerable to Heat",
        "1 day",
    ),
    (
        "Lucidius pollen",
        "Characters",
        "Grants ability to strike for 1 focused attack in melee",
        "1 day or until used",
    ),
    ("Neo-Mandragora Root", "Characters", "Dulls roleplay effects that affect you", "1 day"),
    ("Pelgrin Bark Extract", "Characters", "Restores 1 spent Psi Point or Will Point", "None"),
    (
        "Roddenberry Extract",
        "Characters",
        "Grants 1 rank of Steel Nerves & prevents neural shock from cybernetics",
        "1 day",
    ),
    (
        "Saggitarian Lizard Scales",
        "Characters",
        "Grants ability to ignore 1 roleplay effect",
        "1 day or until used",
    ),
    (
        "Sand-Mold Extract",
        "Characters",
        "Protects from Major Heat Environments, makes character Vulnerable to Cold",
        "1 day",
    ),
    ("Stardust Mold", "Characters", "Grants 1 rank of Steel Head", "2 hours"),
)
