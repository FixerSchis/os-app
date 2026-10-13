"""Wiki skill catalogue used by the default-data seed.

Sources, retrieved 13 Oct 2026:
- combat_skills
- professional_skills
- reputation_skills
- discipline_skills and species_skills
- psionics_skills and the species psionic path pages
- n-dax_mutation_skills
- devotion_skills
- nanodeck (each Corpori program is its own skill)

Costs marked "+" on the wiki increase by 1 each rank. Costs marked "a" or
"per rank" without that note do not. A free species rank is not represented
here; those grants belong on the species, and must not count as a paid rank.
Console skills have a maximum of 2 ranks, so each one is a Basic skill and an
Advanced skill. The Advanced skill is what the later spaceflight skills require.
A skill's own maximum is max_ranks. A species rank-cap ability can set a lower one.
Each psionic path rank is its own skill, because the benefit changes every rank.
Each N-DAX mutation rank is its own skill for the same reason.
"""

import importlib.util
import os

_CAPTAIN_EXPERT_SKILLS = (
    "Evasive Maneuvers",
    "Emergency Evacuation",
    "Concentrate Fire",
    "Concussive Blast",
    "Emergency Repairs",
    "Technical Support",
    "Sensor Ping",
    "Wide Area Scan",
    "Taunt",
    "Coordinate Hacking",
)
_CAPTAIN_CONSOLE_SKILLS = (
    "Helm Console [Advanced]",
    "Weapons Console [Advanced]",
    "Engineering Console [Advanced]",
    "Science Console [Advanced]",
    "Relay Console [Advanced]",
)


_PSIONIC_SPECIES = [
    "Elysian",
    "Felani",
    "Kelki",
    "Kordai",
    "Lithos",
    "Vikaas Aquerna",
]


def _captain(name, effect):
    return _skill(
        name,
        effect,
        "spaceflight",
        2,
        any_of=_CAPTAIN_EXPERT_SKILLS,
        distinct_of=_CAPTAIN_CONSOLE_SKILLS,
    )


def _skill(name, description, skill_type, base_cost, **flags):
    row = {
        "name": name,
        "description": description,
        "skill_type": skill_type,
        "base_cost": base_cost,
    }
    row.update(flags)
    return row


def _console(name, basic, advanced):
    """Split a 2-rank console skill so the second rank can be a normal prerequisite."""
    return (
        _skill(f"{name} [Basic]", basic, "spaceflight", 1),
        _skill(
            f"{name} [Advanced]",
            advanced,
            "spaceflight",
            2,
            requires=f"{name} [Basic]",
        ),
    )


