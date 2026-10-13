"""Mods from the wiki Mods page, grouped by the item types each section applies to.

Effect text is from https://www.orionspherelrp.co.uk/doku.php?id=mods, retrieved 13 Oct 2026.
Weave Crystal is rank 5 of the Psionic Resonance path. Talisman needs Priestly Devotion,
and an engineer with Priestly Devotion knows it without using a mod slot, as stated on the
Devotion Skills page.
"""

_ENERGY_WEAPONS = ("Light Energy Weapon", "Medium Energy Weapon")
_HEAVY_ENERGY_WEAPONS = ("Heavy Energy Weapon",)
_MELEE_WEAPONS = ("Small Melee Weapon", "Medium Melee Weapon", "Large Melee Weapon")
_SHIELDS = ("Shield",)
_ARMOUR = ("Light Armour", "Medium Armour", "Heavy Armour", "Assault Armour")
_ENERGY_FIELDS = ("Energy Field",)
_SCANNERS = ("Scanner",)

_WEAVE_CRYSTAL = ("Psionic Resonance [5]",)
_WEAVE_CRYSTAL_NOTE = " You must have the Weave Crystal psionic power to learn this Mod."

_FOCUS_NOTE = (
    " A Scanner can only have one type of Focus Mod applied to it - after the first, "
    "different types of Focus Mod cannot be applied. If multiple Focus Mods of the same type "
    "are applied to a Scanner, they grant additional automatic successes, but only on "
    "odd-numbers of the same mod applied. So a Scanner with 1 or 2 of this Focus Mod gets 1 "
    "automatic success, one with 3 or 4 gets 2 auto-successes, one with 5 or 6 gets 3 "
    "auto-successes, and so on. Automatic Successes can only be used by the lead character "
    "while scanning, and only an amount of times equal to their Skill Rank."
)


def _mod(name, description, item_types=(), requires=(), granted_by=()):
    return {
        "name": name,
        "description": description,
        "item_types": item_types,
        "requires": requires,
        "granted_by": granted_by,
    }


