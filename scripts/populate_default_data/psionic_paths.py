"""One entry per psionic path. Each rank is expanded into its own skill.

Rank text is the mechanical effect from the species path pages, retrieved 13 Oct 2026.
Telekinetic Fortification numbers Deflection and Shielding both as rank 3; the ranks
here follow the order on that page. Lithomorphosis requires Lithokinesis 2 on its
path page.
"""

PATHS = (
    {
        "name": "Coercion",
        "species": "Elysian",
        "ranks": (
            "Spend 1 Psi Point to call MESMERIZE.",
            "Spend 1 Psi Point to implant a minor suggestion until the event ends.",
            "Spend 1 Psi Point to force a mesmerized target to follow you.",
            ("Spend 2 Psi Points in a Psionic Aura to implant an order with a trigger " "phrase."),
            (
                "Spend 1 Psi Point to give a mesmerized target one command, lasting until "
                "it is done or 10 minutes pass."
            ),
        ),
    },
    {
        "name": "Psionic Resonance",
        "species": "Elysian",
        "ranks": (
            (
                "Spend 1 Psi Point. The target gains 1 Psi Point or 1 Will Point, up to "
                "their maximum."
            ),
            "Spend 1 or 2 Psi Points to repair a ruined item with a Crystal Mod.",
            (
                "Spend 1 Psi Point in a Psionic Aura to send a 13-word message to a named "
                "person. Needs a ref."
            ),
            (
                "Spend 2 Psi Points and 1 minute for a vague impression of past events "
                "here. Needs a ref."
            ),
            (
                "Spend 5 Psi Points in a Psionic Aura to create a Psi Crystal. Cooperative. "
                "Needs a ref."
            ),
        ),
    },
    {
        "name": "Psychosomatics",
        "species": "Elysian",
        "ranks": (
            "Spend 1 Psi Point to reset a dying target's death count to 0.",
            (
                "Spend 1 Psi Point in a Psionic Aura. The target regains 1 hit on every "
                "location, or 3 global hits."
            ),
            (
                "After 10 seconds, lose 1 body hit to restore 1 hit on that same location "
                "of a target. Costs no Psi Points."
            ),
            "Spend 1 Psi Point and 1 minute to restore all lost hits on one location.",
            "Spend 2 Psi Points and 5 seconds to end a target's death count.",
        ),
    },
    {
        "name": "Endopathoi",
        "species": "Elysian",
        "requires": ("Coercion", 1),
        "ranks": (
            (
                "Spend 1 Psi Point to IMBUE a weak disgust, sadness, surprise, or fear for "
                "10 minutes on a mesmerized target."
            ),
            (
                "Spend 1 Psi Point to IMBUE a normal one of those emotions on a mesmerized "
                "target, or a weak one within 10 metres."
            ),
            (
                "Spend 1 Psi Point to IMBUE a strong emotion on a mesmerized target, or 2 "
                "to IMBUE a normal emotion within 10 metres or a mass weak emotion."
            ),
            (
                "Spend 2 Psi Points to IMBUE a strong emotion within 10 metres, or 3 for a "
                "mass normal emotion."
            ),
            (
                "Spend 3 Psi Points to call MASS IMBUE Loathing, Grief, Amazement, or "
                "Terror for 5 minutes."
            ),
        ),
    },
    {
        "name": "Exopathoi",
        "species": "Elysian",
        "requires": ("Coercion", 1),
        "ranks": (
            (
                "Spend 1 Psi Point to IMBUE a weak anger, anticipation, joy, or trust for "
                "10 minutes on a mesmerized target."
            ),
            (
                "Spend 1 Psi Point to call EFFECT for a normal one of those emotions on a "
                "mesmerized target, or IMBUE a weak one within 10 metres."
            ),
            (
                "Spend 1 Psi Point to IMBUE a strong emotion on a mesmerized target, or 2 "
                "to IMBUE a normal emotion within 10 metres or a mass weak emotion."
            ),
            (
                "Spend 2 Psi Points to IMBUE a strong emotion within 10 metres, or 3 for a "
                "mass normal emotion."
            ),
            (
                "Spend 3 Psi Points to call MASS IMBUE Rage, Vigilance, Ecstasy, or "
                "Admiration for 5 minutes."
            ),
        ),
    },
    {
        "name": "Mnemomorphosis",
        "species": "Elysian",
        "requires": ("Coercion", 4),
        "ranks": (
            "Spend 1 Psi Point in a Psionic Aura. A willing target forgets one memory.",
            "Spend 2 Psi Points in a Psionic Aura to inflict a psionic condition.",
            "Spend 2 Psi Points. A mesmerized target forgets the past hour.",
            (
                "Spend 4 Psi Points in a Psionic Aura to inflict a psionic condition. "
                "Cooperative."
            ),
            (
                "Spend at least 3 Psi Points in a Psionic Aura to add or remove skills, "
                "with the target's permission. Needs a ref. Other Mnemomorphosis or "
                "Coercion powers can be concealed for 2 extra Psi Points."
            ),
        ),
    },
    {
        "name": "Resonant Vitality",
        "species": "Elysian",
        "requires": ("Psionic Resonance", 1),
        "ranks": (
            "Spend 1 Psi Point to blend with a large tree and become impossible to detect.",
            (
                "At a Nexus Tree, open a wormhole to another tree later in the event. The "
                "Psi Point cost depends on distance. Cooperative. Needs a ref."
            ),
            (
                "In a Psionic Aura, spend 1 Psi Point per participant to grant them a "
                "vision. Cooperative. Needs a ref."
            ),
            (
                "Spend 3 Psi Points at an active Nexus Tree so a character can use "
                "wormholes and Psi Crystals."
            ),
            (
                "At an active Nexus Tree, spend 1 Psi Point per participant to restore 3 "
                "spent Psi Points."
            ),
        ),
    },
    {
        "name": "Resonant Blade",
        "species": "Elysian",
        "requires": ("Psionic Resonance", 2),
        "ranks": (
            (
                "Spend 1 Psi Point to strike THROUGH with a melee weapon that has the Psi "
                "Crystal Weave mod."
            ),
            (
                "Spend 1 Psi Point to strike STRIKE with a melee weapon that has the Psi "
                "Crystal Weave mod."
            ),
            (
                "Spend 2 Psi Points to strike SUNDER with a melee weapon that has the Psi "
                "Crystal Weave mod."
            ),
            (
                "Spend 2 Psi Points to strike REND with a melee weapon that has the Psi "
                "Crystal Weave mod."
            ),
            (
                "Spend 2 Psi Points to strike LETHAL with a melee weapon that has the Psi "
                "Crystal Weave mod."
            ),
        ),
    },
    {
        "name": "Empathosomatics",
        "species": "Elysian",
        "requires": ("Psychosomatics", 2),
        "ranks": (
            (
                "Spend 1 Psi Point and concentrate for 10 seconds. The target must reveal "
                "that a lingering psionic effect is present."
            ),
            "Spend 1 Psi Point to suppress a target's roleplay effects for 10 minutes.",
            (
                "Spend 1 Psi Point in a Psionic Aura. After 30 seconds the target shows "
                "psionic conditions and suggestions. Concealed effects stay hidden."
            ),
            (
                "Spend 1 Psi Point and 30 seconds to take one psionic condition from a "
                "willing target."
            ),
            (
                "Spend 5 Psi Points to inflict a condition that suppresses other roleplay "
                "effects for the rest of the day. Cooperative."
            ),
        ),
    },
    {
        "name": "Psychirosi",
        "species": "Elysian",
        "requires": ("Psychosomatics", 3),
        "ranks": (
            "Spend 2 Psi Points in a Psionic Aura to gain 1 body hit for 2 hours.",
            (
                "Spend 2 Psi Points in a Psionic Aura to gain some resistance to toxins "
                "and radiation for 1 day."
            ),
            (
                "Spend 1 Psi Point. When a card draw would inflict a condition on you, "
                "draw twice and choose."
            ),
            "Spend 1 Psi Point to shorten FREEZE or KNOCKOUT by 30 seconds.",
            (
                "Spend 2 Psi Points in a Psionic Aura to gain 1 armour hit on each "
                "location for a day."
            ),
        ),
    },
    {
        "name": "Aura Development",
        "species": "Felani",
        "ranks": (
            ("Spend 1 Psi Point. Latent healing restores 2 hits every 10 minutes for " "1 hour."),
            (
                "Spend 1 Psi Point. For 1 hour, call IMBUE Calm for 10 minutes on people "
                "you are treating."
            ),
            (
                "After a 10 minute ritual, healing time halves to 5 minutes while you "
                "remain in a 10 metre area."
            ),
            (
                "A treated lead character gains +1 green card. Inside a bounded area you "
                "can treat 10 people."
            ),
            (
                "Spend 1 Psi Point, or none inside a bounded area, to suppress condition "
                "pain for 1 hour. Emotion Aura then costs no Psi Points."
            ),
        ),
    },
    {
        "name": "Aura Dynamics",
        "species": "Felani",
        "requires": ("Aura Development", 2),
        "ranks": (
            "Emotion Aura can be Joy, Curiosity, or Acceptance instead of Calm.",
            (
                "Spend 1 Psi Point to call IMBUE for 10 minutes on one target within 10 "
                "metres, using an Emotion Aura emotion."
            ),
            (
                "Emotion Aura can also be Annoyance, Worry, Trust, or Anticipation. "
                "Focusing Aura can redraw a yellow card for 1 Psi Point or a red card "
                "for 2."
            ),
            (
                "Spend 1 Psi Point and 10 minutes to duplicate one listed medicament "
                "treatment on someone else."
            ),
            (
                "Spend 1 Psi Point to IMBUE a treated character for 1 hour. They resist "
                "the opposing emotions for that hour."
            ),
        ),
    },
    {
        "name": "Aura Echoing",
        "species": "Felani",
        "requires": ("Aura Development", 3),
        "ranks": (
            (
                "Inside a bounded Psionic Aura, regain 1 Psi Point every 30 minutes. "
                "Others cannot use that aura while you do."
            ),
            (
                "Spend 2 Psi Points and 30 seconds for a rough impression of local "
                "forces and their mood. Needs a ref. Not in the main event area."
            ),
            (
                "Healing restores twice as many hits. With Bolstered Aura, that is 4 "
                "hits every 10 minutes."
            ),
            (
                "Spend 6 Psi Points and 10 minutes to restore 2 Psi Points to each "
                "treated character in the bounded area."
            ),
            (
                "Spend 2 Psi Points and 10 minutes to give treated characters in the "
                "bounded area a shared vision."
            ),
        ),
    },
    {
        "name": "Telekinesis",
        "species": "Kelki",
        "ranks": (
            "Spend 1 Psi Point to call REPEL at a character within 10 metres.",
            "Spend 1 Psi Point to call STRIKEDOWN at a character within 10 metres.",
            (
                "Spend 1 Psi Point and 10 seconds to gain 1 field hit for up to 1 hour. "
                "It is lost when you take damage."
            ),
            "Spend 2 Psi Points to call MASS REPEL in an arc of up to 180 degrees.",
            "Spend 2 Psi Points to call MASS STRIKEDOWN in an arc of up to 180 degrees.",
        ),
    },
    {
        "name": "Telekinetic Finesse",
        "species": "Kelki",
        "requires": ("Telekinesis", 2),
        "ranks": (
            "Spend 1 Psi Point to call STRIKE at a character within 10 metres.",
            "Spend 1 Psi Point to call DISARM on a held object within 10 metres.",
            "Spend 3 Psi Points to call GLOBAL STRIKE at a character within 10 metres.",
            (
                "After 5 seconds, spend 1 Psi Point to call THROUGH at a character "
                "within 10 metres."
            ),
            ("Spend 3 Psi Points to call MASS STRIKE in an arc of up to 180 degrees."),
        ),
    },
    {
        "name": "Telekinetic Fortification",
        "species": "Kelki",
        "requires": ("Telekinesis", 3),
        "ranks": (
            "Spend 1 Psi Point to RESIST REPEL or STRIKEDOWN.",
            (
                "Spend 1 Psi Point to RESIST DISARM or THROUGH. A verbal THROUGH still "
                "deals its damage."
            ),
            (
                "Spend 1 Psi Point and 10 seconds to gain 1 field hit. This can be "
                "repeated. Remaining hits fade at dawn."
            ),
            ("Spend 1 Psi Point to RESIST REND or SUNDER against worn armour or a " "held item."),
            (
                "After using shielding twice today, 1 minute of concentration at 0 field "
                "hits restores 2 field hits and costs no Psi Points."
            ),
        ),
    },
    {
        "name": "Gravitic Equilibrium",
        "species": "Kordai",
        "ranks": (
            "Spend 1 Psi Point to call ROOT 10.",
            "Spend 1 Psi Point to RESIST REPEL or STRIKEDOWN.",
            "Spend 1 Psi Point to call REPEL at a target within 10 metres.",
            (
                "Spend 1 Psi Point to call STRIKE with a melee weapon up to 3 times in "
                "the next 10 seconds."
            ),
            (
                "Spend 1 Psi Point per target so they can RESIST REPEL or STRIKEDOWN "
                "for the next hour."
            ),
        ),
    },
    {
        "name": "Gravitic Force",
        "species": "Kordai",
        "requires": ("Gravitic Equilibrium", 3),
        "ranks": (
            "Spend 2 Psi Points to call THROUGH at a character within 10 metres.",
            "Spend 2 Psi Points to improve turn rate on a starship mission.",
            (
                "After 10 seconds, spend 2 Psi Points to call MASS ROOT 5. A Singular "
                "Point then costs 1 Psi Point."
            ),
            ("Spend 2 Psi Points to call FREEZE 10 or ROOT 30 at a character within " "10 metres."),
            (
                "After 10 seconds, spend 2 Psi Points to call MASS REPEL, MASS "
                "STRIKEDOWN, or MASS ROOT 10."
            ),
        ),
    },
    {
        "name": "Gravitic Focus",
        "species": "Kordai",
        "requires": ("Gravitic Equilibrium", 4),
        "ranks": (
            "Spend 1 Psi Point to call DISARM with a melee weapon.",
            (
                "Spend 1 Psi Point to deflect blaster fire for 30 seconds while holding "
                "a melee weapon."
            ),
            (
                "Spend 2 Psi Points to call THROUGH up to 5 times in 10 seconds. A "
                "Singular Point then costs 1 Psi Point."
            ),
            ("Spend 2 Psi Points to redirect an IMBUE call to another target within " "3 metres."),
            (
                "Spend 2 Psi Points to redirect blaster fire for 30 seconds while "
                "holding a melee weapon."
            ),
        ),
    },
    {
        "name": "Lithokinesis",
        "species": "Lithos",
        "ranks": (
            (
                "Spend 1 Psi Point to call STRIKEDOWN within 10 metres. The target must "
                "be standing on earth or stone."
            ),
            (
                "Spend 2 Psi Points and meditate for 1 minute to gain 1 armour hit on "
                "each location until it is lost or the day ends."
            ),
            (
                "After 5 seconds, call REND with a small weapon, DISARM with a medium "
                "weapon, or REPEL with a large weapon."
            ),
            (
                "Consume a Psi Crystal. After 5 seconds, while conscious, regain all "
                "body hits and stop your death count."
            ),
            (
                "After 5 seconds, spend 2 Psi Points to call MASS STRIKEDOWN on everyone "
                "within 5 metres."
            ),
        ),
    },
    {
        "name": "Lithomorphosis",
        "species": "Lithos",
        "requires": ("Lithokinesis", 2),
        "ranks": (
            ("In a Psionic Aura, spend 1 Psi Point and 10 seconds to repair a " "sundered item."),
            ("After 5 seconds, spend 2 Psi Points to strike SUNDER with a melee " "weapon."),
            "Engineer work costs half as many energy chits.",
            "Spend 1 Psi Point and 10 seconds to repair a sundered item.",
            (
                "After 10 seconds, spend 2 Psi Points to call SUNDER on a held object "
                "within 10 metres."
            ),
        ),
    },
    {
        "name": "Henosis",
        "species": "Lithos",
        "requires": ("Lithokinesis", 4),
        "ranks": (
            (
                "Spend 1 Psi Point to reduce an emotional effect to a mild influence, "
                "and call RESIST."
            ),
            (
                "Spend 2 Psi Points and meditate for 1 minute in contact with stone for "
                "a vague impression of past events. Needs a ref."
            ),
            (
                "Consume a Psi Crystal. For 2 hours, regain 1 lost body hit per minute "
                "on each damaged location."
            ),
            (
                "After 1 minute, invest 2 maximum Psi Points to gain 1 locational body "
                "hit until you release them or the day ends."
            ),
            (
                "Spend 5 Psi Points to emit a Psionic Aura for 10 minutes. You cannot "
                "use other powers while maintaining it."
            ),
        ),
    },
    {
        "name": "Hydrolysis",
        "species": "Vikaas Aquerna",
        "ranks": (
            (
                "Spend 1 Psi Point to IMBUE Calm for 1 minute, or for 10 minutes if the "
                "target is you."
            ),
            (
                "Spend 1 Psi Point for an impression of local life, or call MASS DETECT "
                "DYING and MASS DETECT DEADLY CONDITION. The impression needs a ref."
            ),
            (
                "Spend 2 Psi Points to call MASS IMBUE for 5 minutes with the emotion "
                "you currently feel. It cannot be directed."
            ),
            (
                "Spend 1 Psi Point and treat up to 5 organic targets for 5 minutes. "
                "Each regains 1 hit per location, or 3 global hits."
            ),
            "In a Psionic Aura, regain 1 spent Psi Point every 10 minutes.",
        ),
    },
    {
        "name": "Diffusion",
        "species": "Vikaas Aquerna",
        "requires": ("Hydrolysis", 3),
        "ranks": (
            (
                "Spend 1 Psi Point to IMBUE your current emotion for 10 minutes on a "
                "target within 10 metres."
            ),
            "Spend 1 Psi Point to IMBUE yourself with any emotion for 10 minutes.",
            (
                "Spend 2 Psi Points and meditate for 1 minute. For 2 hours you need not "
                "act out roleplay effects, but they still count as your emotion."
            ),
            (
                "After 5 minutes of movement, spend 2 Psi Points to treat one toxic or "
                "radiation condition and lose 1 hit on each location. Heart of the "
                "Storm then costs 1 Psi Point."
            ),
            (
                "Spend 2 Psi Points to call a directed MASS IMBUE for 5 minutes with a "
                "chosen emotion."
            ),
        ),
    },
    {
        "name": "Osmosis",
        "species": "Vikaas Aquerna",
        "requires": ("Hydrolysis", 2),
        "ranks": (
            (
                "Spend 1 Psi Point to diagnose a condition on a living organic target "
                "as Physician rank 2, or as an examine with 2 successes."
            ),
            (
                "Spend 1 Psi Point to survey for life phenomena with 3 successes, or "
                "examine one with 3 extra green cards."
            ),
            (
                "Spend 2 Psi Points while assisting a card draw. The target draws 2 "
                "cards and chooses one."
            ),
            (
                "Spend 2 Psi Points and meditate for 1 minute for a vague empathic "
                "impression of past events. Needs a ref."
            ),
            (
                "Spend 3 Psi Points and meditate for 5 minutes to read a target's "
                "psionic conditions. 2 more Psi Points and 5 minutes expires one that "
                "has an expiry."
            ),
        ),
    },
)
