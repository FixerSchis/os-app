"""Species abilities from the wiki Game Rules sections that only need printed text.

Abilities with app mechanics (starting skills, discounts, bans, rank caps, condition
timing, psi, Black Frost, group income) are seeded separately. Body hits and death
counts come from the species record, so they have no ability here.
https://www.orionspherelrp.co.uk/doku.php?id=species
"""

_TULAKI_DEVOTION = (
    "Devotion",
    "May buy ranks of Priestly Devotion, or Heroic Devotion if Devoted.",
)


def _psionic_paths(paths):
    return ("Psionic paths", f"May buy psionic powers from {paths} and its branch paths.")


SPECIES_ABILITIES = {
    "Ascendancy Terran": (
        (
            "Discipline training",
            "May buy Discipline skills, representing the Ascendancy's brutal training "
            "and conditioning.",
        ),
    ),
    "Borean": (("Regeneration", "Regain 1 lost body hit on each location every 5 minutes."),),
    "Coronite": (
        (
            "Specialist treatment",
            "First Aid and Physician only work on a Coronite if the user has at least 1 rank "
            "of Etheric Science or is a Coronite. An Engineer can reset, pause, or stop a "
            "Coronite's death count as if they had First Aid and Physician at their Engineer "
            "rank, but cannot heal them or perform surgery. A Coronite Engineer can reset or "
            "pause their own death count, but not end it.",
        ),
        (
            "Plasma-gaseous physiology",
            "At 0 global hits, become Walking Wounded instead of Unconscious or Badly "
            "Injured, and start the death count immediately. Immune to DISEASE and TOXIC "
            "conditions unless they have the Gaseous, Energy Being, or Universal keyword. "
            "Does not need a breathable atmosphere. Most RADIATION conditions have altered "
            "effects, at the referee's discretion. Medicaments only work when doped with "
            "Yurian Lattice Plasma, unless a condition's cure needs a different exotic "
            "substance.",
        ),
        (
            "Ionic charge",
            "Item abilities cost 1 less Charge, so 1-Charge abilities are free. Alternatively, "
            "grant this to another character by staying in close contact with them. The "
            "Coronite cannot take other actions while doing so.",
        ),
    ),
    "Cradian": (
        (
            "Resolute Voice",
            "While in a one-to-one conversation with another character, roleplay effects on "
            "that character are suppressed. Show-me lammie.",
        ),
        (
            "Poem of the Will",
            "Once per event, a stirring speech lets up to 5 listening characters call RESIST "
            "to the next roleplay effect that affects them. It expires when used or after 2 "
            "hours. Show-me lammie.",
        ),
        (
            "In Defiance of Dread",
            "Show the Game Team a notable painting, poem, song, or other artwork made before "
            "the event to call RESIST to roleplay effects that cause fear or apprehension for "
            "the rest of that event.",
        ),
    ),
    "Elysian": (
        (
            "Psionic paths",
            "May buy psionic powers from the Coercion, Psionic Resonance, and Psychosomatics "
            "root paths and their branch paths.",
        ),
        (
            "Nexus trees",
            "Attuned to Commonality Nexus Trees, and can travel through them when the path "
            "is opened.",
        ),
    ),
    "Etherna": (
        (
            "Energy sense",
            "Roleplay investigating for at least 1 minute to Survey the area for Etheric "
            "Science phenomena, and Examine an identified phenomenon with the Card Draw "
            "System, without the Scientist skill. When leading, add Etheric Science ranks as "
            "green cards. With at least 1 rank of Etheric Science, gain 1 automatic success. "
            "Can assist other Etherna or Scientists examining Etheric Science phenomena. "
            "Needs a referee.",
        ),
    ),
    "Felani": (
        _psionic_paths("the Aura Development path"),
        (
            "Latent psionic healing",
            "When resting and not in combat, treat up to 5 willing or unresisting characters, "
            "including themselves. While they stay within 10 metres, they regain 1 lost body "
            "hit every 10 minutes. Needs some roleplayed interaction, which does not have to "
            "be medical.",
        ),
        (
            "Hollow-boned and thin-skinned",
            "Call RESIST to STRIKEDOWN or REPEL when it is successfully parried, or blocked "
            "with a shield. Cannot use or wear heavy armour, heavy energy weapons, or large "
            "melee weapons.",
        ),
    ),
    "Gardener": (
        ("Regeneration", "Regain 1 lost body hit on each location every 30 minutes."),
        (
            "Melody",
            "Hears a Melody from their home ecosystem: feelings, intents, and impressions "
            "that push its agenda. Roleplay receiving them; acting on them is optional. "
            "Referees may occasionally supply messages.",
        ),
        (
            "Parasitic biology",
            "Cannot use the Lazarus Corporation Rebirth Process as it currently exists.",
        ),
    ),
    "Ikunkuma": (
        (
            "Appraisal",
            "With a referee present, studying a crafted object for a while may reveal extra "
            "information about it. Tell a nearby referee. Nothing is guaranteed.",
        ),
        (
            "Scavengers",
            "May occasionally receive extra objects or game items in the character pack, at "
            "the Game Team's discretion.",
        ),
    ),
    "Kelki": (_psionic_paths("the Telekinesis root path"),),
    "Kordai": (
        _psionic_paths("the Gravitic Equilibrium root path"),
        (
            "Aura Sensitivity",
            "Feel profound Awe or Fear when affected by psionic phenomena, such as a PSIONIC "
            "ability or a PSIONIC condition. This roleplay effect is weaker than an emotional "
            "effect a psionic power causes, and anything that suppresses roleplay effects "
            "suppresses it. A psionic power or Psionic Aura prevents any action but movement. "
            "Powers used on the Kordai inside a Psionic Aura may act strangely with a referee "
            "present; otherwise the user feels mental static for 15 minutes. A long-lasting "
            "phenomenon such as a condition only affects them for about 15 minutes, but they "
            "never adjust to a Psionic Aura. Their own powers do not affect them, and other "
            "Kordai cause a weaker effect. Spend 1 Psi Point to suppress it for about 30 "
            "minutes. May be briefed with extra information.",
        ),
    ),
    "Lithos": (
        _psionic_paths("the Lithokinesis root path"),
        (
            "Mineral physiology",
            "A Physician must have at least 1 rank of Corporeal Science, or be Lithos, to "
            "treat a Lithos. Medicaments only work when doped with Spectrum Inhibitor, unless "
            "a condition's cure needs a different exotic substance. Immune to DISEASE and "
            "TOXIC conditions unless they have the MINERAL or UNIVERSAL keyword.",
        ),
        (
            "Psi-crystal neurons",
            "Emotions from the EFFECT call are more intense and last twice as long. A new "
            "EFFECT call immediately ends any earlier one.",
        ),
    ),
    "N-DAX": (
        (
            "Regeneration",
            "Regain 1 lost global hit per minute. Stop being Unconscious, Badly Injured, or "
            "Walking Wounded on reaching 1 global hit. LETHAL and the death count work as "
            "normal.",
        ),
        (
            "Lightning Reflexes",
            "While moving at least at a rapid walk and wearing no armour, FREEZE lasts 5 "
            "seconds less and STRIKEDOWN is RESISTed.",
        ),
        (
            "Adaptive physiology",
            "May buy Mutate Claws, Mutate Musculature, and Mutate Rapid Recovery, using only "
            "character points earned by playing this character.",
        ),
    ),
    "Notumi Cerebri": (
        (
            "Techno-organic metabolism",
            "Surgery by a Physician who is not Cerebri or Corpori needs an Engineer's help. "
            "That can be the Physician, and a separate Engineer adds 1 green card as an "
            "assistant. Physicians can stop the death count, and First Aiders pause or reset "
            "it, as normal. Physician treatment does not restore body hits; Medicaments, "
            "Devices, and the Elevation Control Core do.",
        ),
        (
            "Cyber-nanite internals",
            "Has an Elevation Control Core, a lammied Device that can be SUNDERed. Spend its "
            "Charges to regain body hits after a short rest. It must stay attached, and "
            "removing it needs a surgery with 3 successes. With a working core, their own "
            "cybernetic implant abilities cost 1 less Charge. An unblocked DISRUPT becomes a "
            "30 second FREEZE, which stacks with cybernetic neural shock.",
        ),
        (
            "The Bane",
            "If the Control Core is removed or damaged, such as by SUNDER, all body hit damage "
            "counts as LETHAL and starts the death count, they cannot move faster than a slow "
            "walk without help, and they are more susceptible to DISEASE, TOXIC, and RADIATION "
            "conditions. An Engineer can repair a SUNDERed core. A destroyed or removed core "
            "needs another power source.",
        ),
    ),
    "Notumi Corpori": (
        (
            "Nanotech user",
            "Starts with a Nanodeck, a lammied Device that can be SUNDERed. Spend its Charges "
            "to generate ranged calls and effects from known programs; it must be attached to "
            "be used. An Engineer needs at least 1 rank of Corporeal Science to mod it. A "
            "DISRUPT on armour or body hits stops Nanodeck use for 5 minutes. Learn more "
            "programs with the Extra Programs skill. Can attach Notum to a Nanodeck without "
            "Corporeal Science.",
        ),
    ),
    "Raegar": (
        (
            "Inured to pain",
            "Suffer reduced pain from conditions and roleplay effects, and act relatively "
            "normally with burns, broken limbs, and anything short of extreme agony. Still "
            "respond in some way; fighting with a broken arm is still impossible.",
        ),
    ),
    "Thrah'Kah": (
        (
            "Feel No Pain",
            "Ignore any reference to pain in roleplay effects or conditions. Surgery to "
            "install Corporeal Perfection Syndicate cybernetics has 1 fewer black card.",
        ),
        (
            "Strength of Steel",
            "Armour of any category visibly modified with crude extra plates and bolts gives "
            "1 extra locational armour hit on each armoured location.",
        ),
        (
            "Hardy Constitution",
            "Minor RADIATION and TOXIC Protection at all times, reducing environmental "
            "hazards of those types.",
        ),
    ),
    "Tulaki Serpentine": (_TULAKI_DEVOTION,),
    "Tulaki Saurian": (_TULAKI_DEVOTION,),
    "Tulaki Megasaurian": (
        _TULAKI_DEVOTION,
        (
            "Unique phenotype",
            "Further abilities based on the physrep, agreed with the Game Team before or at "
            "the start of the first event.",
        ),
        (
            "Environmental nano-treatment",
            "May use Megasaurian Environmental Nano-treatment to reduce bulky trappings for "
            "a time.",
        ),
    ),
    "Urg": (
        ("Tireless", "May ignore tiredness and exhaustion from roleplay effects and conditions."),
        ("Hard to stop", "May move at up to a normal walking pace while Walking Wounded."),
    ),
    "Vikaas Aquerna": (
        _psionic_paths("the Hydrolysis path"),
        (
            "Diffuse empaths",
            "Tend to mirror the emotional state of those around them, and should roleplay "
            "it. This is weaker than the EFFECT call.",
        ),
        (
            "Resistant to physical trauma",
            "Call RESIST to the first INJURY condition to afflict them each day.",
        ),
        (
            "Breathing apparatus",
            "After 30 minutes without their breathing apparatus, cannot use psionic "
            "abilities, professional skills, or combat skills other than Toughness and "
            "Resilience, and cannot speak words. Communicate with non-verbal sounds and "
            "sign language instead.",
        ),
    ),
    "Wrathian": (
        (
            "Toxic biology",
            "Immune to RADIATION and TOXIC conditions unless they have the Wrathian keyword, "
            "including Universal ones. Unaffected by Glowfish Toxin, including its positive "
            "effects. Needs a breathing mask that delivers toxins; without it they slowly "
            "sicken and may die.",
        ),
        (
            "Wrathian toxins",
            "Staying in close contact afflicts others with nausea and weakness, and can "
            "disrupt the concentration needed for psionic powers or Discipline skills. A "
            "Physician working on a Wrathian without protection may be poisoned. Show-me "
            "lammie.",
        ),
    ),
    "Xak'Noth": (
        (
            "Highly resilient",
            "MAJOR RADIATION Protection, and a RADIATION condition can be treated one more "
            "time each event. Can survive 10 minutes without a breathable atmosphere. COLD "
            "and HOT hazards take 10 minutes longer to affect them.",
        ),
        (
            "Natural armour",
            "Cannot wear armour, but has 3 natural armour hits on every location. An Engineer "
            "cannot repair it; a Physician with at least 1 rank of Life Science, or who is "
            "Xak'Noth, heals it like body hits.",
        ),
    ),
}