def _load_path_catalogue():
    path = os.path.join(os.path.dirname(__file__), "psionic_paths.py")
    spec = importlib.util.spec_from_file_location("psionic_paths", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.PATHS


def _effect_text(effect):
    if isinstance(effect, tuple):
        return "".join(effect)
    return effect


def _expand_paths(catalogue):
    """Turn each path into six once-only skills. Rank 6 adds a Psi Point."""
    skills = []
    for path in catalogue:
        ranks = path["ranks"]
        if len(ranks) != 5:
            raise ValueError(f"{path['name']} must list five rank effects")
        prerequisite = None
        if path.get("requires"):
            parent, parent_rank = path["requires"]
            prerequisite = f"{parent} [{parent_rank}]"
        for index, effect in enumerate(ranks, start=1):
            name = f"{path['name']} [{index}]"
            flags = {"species": path["species"]}
            if prerequisite:
                flags["requires"] = prerequisite
            skills.append(_skill(name, _effect_text(effect), "psionic", 1, **flags))
            prerequisite = name
        skills.append(
            _skill(
                f"{path['name']} [6]",
                "Grants +1 maximum Psi Point.",
                "psionic",
                1,
                species=path["species"],
                requires=prerequisite,
                psi=1,
            )
        )
    return skills


def _mutation(name, ranks):
    """Split a mutation into once-only ranks. Each rank costs 2 and does not increase."""
    skills = []
    prerequisite = None
    note = " Cannot be bought with starting character points."
    for index, effect in enumerate(ranks, start=1):
        flags = {"species": "N-DAX", "earned_only": True}
        if prerequisite:
            flags["requires"] = prerequisite
        skill_name = f"{name} [{index}]"
        skills.append(_skill(skill_name, effect + note, "mutation", 2, **flags))
        prerequisite = skill_name
    return skills


def _program(name, cost, effect, advanced=False):
    kind = "advanced_program" if advanced else "standard_program"
    return _skill(
        name,
        f"{cost}. {effect}",
        kind,
        1,
        species="Notumi Corpori",
    )


SKILL_DEFINITIONS = [
    # Combat skills. https://www.orionspherelrp.co.uk/doku.php?id=combat_skills
    _skill(
        "Toughness",
        "Each rank grants +1 locational body hit.",
        "combat",
        2,
        multiple=True,
        increases=True,
    ),
    _skill(
        "Resilience",
        "Each rank extends the death count by 100 seconds.",
        "combat",
        1,
        multiple=True,
        increases=True,
    ),
    _skill(
        "Dual Weapons Training",
        "Fight with a weapon in each hand. Two-handed weapons cannot be dual-wielded.",
        "combat",
        2,
    ),
    _skill(
        "Shield Training",
        "Use a shield to block attacks and energy fire. A shield cannot be used to attack.",
        "combat",
        2,
    ),
    _skill(
        "Large Melee Weapon Training",
        "Use a great weapon or pole weapon of 42 to 84 inches, or a thrust-safe pike.",
        "combat",
        2,
    ),
    _skill(
        "Projectile Weapon Training",
        "Use an LRP-safe bow or crossbow of at most 30 lb draw. A safety briefing is required.",
        "combat",
        4,
    ),
    _skill(
        "Thrown Weapons Training",
        "Throw an LRP-safe throwing weapon of at least 8 inches for one point of damage.",
        "combat",
        1,
    ),
    _skill(
        "Medium Energy Weapon Training",
        (
            "Use a medium energy weapon: a NERF dart gun with 10 or more darts, a clip, or a "
            "powered mechanism."
        ),
        "combat",
        2,
        group="Energy Weapon Training",
    ),
    _skill(
        "Heavy Energy Weapon Training",
        (
            "Use a heavy energy weapon that fires MEGA-style darts. It may call STRIKE at no "
            "charge cost."
        ),
        "combat",
        2,
        requires="Medium Energy Weapon Training",
        group="Energy Weapon Training",
    ),
    _skill(
        "Medium Armour Training",
        "Wear medium armour, which provides 2 locational hits.",
        "combat",
        2,
        group="Armour Training",
    ),
    _skill(
        "Heavy Armour Training",
        "Wear heavy armour (3 locational hits) or assault armour (4 locational hits).",
        "combat",
        1,
        requires="Medium Armour Training",
        group="Armour Training",
    ),
    _skill(
        "Steel Nerves",
        (
            "Each rank reduces FREEZE duration by 5 seconds. Call RESIST if the duration reaches "
            "0."
        ),
        "combat",
        2,
        multiple=True,
        increases=True,
    ),
    _skill(
        "Steel Head",
        (
            "Each rank reduces KNOCKOUT duration by 5 seconds. Call RESIST if the duration reaches "
            "0."
        ),
        "combat",
        2,
        multiple=True,
        increases=True,
    ),
    _skill(
        "Steel Viscera",
        (
            "Each rank adds another multiple of a toxin or disease's progression time, and adds "
            "one green card when you are the surgery patient."
        ),
        "combat",
        2,
        multiple=True,
        increases=True,
    ),
    # Professional skills.
    _skill(
        "First Aid",
        (
            "Reset a death count after 30 seconds of treatment, then 20, 10, and 5 seconds at "
            "ranks 2 to 4. You may then pause it at 0. Maximum 4 ranks. The cost increases by 1 "
            "each rank."
        ),
        "professional",
        1,
        multiple=True,
        increases=True,
        max_ranks=4,
    ),
    _skill(
        "Physician",
        (
            "Stop a death count, promote healing for up to 5 resting characters, diagnose and "
            "perform surgery, and administer medicaments."
        ),
        "professional",
        2,
        multiple=True,
        increases=True,
    ),
    _skill(
        "Engineer",
        (
            "Each rank grants 1 engineer work slot and knowledge of 2 mods. Repair one armour hit "
            "or a sundered item in 2 minutes, 20 seconds faster per extra rank, to a minimum of 20 "
            "seconds."
        ),
        "professional",
        2,
        multiple=True,
        increases=True,
        mods=2,
        eng_slots=1,
    ),
    _skill(
        "Extra Mods",
        "Learn 2 additional mods.",
        "professional",
        1,
        multiple=True,
        requires="Engineer",
        mods=2,
    ),
    _skill(
        "Scientist",
        (
            "Bought once. Use a scanner to locate, examine, and sample phenomena, and gain 1 "
            "generic research point."
        ),
        "professional",
        2,
        sci_slots=1,
        science="generic",
    ),
    _skill(
        "Etheric Science",
        (
            "Each rank grants 1 etheric research point and +1 green card when examining or "
            "sampling etheric phenomena."
        ),
        "professional",
        1,
        multiple=True,
        increases=True,
        requires="Scientist",
        sci_slots=1,
        science="etheric",
    ),
    _skill(
        "Corporeal Science",
        (
            "Each rank grants 1 corporeal research point and +1 green card when examining or "
            "sampling corporeal phenomena."
        ),
        "professional",
        1,
        multiple=True,
        increases=True,
        requires="Scientist",
        sci_slots=1,
        science="corporeal",
    ),
    _skill(
        "Life Science",
        (
            "Each rank grants 1 life research point and +1 green card when examining or sampling "
            "life phenomena."
        ),
        "professional",
        1,
        multiple=True,
        increases=True,
        requires="Scientist",
        sci_slots=1,
        science="life",
    ),
    _skill(
        "Aptitude",
        (
            "Children aged 7 to 11 only. Pause a death count, help one or two people heal, repair "
            "an armour hit or broken item in 1 minute, and use a scanner to survey or assist."
        ),
        "professional",
        0,
    ),
    # Spaceflight skills: consoles, the skills they unlock, and captain skills.
    *_console(
        "Helm Console",
        "Grants +3 turning speed on Helm and +3 impulse speed on any console.",
        "Replaces the basic primary bonus with +6 turning speed. The any-console bonus remains.",
    ),
    *_console(
        "Weapons Console",
        "Grants -1 beam cycle time on Weapons and +1 damage to one beam from any console.",
        (
            "Replaces the basic primary bonus with +2 beam cycle time. The any-console bonus "
            "remains."
        ),
    ),
    *_console(
        "Engineering Console",
        "Grants +40 hull on Engineering and +50 maximum energy on any console.",
        "Replaces the basic primary bonus with +80 hull. The any-console bonus remains.",
    ),
    *_console(
        "Science Console",
        "Grants +5000 science sensor range on Science and +10 shield strength on any console.",
        (
            "Replaces the basic primary bonus with +10000 science sensor range. The any-console "
            "bonus remains."
        ),
    ),
    *_console(
        "Relay Console",
        "Grants +1000 tactical sensor range on Relay and +2 probes on any console.",
        (
            "Replaces the basic primary bonus with +2000 tactical sensor range. The any-console "
            "bonus remains."
        ),
    ),
    _skill(
        "Evasive Maneuvers",
        "Once per mission, the ship instantly jumps 2U backwards and inverts its direction.",
        "spaceflight",
        2,
        requires="Helm Console [Advanced]",
    ),
    _skill(
        "Emergency Evacuation",
        (
            "Once per ground mission, a beacon returns you and one character you are touching to "
            "the intact starship after 30 seconds."
        ),
        "spaceflight",
        2,
        requires="Helm Console [Advanced]",
    ),
    _skill(
        "Concentrate Fire",
        (
            "Once per mission, discharge the backup beam capacitors to create a nuclear-scale "
            "blast. Be well clear of the target."
        ),
        "spaceflight",
        2,
        requires="Weapons Console [Advanced]",
    ),
    _skill(
        "Concussive Blast",
        (
            "Once per ground mission, after 30 seconds of roleplay, call MASS STRIKEDOWN in a "
            "directed arc."
        ),
        "spaceflight",
        2,
        requires="Weapons Console [Advanced]",
    ),
    _skill(
        "Emergency Repairs",
        "Once per mission, instantly repair all damaged ship systems by 20%.",
        "spaceflight",
        2,
        requires="Engineering Console [Advanced]",
    ),
    _skill(
        "Technical Support",
        (
            "On a ground mission, count as having 2 extra Engineer ranks for armour and SUNDER "
            "repairs, and RESIST the first SUNDER against your equipment."
        ),
        "spaceflight",
        2,
        requires="Engineering Console [Advanced]",
    ),
    _skill(
        "Sensor Ping",
        "Once per mission, instantly scan all ships within 5000 units.",
        "spaceflight",
        2,
        requires="Science Console [Advanced]",
    ),
    _skill(
        "Wide Area Scan",
        "On arrival at a ground mission, ask the encounter ref for a scan of the area.",
        "spaceflight",
        2,
        requires="Science Console [Advanced]",
    ),
    _skill(
        "Taunt",
        "Once per mission, ships within 5000 units attempt to travel directly to your location.",
        "spaceflight",
        2,
        requires="Relay Console [Advanced]",
    ),
    _skill(
        "Coordinate Hacking",
        (
            "Once per ground mission, after 30 seconds of roleplay, call MASS DISRUPT in a "
            "directed arc."
        ),
        "spaceflight",
        2,
        requires="Relay Console [Advanced]",
    ),
    _captain(
        "A Good Day To Die",
        (
            "Captain only, once per mission. Directional shields become 500 and hull becomes 300%. "
            "The crew gains an extreme and a mild condition. Requires a different Advanced console "
            "skill for each captain skill. Includes Ready Room."
        ),
    ),
    _captain(
        "Fly Her Apart",
        (
            "Captain only, once per mission. Manoeuvring systems are fully repaired and warp, "
            "impulse, and turn rate are pushed past their limits. The crew gains an extreme and a "
            "mild condition. Each captain skill needs a different Advanced console skill. Includes "
            "Ready Room."
        ),
    ),
    _captain(
        "Needs Of The Many",
        (
            "Captain only. At the end of the mission, take any 2 assigned crew conditions onto "
            "yourself. Each captain skill needs a different Advanced console skill. Includes Ready "
            "Room."
        ),
    ),
    _captain(
        "Give It All She's Got",
        (
            "Captain only, once per mission. Ship energy becomes 2500. The crew gains an extreme "
            "and a mild condition. Each captain skill needs a different Advanced console skill. "
            "Includes Ready Room."
        ),
    ),
    # Reputation skills. Faction status is 3 points, or 2 for that faction's core species.
    _skill(
        "Armaments Standing",
        (
            "Advanced Armaments charges less for weapons and may offer restricted gear. 2 points "
            "per rank. The cost does not increase."
        ),
        "reputation",
        2,
        multiple=True,
        reputation_faction="Advanced Armaments",
        reputation=1,
    ),
    _skill(
        "Spacer Renown",
        (
            "The Spacer Collective charges less for ship hire and forfeiture. 2 points per rank. "
            "The cost does not increase."
        ),
        "reputation",
        2,
        multiple=True,
        reputation_faction="Spacer Collective",
        reputation=1,
    ),
    _skill(
        "Pylon Membership",
        (
            "Galactic Energy Supplies grants favourable rates on research facilities. 2 points per "
            "rank. The cost does not increase."
        ),
        "reputation",
        2,
        multiple=True,
        reputation_faction="Galactic Energy Supplies",
        reputation=1,
    ),
    _skill(
        "Clearance Certified",
        (
            "Clearance Organisation takes a smaller cut from missions you sign up for. 2 points "
            "per rank. The cost does not increase."
        ),
        "reputation",
        2,
        multiple=True,
        reputation_faction="Clearance Organisation",
        reputation=1,
    ),
    _skill(
        "CPS Rep",
        (
            "The Corporeal Perfection Syndicate discounts advanced cybernetic implants. 2 points "
            "per rank. The cost does not increase."
        ),
        "reputation",
        2,
        multiple=True,
        reputation_faction="Corporeal Perfection Syndicate",
        reputation=1,
    ),
    _skill(
        "Lazarus Esteem",
        (
            "Lazarus Corporation discounts ReLife contracts and allows medicament shipments. 2 "
            "points per rank. The cost does not increase."
        ),
        "reputation",
        2,
        multiple=True,
        reputation_faction="Lazarus Corporation",
        reputation=1,
    ),
    _skill(
        "Ascendancy Status",
        (
            "Baseline reputation with the Ascendancy, and access to information requests. 3 points "
            "per rank, or 2 for Ascendancy Terrans. The cost does not increase."
        ),
        "reputation",
        3,
        multiple=True,
        faction="Terran Ascendancy",
        reputation=1,
    ),
    _skill(
        "Commonality Status",
        (
            "Baseline reputation with the Commonality, and access to information requests. 3 "
            "points per rank, or 2 for Elysians. The cost does not increase."
        ),
        "reputation",
        3,
        multiple=True,
        faction="Elysian Commonality",
        reputation=1,
    ),
    _skill(
        "Dominion Status",
        (
            "Baseline reputation with the Dominion, and access to information requests. 3 points "
            "per rank, or 2 for Tulaki. The cost does not increase."
        ),
        "reputation",
        3,
        multiple=True,
        faction="Tulaki Dominion",
        reputation=1,
    ),
    _skill(
        "Free Union Status",
        (
            "Baseline reputation with the Free Union, and access to information requests. 3 points "
            "per rank, or 2 for Free Union Terrans. The cost does not increase."
        ),
        "reputation",
        3,
        multiple=True,
        faction="Free Union",
        reputation=1,
    ),
    # Discipline.
    _skill(
        "Discipline",
        (
            "Grants 2 Will Points. Spend 1 Will Point to RESIST an IMBUE call or one roleplay "
            "effect."
        ),
        "discipline",
        2,
        species="Ascendancy Terran",
        will=2,
    ),
    _skill(
        "Extra Will Point",
        ("Each rank grants +1 Will Point."),
        "discipline",
        1,
        multiple=True,
        requires="Discipline",
        species="Ascendancy Terran",
        will=1,
    ),
    _skill(
        "Relentless",
        ("At 0 body or head hits, spend 1 Will Point to keep acting for 30 seconds."),
        "discipline",
        1,
        requires="Discipline",
        species="Ascendancy Terran",
    ),
    _skill(
        "Resolve",
        (
            "When unconscious or badly injured, spend Will Points to shorten the time until you "
            "are walking wounded."
        ),
        "discipline",
        1,
        requires="Discipline",
        species="Ascendancy Terran",
    ),
    _skill(
        "Iron Mind",
        ("Spend 1 Will Point to RESIST MESMERIZE, KNOCKOUT, or a psionic power."),
        "discipline",
        1,
        requires="Discipline",
        species="Ascendancy Terran",
    ),
    _skill(
        "Stalwart",
        ("While walking wounded, spend 1 Will Point to act normally for 1 minute."),
        "discipline",
        1,
        requires="Discipline",
        species="Ascendancy Terran",
    ),
    # N-DAX mutation skills. Not available with starting character points.
    *_mutation(
        "Mutate Claws",
        (
            (
                "Wear biological claw weapons. Growing or retracting them takes 30 seconds. A hit "
                "on a claw damages you as a body hit. DISARM disables it for 5 seconds. SUNDER "
                "regenerates as one body hit after 1 minute."
            ),
            "Call THROUGH with your claws once every 5 minutes.",
            "Call STRIKE with your claws once every 5 minutes.",
            "Call THROUGH with your claws once every minute instead of every 5 minutes.",
            "Call LETHAL with your claws once every 5 minutes.",
        ),
    ),
    *_mutation(
        "Mutate Musculature",
        (
            (
                "While walking or faster and wearing no armour, reduce FREEZE and ROOT by 5 "
                "seconds and RESIST STRIKEDOWN."
            ),
            (
                "While walking or faster in light armour or none, reduce FREEZE and ROOT by 5 "
                "seconds and RESIST STRIKEDOWN."
            ),
            "Gain +1 global body hit and +1 global armour hit.",
            (
                "While walking or faster in light armour or none, reduce FREEZE and ROOT by 10 "
                "seconds and RESIST STRIKEDOWN."
            ),
            (
                "While walking or faster in light armour or none, reduce FREEZE and ROOT by 20 "
                "seconds and RESIST STRIKEDOWN."
            ),
        ),
    ),
    *_mutation(
        "Mutate Rapid Recovery",
        (
            (
                "Treatment of an INJURY condition adds 1 green card to the surgery deck. You no "
                "longer need a breathable atmosphere."
            ),
            (
                "You may use one rank of Physician for surgery on yourself only. You cannot move, "
                "fight, or use other skills while doing so, and you cannot do this while "
                "unconscious or walking wounded."
            ),
            "Removing a RADIATION condition does not replace it with Chronic Radiation.",
            (
                "You automatically diagnose your own INJURY conditions. Regeneration restores 1 "
                "global body hit every 50 seconds."
            ),
            (
                "After 30 minutes, your INJURY conditions end without surgery, except conditions "
                "that cannot be regenerated."
            ),
        ),
    ),
    # Tulaki devotion.
    _skill(
        "Priestly Devotion",
        (
            "Each rank grants one major ceremony and one minor ceremony. 2 points per rank and the "
            "cost does not increase. A priest cannot buy new ranks of "
            "Heroic Devotion."
        ),
        "devotion",
        2,
        multiple=True,
        faction="Tulaki Dominion",
        species=["Tulaki Serpentine", "Tulaki Saurian", "Tulaki Megasaurian"],
    ),
    _skill(
        "Heroic Devotion",
        (
            "Gain the favour and powers of your chosen Immortal Spirit. 2 points per rank and the "
            "cost does not increase."
        ),
        "devotion",
        2,
        multiple=True,
        faction="Tulaki Dominion",
    ),
    # Psionic paths and the two non-path skills.
    _skill(
        "Psionic Potential",
        ("Grants 2 extra Psi Points. Any character who can buy a psionic path may buy this."),
        "psionic",
        1,
        multiple=True,
        increases=True,
        species=_PSIONIC_SPECIES,
        psi=2,
    ),
    _skill(
        "Psionic Aptitude",
        (
            "Children aged 7 to 11 of a psionic species only. Contribute to a psionic ritual as if "
            "you knew the power being used."
        ),
        "psionic",
        0,
        species=_PSIONIC_SPECIES,
    ),
    *_expand_paths(_load_path_catalogue()),
    # Corpori programs. Each is a skill costing 1. Standard and advanced are separate types.
    _program(
        "Repair",
        "1 charge",
        "Repair one armour hit at up to 10 metres, or two armour hits within arm's reach.",
    ),
    _program(
        "Study",
        "1 charge",
        (
            "Examine a phenomenon as a scanner at up to 10 metres, with +1 green card within arm's "
            "reach."
        ),
    ),
    _program(
        "Sample",
        "1 charge",
        (
            "Sample a phenomenon as a scanner at up to 10 metres, with +1 green card within arm's "
            "reach."
        ),
    ),
    _program(
        "Seal Wound",
        "1 charge",
        (
            "Pause the death count of a target within arm's reach while you remain there and use "
            "no other program."
        ),
    ),
    _program(
        "Barrier",
        "1 charge",
        (
            "If you have fewer than 3 field hits, gain 1 field hit. It fades after 1 hour or when "
            "lost."
        ),
    ),
    _program(
        "Erase",
        "1 charge",
        (
            "When targeted by IMBUE, replace the roleplay effect so you cannot perceive its "
            "source. It ends if that source damages you."
        ),
    ),
    _program(
        "Anchor",
        "1 charge",
        "Call RESIST to REPEL or STRIKEDOWN.",
    ),
    _program(
        "Impact",
        "1 charge",
        "Call nano STRIKE against a target's location.",
    ),
    _program(
        "Shelter",
        "2 charges",
        (
            "In an area with no hazards, gain a breathable atmosphere and minor thermal, toxic, "
            "and radiation protection from environmental hazards for 30 minutes."
        ),
    ),
    _program(
        "Flechette",
        "2 charges",
        "Call nano THROUGH against a target's location.",
    ),
    _program(
        "Force",
        "2 charges",
        "Call nano REPEL against a target.",
    ),
    _program(
        "Destroy",
        "3 charges",
        "Call nano SUNDER against a target item.",
    ),
    _program(
        "Sustain",
        "4 charges",
        (
            "If you have Physician and are in a surgery within arm's reach, ignore a card just "
            "drawn and draw another."
        ),
    ),
    _program(
        "Survive",
        "1 notum",
        "The target may call RESIST to all attacks for 30 seconds. DISRUPT breaks the effect.",
        advanced=True,
    ),
    _program(
        "Crush",
        "1 notum",
        "Call nano GLOBAL REND against a target.",
        advanced=True,
    ),
    _program(
        "Force Wave",
        "1 notum",
        "Call nano MASS REPEL.",
        advanced=True,
    ),
    _program(
        "Lockdown",
        "1 notum",
        "Call nano MASS ROOT (10).",
        advanced=True,
    ),
]
