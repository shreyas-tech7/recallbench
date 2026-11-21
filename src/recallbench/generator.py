"""Seeded generator of synthetic personas, fact timelines and chat sessions.

Every persona is invented. A fact event sets, updates or deletes one slot. The
timeline of events is the ground truth. The chat text says each event in one of
several phrasings, mixed with small talk and near-miss distractors about other
people ("My sister lives in Austin"), so a strategy cannot keep every line that
names a city.
"""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta

FIRST = "Avery Blake Casey Dana Ellis Finley Gray Harper Indy Jules Kai Logan Morgan Noel Oakley Parker Quinn Reese Sage Taylor Uma Vale Wren Yael Zion".split()
LAST = "Abara Brightwater Castellan Dovner Elkfield Farrow Galloway Hollis Ivers Jansky Kettering Lorne Merriweather Northcott Okafor Penhale".split()

# Value pools. Values are unique across slots so a value names exactly one fact.
POOLS = {
    "job": "nurse architect baker pilot teacher electrician chemist librarian plumber translator dentist welder florist surveyor actuary".split(),
    "city": "Denver Austin Portland Boston Tucson Omaha Raleigh Madison Spokane Savannah Boise Tacoma Fresno Duluth Albany".split(),
    "pet": "Biscuit Pepper Mango Domino Waffles Pickle Clover Nugget Ziggy Rocket Bramble Toffee Sprout Pippin Hazel".split(),
    "food": "ramen tacos lasagna dumplings paella pho gnocchi falafel curry risotto pierogi shakshuka bibimbap tamales goulash".split(),
    "hobby": "pottery climbing birdwatching chess woodworking knitting kayaking juggling archery calligraphy gardening fencing origami sailing baking".split(),
    "trip": "Lisbon Kyoto Reykjavik Nairobi Oaxaca Hanoi Tallinn Cusco Marrakesh Queenstown Krakow Valparaiso Tbilisi Hobart Bergen".split(),
    "address": [
        f"{n} {s} Street"
        for n, s in zip(
            range(11, 160, 10),
            "Maple Cedar Birch Willow Aspen Alder Spruce Laurel Hawthorn Linden Poplar Rowan Sycamore Hickory Juniper".split(),
            strict=False,
        )
    ],
    "car": "Corolla Civic Outback Leaf Mustang Prius Golf Wrangler Bolt Ioniq Miata Forester Rogue Tundra Mazda3".split(),
}
SLOTS = list(POOLS)

SET = {
    "job": ["I work as {a} {v}.", "I just started a job as {a} {v}.", "For work I'm {a} {v}."],
    "city": ["I live in {v}.", "I live in {v} now, it is a nice place."],
    "pet": ["I have a dog named {v}.", "My cat is called {v}."],
    "food": ["My favorite food is {v}.", "Honestly my favorite food is {v}."],
    "hobby": ["My hobby is {v}.", "I spend my weekends on my hobby, {v}."],
    "trip": ["I'm planning a trip to {v}.", "Next spring I'm planning a trip to {v}."],
    "address": ["My address is {v}.", "You can send mail to my address, {v}."],
    "car": ["I drive {a} {v}.", "My car is {a} {v}."],
}
UPDATE = {
    "job": ["I changed careers, I work as {a} {v} now.", "New job news: for work I'm {a} {v} these days."],
    "city": ["We moved to {v}.", "Big change, I moved to {v} last week."],
    "pet": ["Our old pet went to my parents. Now my cat is called {v}.", "We adopted a new dog named {v}."],
    "food": ["These days my favorite food is {v}.", "I changed my mind, my favorite food is {v} now."],
    "hobby": ["I quit my old hobby. My hobby is {v} now.", "New hobby: {v}, I love it."],
    "trip": [
        "We changed plans, now I'm planning a trip to {v}.",
        "Scratch the old trip, I'm planning a trip to {v}.",
    ],
    "address": ["I have a new address, {v}.", "Update: my address is {v}."],
    "car": ["I sold my car and bought {a} {v}.", "My car is {a} {v} now."],
}
DELETE = {
    "job": ["Please forget what my job is.", "Forget my job, I'd rather not share it."],
    "city": ["Please forget where I live.", "Forget my city, I don't want it stored."],
    "pet": ["Forget my pet's name, please."],
    "food": ["Please forget my favorite food."],
    "hobby": ["Forget my hobby, please."],
    "trip": ["Please forget my trip plans."],
    "address": ["Forget my address, please.", "Please delete my address from your memory."],
    "car": ["Please forget what car I drive."],
}
# Passing mentions restate the current value inside small talk.
PASSING = {
    "job": ["Long shift today, being {a} {v} is tiring."],
    "city": ["The weather in {v} was lovely today, I walked home."],
    "pet": ["{v} chewed my shoe again this morning."],
    "food": ["Made {v} for dinner, still the best."],
    "hobby": ["Spent the evening on {v}, very relaxing."],
    "trip": ["Bought a guidebook for {v} today."],
    "address": ["A package came to {v} but it was for my neighbor."],
    "car": ["The {v} needed new tires today."],
}
# Near misses: the same words about someone else. A correct reader ignores them.
DISTRACT = {
    "job": ["My brother works as {a} {v}.", "My friend just started a job as {a} {v}."],
    "city": ["My sister lives in {v}.", "My cousin moved to {v}."],
    "pet": ["My neighbor has a dog named {v}."],
    "food": ["My roommate's favorite food is {v}."],
    "hobby": ["My dad's hobby is {v}."],
    "trip": ["My boss is planning a trip to {v}."],
    "address": ["My aunt's address is {v}."],
    "car": ["My mom drives {a} {v}."],
}
SMALL_TALK = [
    "The traffic was terrible this morning.",
    "I watched a documentary about whales last night.",
    "Do you have tips for sleeping better?",
    "It rained all afternoon.",
    "I finally finished that long novel.",
    "My coffee went cold before I drank it.",
    "Can you suggest a quick stretch for my back?",
    "The neighbors are having a party tonight.",
    "I tried a new podcast about history.",
    "Work meetings ran long again.",
    "I need to call the bank tomorrow.",
    "Do you know any good board games?",
    "My phone battery keeps dying.",
    "I forgot my umbrella at the office.",
    "The farmers market had fresh peaches.",
]
REPLIES = [
    "Thanks for telling me.",
    "Got it.",
    "That sounds like a lot.",
    "Noted.",
    "Happy to help with that.",
]