MOD_DEFINITIONS = [
    # Generic mods.
    _mod("Charge Cells", "+2 Charge Capacity. Can be applied multiple times."),
    _mod(
        "Integrity Field",
        "Tear 1 Charge to Resist a SUNDER call that hits this weapon, shield or device.",
    ),
    _mod(
        "Hardened Components",
        "This item cannot become Broken (it can still become SUNDERED).",
    ),
    # Dominion cultural mods.
    _mod(
        "Talisman",
        (
            "Dominion characters with a Talisman item may call RESIST to one IMBUE call or "
            "roleplay effect each day. Engineers with at least one rank of Priestly Devotion "
            "automatically gain knowledge of this Mod in addition to their normal allocation."
        ),
        requires=("Priestly Devotion",),
        granted_by=("Priestly Devotion",),
    ),
    # Commonality cultural mods.
    _mod(
        "Psi Crystal Battery",
        "+3 Charge Capacity. Can be applied multiple times." + _WEAVE_CRYSTAL_NOTE,
        requires=_WEAVE_CRYSTAL,
    ),
    _mod(
        "Psi Crystal Capacitor",
        "You may spend psi points in place of Charges when using this item." + _WEAVE_CRYSTAL_NOTE,
        requires=_WEAVE_CRYSTAL,
    ),
    _mod(
        "Psi Crystal Matrix",
        (
            "This mod infuses psi crystals through a devices mechanisms, allowing it to be "
            "manipulated with certain specific psionic abilities." + _WEAVE_CRYSTAL_NOTE + " A "
            "melee weapon with a Psi Crystal Matrix can be used with the Resonant Blade psionic "
            "powers."
        ),
        requires=_WEAVE_CRYSTAL,
    ),
    # Energy weapons, apart from heavy.
    _mod(
        "Shock Bolt",
        (
            "Tear 1 charge to make a FREEZE(5) call. Can be applied multiple times, each time "
            "allowing an extra charge to be torn to increase the FREEZE duration by 5."
        ),
        _ENERGY_WEAPONS,
    ),
    _mod("Penetrator Bolt", "Tear 1 charge to make a THROUGH call.", _ENERGY_WEAPONS),
    _mod("Disruption Bolt", "Tear 2 charges to make a DISRUPT call.", _ENERGY_WEAPONS),
    _mod("Force Bolt", "Tear 1 charge to make a STRIKE call.", _ENERGY_WEAPONS),
    _mod("Kill Bolt", "Tear 4 charges to make a LETHAL call.", _ENERGY_WEAPONS),
    _mod("Impact Bolt", "Tear 1 charge to make a STRIKEDOWN call.", _ENERGY_WEAPONS),
    # Heavy energy weapons.
    _mod(
        "Heavy Disruption Bolt",
        "Tear 1 charge to make a DISRUPT call.",
        _HEAVY_ENERGY_WEAPONS,
    ),
    _mod(
        "Heavy Shock Bolt",
        (
            "Tear 1 charge to make a FREEZE(10) call. Can be applied multiple times, each time "
            "allowing an extra charge to be torn to increase the FREEZE duration by 10."
        ),
        _HEAVY_ENERGY_WEAPONS,
    ),
    _mod(
        "Heavy Stun Bolt",
        (
            "Tear 1 charges to make a KNOCKOUT(10) call. Can be applied multiple times, each "
            "time allowing an extra 1 charge to be torn to increase the KNOCKOUT duration by 10."
        ),
        _HEAVY_ENERGY_WEAPONS,
    ),
    _mod("Heavy Shredder Bolt", "Tear 2 charges to make a REND call.", _HEAVY_ENERGY_WEAPONS),
    _mod("Heavy Ruin Bolt", "Tear 2 charges to make a SUNDER call.", _HEAVY_ENERGY_WEAPONS),
    _mod(
        "Heavy Suppressing Fire",
        (
            "Add the MASS modifier to a call for 3x the normal Charge Cost (the basic STRIKE "
            "call of heavy energy weapons counts as having 1 Charge Cost for the purposes of "
            "this mod). You must direct this MASS call in a 90-180 degree arc to the front of "
            "your weapon."
        ),
        _HEAVY_ENERGY_WEAPONS,
    ),
    _mod(
        "Heavy Overcharge Bolt",
        (
            "Add the GLOBAL modifier to a call for 3x the normal Charge Cost (the basic STRIKE "
            "call of heavy energy weapons counts as having 1 Charge Cost for the purposes of "
            "this mod). This Mod only has an effect on calls that have a locational effect "
            "(DISARM, DISRUPT, REND, STRIKE, THROUGH)."
        ),
        _HEAVY_ENERGY_WEAPONS,
    ),
    # Melee weapons, any size.
    _mod("Penetrator Matrix", "Tear 1 charge to make a THROUGH call.", _MELEE_WEAPONS),
    _mod(
        "Shock Matrix",
        (
            "Tear 1 charge to make a FREEZE(5) call. Can be applied multiple times, each time "
            "allowing an extra charge to be torn to increase the FREEZE duration by 5."
        ),
        _MELEE_WEAPONS,
    ),
    # Melee weapons, one size.
    _mod("Disruption Matrix", "Tear 1 charge to make a DISRUPT call.", ("Small Melee Weapon",)),
    _mod("Convulsor Matrix", "Tear 1 charge to call DISARM.", ("Medium Melee Weapon",)),
    _mod("Force Matrix", "Tear 1 charge to call STRIKE.", ("Large Melee Weapon",)),
    _mod("Impact Matrix", "Tear 1 charge to call STRIKEDOWN.", ("Large Melee Weapon",)),
    _mod(
        "Stun Matrix",
        (
            "Tear 2 charges to make a KNOCKOUT(10) call. Can be applied multiple times, each "
            "time allowing an extra 1 charge to be torn to increase the KNOCKOUT duration by 10."
        ),
        ("Large Melee Weapon",),
    ),
    _mod("Shredder Matrix", "Tear 2 charges to call REND.", ("Large Melee Weapon",)),
    _mod("Ruination Matrix", "Tear 2 charges to call SUNDER.", ("Large Melee Weapon",)),
    # Shields.
    _mod(
        "Reflection Matrix",
        "Tear 2 charges to call SUNDER to a melee weapon that strikes this shield.",
        _SHIELDS,
    ),
    _mod(
        "Compensator Matrix",
        "You may move at full speed while under fire using this shield.",
        _SHIELDS,
    ),
    _mod(
        "Force Absorption Matrix",
        "You may call RESIST to STRIKEDOWN and REPEL attacks that strike this shield.",
        _SHIELDS,
    ),
    _mod(
        "Energy Absorption Matrix",
        (
            "Reduce the duration of FREEZE and KNOCKOUT attacks that strike this shield by 10 "
            "seconds for each time this mod is applied."
        ),
        _SHIELDS,
    ),
    _mod(
        "Resistance Matrix",
        "Tear 1 charge to call RESIST to a Call that strikes this shield.",
        _SHIELDS,
    ),
    _mod(
        "Repulsor Matrix",
        "Tear 2 charges to call REPEL to a character that strikes this shield with a melee weapon.",
        _SHIELDS,
    ),
    # Armour.
    _mod(
        "Shock Distributors",
        "Reduce FREEZE duration by 2 seconds. Can be applied multiple times.",
        _ARMOUR,
    ),
    _mod(
        "Reinforcement Pattern",
        (
            "Tear 1 Charge to restore 1 lost hit on a location. Can be applied multiple times to "
            "restore more hits per Charge expended (so armour with 2 of these mods can tear 1 "
            "Charge to restore 2 hits on a location). Regardless of how many of these Mods are "
            "on armour, the Reinforcement Pattern ability can only be triggered once every 30 "
            "seconds."
        ),
        _ARMOUR,
    ),
    _mod(
        "Ablative Layers",
        (
            "Adds 1 Armour Hit to the armour. Can be applied once for Light, twice for Medium, "
            "3 times for Heavy, and 4 times for Assault Armour."
        ),
        _ARMOUR,
    ),
    _mod("Integrity Pattern", "Tear 1 charge to call RESIST(REND).", _ARMOUR),
    _mod("Stabilisers", "Tear 1 charge to call RESIST(STRIKEDOWN).", _ARMOUR),
    _mod(
        "Weave Solidifier",
        (
            "Tear 2 charges to activate for 30 seconds. While active, you may call "
            "RESIST(THROUGH) at no cost. Can be applied multiple times - each application after "
            "the first increases the activation duration by 15 seconds."
        ),
        _ARMOUR,
    ),
    _mod(
        "Deflection Generator",
        (
            "Tear 4 charges to activate for 30 seconds. While active, you may call RESIST to all "
            "attacks at no cost, but cannot make attacks or use any abilities that affect any "
            "other characters or external objects (you may still use abilities that affect you "
            "and your carried or worn equipment, or allow you to RESIST other effects). After "
            "use, this Mod cannot be used again for another 30 seconds."
        ),
        _ARMOUR,
    ),
    # Energy fields.
    _mod("Field Strengthener", "Energy Field gains 1 Field Hit.", _ENERGY_FIELDS),
    _mod(
        "Combat Repower",
        (
            "Tear 1 charge to initiate a 30-second recharge cycle. After 30 seconds all field "
            "hits are restored. If you are struck during this period then the recharge fails and "
            "the charges spent are wasted. This mod may be applied multiple times, allowing you "
            "to tear 1 extra charge to reduce the recharge cycle by 10 seconds."
        ),
        _ENERGY_FIELDS,
    ),
    # Scanners.
    _mod(
        "Detection Module",
        "Increases the detection range for Surveys to a wider area.",
        _SCANNERS,
    ),
    _mod(
        "Analysis Module",
        "Adds a Green Card to Examinations performed using the Scanner.",
        _SCANNERS,
    ),
    _mod(
        "Sampling Module",
        "Adds a Green Card to Sampling performed using the Scanner.",
        _SCANNERS,
    ),
    _mod(
        "Flexible Energy Containment",
        "Grants an additional slot for Exotic Substances. Can only be applied once.",
        _SCANNERS,
    ),
    _mod(
        "Etheric Focus",
        (
            "Grants 1 automatic success to Examine and Sample attempts performed on Etheric "
            "Science Phenomena using the Scanner. A Scanner with this mod cannot perform Examine "
            "and Sample attempts on Life or Corporeal Science phenomena." + _FOCUS_NOTE
        ),
        _SCANNERS,
    ),
    _mod(
        "Corporeal Focus",
        (
            "Grants 1 automatic success to Examine and Sample attempts performed on Corporeal "
            "Science Phenomena using the Scanner. A Scanner with this mod cannot perform Examine "
            "and Sample attempts on Etheric or Life Science phenomena." + _FOCUS_NOTE
        ),
        _SCANNERS,
    ),
    _mod(
        "Life Focus",
        (
            "Grants 1 automatic success to Examine and Sample attempts performed on Life Science "
            "Phenomena using the Scanner. A Scanner with this mod cannot perform Examine and "
            "Sample attempts on Etheric or Corporeal Science phenomena." + _FOCUS_NOTE
        ),
        _SCANNERS,
    ),
    _mod(
        "Diagnostic Focus",
        (
            "Grants 1 automatic success to Examine and Sample attempts performed on "
            "character-affecting Conditions using the Scanner. A Scanner with this mod cannot "
            "perform Examine and Sample attempts on other phenomena." + _FOCUS_NOTE
        ),
        _SCANNERS,
    ),
]
