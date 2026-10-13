"""Base items from the wiki Downtime Equipment List.

Rows are from https://www.orionspherelrp.co.uk/doku.php?id=downtime_equipment_list,
retrieved 13 Oct 2026. When a mod from default_mods.py gives the listed ability, the
blueprint carries that mod and no ability text, so editing the mod updates the item.
Ability text is kept only where no mod matches. Charges are not stored on a blueprint.

AA Power Field is AA Light Field's ability plus Field Strengthener, for 2 Field Hits.
AA Stalwart Lorica can RESIST either THROUGH or REND for 1 Charge, which no single mod gives.
"""

_FIELD_ABILITY = "1 Global Field Hit. 1 charge to re-power when not in combat"


def _blueprint(name, item_type, base_cost, ability=None, mods=()):
    return {
        "name": name,
        "item_type": item_type,
        "base_cost": base_cost,
        "ability": ability,
        "mods": mods,
    }


BLUEPRINT_DEFINITIONS = [
    # Melee weapons.
    _blueprint("AA Power Blade", "Small Melee Weapon", 10),
    _blueprint("AA Penetrator Blade", "Small Melee Weapon", 20, mods=("Penetrator Matrix",)),
    _blueprint("AA Power Sword", "Medium Melee Weapon", 20),
    _blueprint("AA Fortress Sword", "Medium Melee Weapon", 30, mods=("Integrity Field",)),
    _blueprint("AA Power Glaive", "Large Melee Weapon", 20),
    _blueprint("AA Force Glaive", "Large Melee Weapon", 30, mods=("Force Matrix",)),
    _blueprint("AA Ruin Glaive", "Large Melee Weapon", 30, mods=("Ruination Matrix",)),
    # Energy weapons.
    _blueprint("AA Blaster Pistol", "Light Energy Weapon", 20),
    _blueprint("AA Shock Pistol", "Light Energy Weapon", 30, mods=("Shock Bolt",)),
    _blueprint("AA Penetrator Pistol", "Light Energy Weapon", 30, mods=("Penetrator Bolt",)),
    _blueprint("AA Disruptor Pistol", "Light Energy Weapon", 30, mods=("Disruption Bolt",)),
    _blueprint("AA Blaster Rifle", "Medium Energy Weapon", 30),
    _blueprint("AA Fortress Blaster", "Medium Energy Weapon", 40, mods=("Integrity Field",)),
    _blueprint("AA Penetrator Rifle", "Medium Energy Weapon", 40, mods=("Penetrator Bolt",)),
    _blueprint("AA Impact Rifle", "Medium Energy Weapon", 40, mods=("Impact Bolt",)),
    _blueprint("AA Blaster Cannon", "Heavy Energy Weapon", 30),
    _blueprint("AA Stun Cannon", "Heavy Energy Weapon", 40, mods=("Heavy Stun Bolt",)),
    _blueprint("AA Shredder Cannon", "Heavy Energy Weapon", 40, mods=("Heavy Shredder Bolt",)),
    _blueprint("AA Ruiner Cannon", "Heavy Energy Weapon", 40, mods=("Heavy Ruin Bolt",)),
    # Projectiles, sold in packs of 5. The cost is per pack.
    _blueprint("AA Impact Projectiles", "Projectile", 15, "STRIKEDOWN projectiles"),
    _blueprint("AA Stun Projectiles", "Projectile", 15, "FREEZE(5) projectiles"),
    _blueprint("AA Disruptor Projectiles", "Projectile", 20, "DISRUPT projectiles"),
    _blueprint("AA Neural Projectiles", "Projectile", 25, "KNOCKOUT(10) projectiles"),
    _blueprint("AA Shredder Projectiles", "Projectile", 30, "REND projectiles"),
    # Shields.
    _blueprint("AA Power Shield", "Shield", 20),
    _blueprint("AA Gyro-Shield", "Shield", 30, mods=("Compensator Matrix",)),
    _blueprint("AA Fortress Shield", "Shield", 30, mods=("Integrity Field",)),
    _blueprint("AA E-AB Shield", "Shield", 30, mods=("Energy Absorption Matrix",)),
    # Armour.
    _blueprint("AA PowerSkin", "Light Armour", 20),
    _blueprint("AA ReSkin", "Light Armour", 30, mods=("Reinforcement Pattern",)),
    _blueprint("AA StandSkin", "Light Armour", 30, mods=("Stabilisers",)),
    _blueprint(
        "GES Thermo-Skin",
        "Light Armour",
        80,
        "2 Charges for protection from Minor THERMAL Environments for 30 mins.",
    ),
    _blueprint("AA PowerJack", "Medium Armour", 20),
    _blueprint("AA FortJack", "Medium Armour", 30, mods=("Integrity Pattern",)),
    _blueprint("AA ShockJack", "Medium Armour", 30, mods=("Shock Distributors",)),
    _blueprint("AA ToughJack", "Medium Armour", 30, mods=("Ablative Layers",)),
    _blueprint("AA PowerSuit", "Heavy Armour", 20),
    _blueprint("AA StandSuit", "Heavy Armour", 30, mods=("Stabilisers",)),
    _blueprint("AA ShockSuit", "Heavy Armour", 30, mods=("Shock Distributors",)),
    _blueprint("AA WeaveSuit", "Heavy Armour", 30, mods=("Weave Solidifier",)),
    _blueprint(
        "GES Enviro-Suit",
        "Heavy Armour",
        30,
        "2 Charges for protection from Minor THERMAL and RADIATION Environments for 30 mins",
    ),
    _blueprint("AA Stalwart Lorica", "Assault Armour", 70, "1 Charge to RESIST a THROUGH or REND"),
    # Energy fields.
    _blueprint("AA Light Field", "Energy Field", 40, _FIELD_ABILITY),
    _blueprint("AA Power Field", "Energy Field", 80, _FIELD_ABILITY, ("Field Strengthener",)),
    # Science devices.
    _blueprint(
        "GES Scanner",
        "Scanner",
        25,
        "(Scientist) 1 Charge to Survey, Examine or Sample",
    ),
    # General equipment.
    _blueprint("GES XD-5 Charge Pack", "Charge Pack", 15, "Holds Charges"),
    _blueprint("GES XD-10 Charge Pack", "Charge Pack", 30, "Holds Charges"),
    _blueprint(
        "AA Re-Arm Nanite Patch",
        "Engineering Device",
        10,
        (
            "Single-use patch that fully repairs the armour on a single location after it is "
            "applied. Requires Engineer"
        ),
    ),
    _blueprint(
        "AA Harmonic Plasticiser",
        "Engineering Tools",
        50,
        "Tear 1 charge to halve manual repair time for a single suit of armour.",
    ),
    _blueprint(
        "AA Life Preserver",
        "Medical Device",
        30,
        "Tear 1 charge to reset the target's Death Count to 0. Requires First Aid.",
    ),
    _blueprint(
        "AA Decontamination Nanites",
        "Medical Device",
        50,
        "Tear 2 charges to purge basic illnesses from target. Requires Physician",
    ),
    _blueprint(
        "Lensman Corp Oxy-Mask",
        "Breathing Mask",
        80,
        (
            "2 charges to provide 30 minutes of breathable atmosphere, provides protection "
            "from Minor TOXIC Environments while active."
        ),
    ),
]