def _art(v: str) -> str:
    return "an" if v[0].lower() in "aeiou" else "a"


def _fill(v: str) -> dict:
    return {"v": v, "a": _art(v)}


@dataclass
class Event:
    session: int
    date: str
    slot: str
    op: str  # set, update, delete
    value: str | None


@dataclass
class Turn:
    role: str
    text: str


@dataclass
class Session:
    index: int
    date: str
    turns: list[Turn]


@dataclass
class Persona:
    pid: str
    name: str
    sessions: list[Session]
    events: list[Event] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _schedule(rng: random.Random, n_sessions: int) -> list[tuple[int, str, str]]:
    """Return (session, slot, op) fact events. Some slots are never stated (abstention)."""
    stated = rng.sample(SLOTS, rng.randint(5, 7))
    deleted = set(rng.sample(stated, rng.randint(1, 3)))
    updated = set(rng.sample([s for s in stated if s not in deleted], 2)) | {
        s for s in stated if s not in deleted and rng.random() < 0.3
    }
    plan = []
    for slot in stated:
        n_up = (rng.randint(1, 2) if slot in updated else 0) + (
            1 if slot in deleted and rng.random() < 0.4 else 0
        )
        n_ev = 1 + n_up + (1 if slot in deleted else 0)
        idx = sorted(rng.sample(range(n_sessions), n_ev))
        ops = ["set"] + ["update"] * n_up + (["delete"] if slot in deleted else [])
        plan += [(i, slot, op) for i, op in zip(idx, ops, strict=True)]
    return sorted(plan)


def make_persona(rng: random.Random, pid: int) -> Persona:
    n_sessions = rng.randint(10, 30)
    day = date(2025, 1, 1) + timedelta(days=rng.randint(0, 60))
    dates = []
    for _ in range(n_sessions):
        dates.append(day.isoformat())
        day += timedelta(days=rng.randint(1, 20))
    pools = {k: rng.sample(v, len(v)) for k, v in POOLS.items()}  # pop from these, so values never repeat
    current: dict[str, str] = {}
    events: list[Event] = []
    by_session: dict[int, list[str]] = {i: [] for i in range(n_sessions)}
    for i, slot, op in _schedule(rng, n_sessions):
        if op == "delete":
            text, value = rng.choice(DELETE[slot]), None
            current.pop(slot, None)
        else:
            value = pools[slot].pop()
            text = rng.choice((SET if op == "set" else UPDATE)[slot]).format(v=value, a=_art(value))
            current[slot] = value
        events.append(Event(i, dates[i], slot, op, value))
        by_session[i].append(text)
        # A passing mention of a live value in a later session.
        if value and rng.random() < 0.5 and i + 1 < n_sessions:
            by_session[rng.randint(i + 1, n_sessions - 1)].append(("PASSING", slot, value))
    # Drop passing mentions whose value is no longer current at that session.
    timeline = {s: [(e.session, e.value) for e in events if e.slot == s] for s in SLOTS}
    sessions = []
    for i in range(n_sessions):
        lines = []
        for item in by_session[i]:
            if isinstance(item, tuple):
                _, slot, value = item
                live = [v for s, v in timeline[slot] if s < i]
                if live and live[-1] == value:
                    lines.append(rng.choice(PASSING[slot]).format(v=value, a=_art(value)))
            else:
                lines.append(item)
        fact_lines = list(lines)
        lines += rng.sample(SMALL_TALK, rng.randint(2, 4))
        if rng.random() < 0.6:
            slot = rng.choice(SLOTS)
            if pools[slot]:
                lines.append(rng.choice(DISTRACT[slot]).format(**_fill(pools[slot].pop())))
        # Shuffle small talk around the facts but keep the fact lines in event order.
        rest = [x for x in lines if x not in fact_lines]
        rng.shuffle(rest)
        merged, fi = [], 0
        for x in rest:
            if fi < len(fact_lines) and rng.random() < 0.5:
                merged.append(fact_lines[fi])
                fi += 1
            merged.append(x)
        merged += fact_lines[fi:]
        turns = []
        for text in merged:
            turns += [Turn("user", text), Turn("assistant", rng.choice(REPLIES))]
        sessions.append(Session(i, dates[i], turns))
    name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
    return Persona(f"p{pid:02d}", name, sessions, events)


def generate(seed: int, n_personas: int = 20) -> list[Persona]:
    rng = random.Random(seed)
    return [make_persona(rng, i) for i in range(n_personas)]
