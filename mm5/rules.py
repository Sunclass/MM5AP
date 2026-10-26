from dataclasses import dataclass
from math import ceil
from typing import TYPE_CHECKING, Sequence
from typing_extensions import override
from BaseClasses import CollectionState
from NetUtils import JSONMessagePart
from . import names
from .locations import get_boss_locations, mm5_regions
from rule_builder.rules import CanReachLocation, HasAll, HasAny, Has, OptionFilter, Rule, True_, TWorld

if TYPE_CHECKING:
    from . import MM5World

bosses: dict[str, int] = {
    "Gravity Man": 0,
    "Wave Man": 1,
    "Stone Man": 2,
    "Gyro Man": 3,
    "Star Man": 4,
    "Charge Man": 5,
    "Napalm Man": 6,
    "Crystal Man": 7,
    "Dark Man 1": 8,
    "Dark Man 2": 9,
    "Dark Man 3": 10,
    "Dark Man 4": 11,
    "Big Pets": 12,
    "Circring Q9": 13,
    "Wily Press": 14,
    "Wily Machine 5": 15,
    "Wily Capsule II": 16,
}

weapons_to_id: dict[str, int] = {
    "Mega Buster": 0,
    names.gravity_hold: 1,
    names.water_wave: 2,
    names.power_stone: 3,
    names.gyro_attack: 4,
    names.star_crash: 5,
    names.charge_kick: 6,
    names.napalm_bomb: 7,
    names.crystal_eye: 8,
    names.rush_coil: 9,
    names.rush_jet: 10,
    names.super_arrow: 11,
    names.beat: 12,
}

weapon_damage: dict[int, list[int]] = {
    0: [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, ],  # Mega Buster
    1: [0, 0, 0, 4, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, ],  # Gravity Hold
    2: [1, 1, 1, 1, 4, 1, 1, 1, 3, 1, 1, 1, 0, 0, 0, 0, 0, ],  # Water Wave
    3: [1, 1, 1, 1, 1, 4, 1, 1, 1, 1, 1, 2, 1, 1, 0, 1, 0, ],  # Power Stone
    4: [1, 1, 1, 1, 1, 1, 1, 4, 1, 1, 2, 1, 1, 4, 1, 1, 1, ],  # Gyro Attack
    5: [4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 0, 4, 1, 1, ],  # Star Crash
    6: [1, 4, 0, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, ],  # Charge Kick
    7: [1, 1, 4, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, ],  # Napalm Bomb
    8: [1, 1, 1, 1, 1, 1, 3, 1, 1, 2, 1, 1, 4, 1, 1, 1, 1, ],  # Crystal Eye
    9: [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, ],  # Rush Coil
    10: [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, ],  # Rush Jet
    11: [1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 1, 1, 1, 1, 4, 1, ],  # Super Arrow
    12: [1, 1, 1, 1, 1, 1, 1, 1, 3, 3, 3, 3, 1, 1, 1, 1, 2, ],  # Beat
}

weapons_to_name: dict[int, str] = {
    1: names.gravity_hold,
    2: names.water_wave,
    3: names.power_stone,
    4: names.gyro_attack,
    5: names.star_crash,
    6: names.charge_kick,
    7: names.napalm_bomb,
    8: names.crystal_eye,
    9: names.rush_coil,
    10: names.rush_jet,
    11: names.super_arrow,
    12: names.beat
}

minimum_weakness_requirement: dict[int, int] = {
    0: 1,  # Mega Buster is free
    1: 4,  # 7 applications of Gravity Hold (Screen nuke)
    2: 2,  # 14 shots of Water Wave
    3: 1,  # 28 shots of Power Stone
    4: 1,  # 28 shots of Gyro Attack
    5: 2,  # 9 shots of Star Crash if close by enemy, but 14 when firing
    6: 1,  # 28 dashes of Charge Kick
    7: 1,  # 28 shots of Napalm Bomb
    8: 1,  # 28 applications of Crystal Eye
    9: 1,  # Rush Coil doesn't use energy to fire
    10: 1,  # Rush Jet doesn't use energy to fire
    11: 2, #14 shots of Super Arrow while not standing on it
    12: 2, #14 shots of Beat
}

robot_masters: dict[int, str] = {
    0: "Gravity Man Defeated",
    1: "Wave Man Defeated",
    2: "Stone Man Defeated",
    3: "Gyro Man Defeated",
    4: "Star Man Defeated",
    5: "Charge Man Defeated",
    6: "Napalm Man Defeated",
    7: "Crystal Man Defeated"
}

weapon_costs = {
    0: 0,
    1: 4,
    2: 2,
    3: 1,
    4: 1,
    5: 2,
    6: 1,
    7: 1,
    8: 1,
    9: 0,
    10: 0,
    11: 2,
    12: 2,
}


@dataclass
class CanDefeatEnoughRBMs(Rule["MM5World"], game="Mega Man 5"):
    @override
    def _instantiate(self, world: "MM5World") -> Rule.Resolved:
        return self.Resolved(tuple([(key, tuple(val)) for key, val in sorted(world.wily_3_weapons.items())]),
                             world.options.wily_3_requirement.value,
                             player=world.player, caching_enabled=True)

    class Resolved(Rule.Resolved):
        boss_requirements: tuple[tuple[int, tuple[int, ...]], ...]
        required: int

        @override
        def item_dependencies(self) -> dict[str, set[int]]:
            return {
                weapons_to_name[x]: {id(self)} for boss, weapons in self.boss_requirements for x in weapons
            }

        @override
        def explain_json(self, state: CollectionState | None = None) -> list[JSONMessagePart]:
            explain_strs = self.explain_str(state).splitlines()
            messages: list[JSONMessagePart] = [{"type": "text", "text": explain_strs[0]}]
            for rbm in explain_strs[1:]:
                color = "salmon" if "Cannot" in rbm else "green"
                messages.append({"type": "color", "text": rbm, "color": color})
            return messages

        @override
        def explain_str(self, state: CollectionState | None = None) -> str:
            explain_str = f"Required RBMs: {self.required}"
            for boss, reqs in self.boss_requirements:
                if boss in robot_masters:
                    verb = "Can Defeat" if state.has_all(map(lambda x: weapons_to_name[x], reqs), self.player) \
                        else "Cannot Defeat"
                    explain_str += f"\n{robot_masters[boss][:-9]}: {verb}"
            return explain_str

        @override
        def _evaluate(self, state: "CollectionState") -> bool:
            can_defeat = 0
            for boss, reqs in self.boss_requirements:
                if boss in robot_masters:
                    if state.has_all(map(lambda x: weapons_to_name[x], reqs), self.player):
                        can_defeat += 1
                        if can_defeat >= self.required:
                            return True
            return False


HasRushCoil = Has(names.rush_coil)
HasRushJet = Has(names.rush_jet)
HasSuperArrow = Has(names.super_arrow)
HasVertical = HasRushCoil | HasSuperArrow | HasRushJet

STATIC_LOCATION_RULES: dict[str, Rule] = {
    names.proto_man_1_boss: HasVertical,
    names.proto_man_2_boss: HasVertical,
    names.proto_man_3_boss: HasVertical,
    names.wily_1_boss: HasVertical,
    names.wily_2_boss: HasRushJet | HasSuperArrow,
}

STATIC_ENTRANCE_RULES: dict[str, Rule] = {


}

STATIC_1UP_RULES: dict[str, Rule] = {
    names.stone_man_c4:HasVertical,
    names.crystal_man_c3:HasVertical,
    names.proto_man_2_c1:HasVertical,
    names.proto_man_2_c5:HasVertical,
    names.wily_3_c1:HasVertical,
    names.wily_3_c2:HasVertical,
}

STATIC_ENERGY_RULES: dict[str, Rule] = {
    names.gravity_man_c1: HasVertical,
    names.proto_man_1_c1:HasVertical,
    names.proto_man_1_c2:HasVertical,
    names.proto_man_1_c4:HasVertical,
    names.proto_man_1_c5:HasVertical,
    names.proto_man_2_c2:HasVertical,
    names.proto_man_3_c1:HasVertical,
    names.wily_1_c3:HasVertical,
}


def set_rules(world: "MM5World") -> None:
    from .options import RandomWeaknesses
    # most rules are set on region, so we only worry about rules required within stage access
    # or rules variable on settings
    if hasattr(world.multiworld, "re_gen_passthrough"):
        slot_data = getattr(world.multiworld, "re_gen_passthrough")["Mega Man 5"]
        world.weapon_damage = slot_data["weapon_damage"]
    else:
        if world.options.random_weakness == world.options.random_weakness.option_shuffled:
            weapon_tables = [table.copy() for weapon, table in weapon_damage.items() if weapon != 0 and (world.options.random_rush or weapon not in (9, 10))]
            world.random.shuffle(weapon_tables)
            for i in range(1, 9 if not world.options.random_rush else 13):
                world.weapon_damage[i] = weapon_tables.pop()
        elif world.options.random_weakness == world.options.random_weakness.option_randomized:
            world.weapon_damage = {i: [] for i in range(9 if not world.options.random_rush else 11)}
            for boss in range(16):
                for weapon in world.weapon_damage:
                    world.weapon_damage[weapon].append(min(14, max(0, int(world.random.normalvariate(3, 3)))))
                if not any([world.weapon_damage[weapon][boss] >= 4
                            for weapon in range(1, 9 if not world.options.random_rush else 13)]):
                    # failsafe, there should be at least one defined non-Buster weakness
                    weapon = world.random.randint(1, 7)
                    world.weapon_damage[weapon][boss] = world.random.randint(4, 14)  # Force weakness
            # handle Wily Capsule
            boss = 16
            for weapon in world.weapon_damage:
                world.weapon_damage[weapon].append(0)
            weapon = world.random.choice(list(world.weapon_damage.keys()))
            world.weapon_damage[weapon][boss] = minimum_weakness_requirement[weapon]

        if world.options.strict_weakness:
            for weapon in weapon_damage:
                for i in range(16):
                    if weapon > 8 and not world.options.random_rush:
                        continue
                    if weapon == 0:
                        world.weapon_damage[weapon][i] = 0
                    elif i in (14, 15) and not world.options.random_weakness:
                        if 3 > world.weapon_damage[weapon][i] > 0:
                            # Phase 1 takes 3 max
                            world.weapon_damage[weapon][i] = 0
                    elif 4 > world.weapon_damage[weapon][i] > 0:
                        world.weapon_damage[weapon][i] = 0

        for p_boss in world.options.plando_weakness:
            for p_weapon in world.options.plando_weakness[p_boss]:
                if not any(w for w in world.weapon_damage
                           if w != weapons_to_id[p_weapon]
                           and world.weapon_damage[w][bosses[p_boss]] > minimum_weakness_requirement[w]):
                    # we need to replace this weakness
                    weakness = world.random.choice([key for key in world.weapon_damage
                                                    if key != weapons_to_id[p_weapon]])
                    world.weapon_damage[weakness][bosses[p_boss]] = minimum_weakness_requirement[weakness]
                world.weapon_damage[weapons_to_id[p_weapon]][bosses[p_boss]] \
                    = world.options.plando_weakness[p_boss][p_weapon]

        # handle special cases
        for boss in range(17):
            for weapon in range(1, 9 if not world.options.random_rush else 13):
                if (0 < world.weapon_damage[weapon][boss] < minimum_weakness_requirement[weapon] and
                        not any(world.weapon_damage[i][boss] >= minimum_weakness_requirement[i]
                                for i in range(1, 9 if not world.options.random_rush else 13) if i != weapon)):
                    world.weapon_damage[weapon][boss] = minimum_weakness_requirement[weapon]

        if world.weapon_damage[0][world.options.starting_robot_master.value] < 1:
            world.weapon_damage[0][world.options.starting_robot_master.value] = 1

        # weakness validation, it is better to confirm a completable seed than respect plando
        boss_health = {boss: 0x1C for boss in (*range(8), 14, 15)}

        weapon_energy = {key: float(0x1C) for key in weapon_costs if key not in (9, 10) or world.options.random_rush}
        weapon_boss = {boss: {weapon: world.weapon_damage[weapon][boss] for weapon in world.weapon_damage
                              if weapon not in (9, 10) or world.options.random_rush}
                       for boss in (*range(8), 14, 15)}
        flexibility = {
            boss: (
                    sum(damage_value > 0 for damage_value in
                        weapon_damages.values())  # Amount of weapons that hit this boss
                    * sum(weapon_damages.values())  # Overall damage that those weapons do
            )
            for boss, weapon_damages in weapon_boss.items() if boss not in (14, 15)
        }
        boss_flexibility = sorted(flexibility, key=flexibility.get)  # Fast way to sort dict by value
        used_weapons: dict[int, set[int]] = {i: set() for i in (*range(8), 14, 15)}
        for boss in [*boss_flexibility, 14, 15]:
            boss_damage = weapon_boss[boss]
            weapon_weight = {weapon: (weapon_energy[weapon] / damage) if damage else 0 for weapon, damage in
                             boss_damage.items() if weapon_energy[weapon] > 0 and weapon not in (0, 9, 10)}
            while boss_health[boss] > 0:
                if boss_damage[0] > 0:
                    boss_health[boss] = 0  # if we can buster, we should buster
                    continue
                if world.options.random_rush:
                    if boss_damage[9] > 0 or boss_damage[10] > 0:
                        boss_health[boss] = 0
                        continue
                if not weapon_weight:
                    # no choice, we have to apply a buster weakness to any remaining bosses
                    for boss, health in boss_health.items():
                        if health > 0:
                            world.weapon_damage[0][boss] = 1
                    break
                highest, wp = max(zip(weapon_weight.values(), weapon_weight.keys()))
                uses = weapon_energy[wp] // weapon_costs[wp]
                if int(uses * boss_damage[wp]) >= boss_health[boss]:
                    used = ceil(boss_health[boss] / boss_damage[wp])
                    weapon_energy[wp] -= weapon_costs[wp] * used
                    boss_health[boss] = 0
                    used_weapons[boss].add(wp)
                elif highest <= 0:
                    # we are out of weapons that can actually damage the boss
                    # so find the weapon that has the most uses, and apply that as an additional weakness
                    max_uses, wp = max((weapon_energy[weapon] // weapon_costs[weapon], weapon)
                                       for weapon in weapon_weight
                                       if weapon != 0)
                    world.weapon_damage[wp][boss] = minimum_weakness_requirement[wp]
                    used = min(int(weapon_energy[wp] // weapon_costs[wp]),
                               ceil(boss_health[boss] / minimum_weakness_requirement[wp]))
                    weapon_energy[wp] -= weapon_costs[wp] * used
                    boss_health[boss] -= int(used * minimum_weakness_requirement[wp])
                    weapon_weight.pop(wp)
                    used_weapons[boss].add(wp)
                    if not weapon_weight:
                        # DANGER: we are out of weapons!!
                        if not all(health <= 0 for health in boss_health.values()):
                            # this boss still has HP, add 1 to the damage for this boss until it dies
                            # if there's still another boss remaining, we've entered a catastrophic failure state
                            while boss_health[boss] > 0:
                                world.weapon_damage[wp][boss] += 1
                                boss_health[boss] -= int(used)
                        # if the boss doesn't have HP, it'll harmlessly break out of the while
                else:
                    # drain the weapon and continue
                    boss_health[boss] -= int(uses * boss_damage[wp])
                    weapon_energy[wp] -= weapon_costs[wp] * uses
                    weapon_weight.pop(wp)
                    used_weapons[boss].add(wp)

            world.wily_3_weapons = {boss: sorted(weapons) for boss, weapons in used_weapons.items()}

    location_rules: dict[str, Rule] = {}

    for i, boss_locations in zip([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16], [
        get_boss_locations("Gravity Man Stage"),
        get_boss_locations("Wave Man Stage"),
        get_boss_locations("Stone Man Stage"),
        get_boss_locations("Gyro Man Stage"),
        get_boss_locations("Star Man Stage"),
        get_boss_locations("Charge Man Stage"),
        get_boss_locations("Napalm Man Stage"),
        get_boss_locations("Crystal Man Stage"),
        get_boss_locations("Proto Man 1 Fortress"),
        get_boss_locations("Proto Man 2 Fortress"),
        get_boss_locations("Proto Man 3 Fortress"),
        get_boss_locations("Proto Man 4 Fortress"),
        get_boss_locations("Wily Stage 1"),
        get_boss_locations("Wily Stage 2"),
        get_boss_locations("Wily Stage 3"),
        get_boss_locations("Wily Stage 4")
    ]):
        if world.weapon_damage[0][i] > 0:
            continue  # this can always be in logic
        weapons = []
        for weapon in range(1, 9 if not world.options.random_rush else 13):
            if world.weapon_damage[weapon][i] > 0:
                if world.weapon_damage[weapon][i] < minimum_weakness_requirement[weapon]:
                    continue
                weapons.append(weapons_to_name[weapon])
            if i == 14:
                if world.weapon_damage[weapon][i+1] > 0:
                    if world.weapon_damage[weapon][i+1] < minimum_weakness_requirement[weapon]:
                        continue
                    weapons.append(weapons_to_name[weapon])
        if not weapons:
            raise Exception(f"Attempted to have boss {i} with no weakness! Seed: {world.multiworld.seed}")
        for location in boss_locations:
            static_rule = STATIC_LOCATION_RULES.get(location, True_())
            if i == 14:
                # multi-phase fight, get all potential weaknesses
                # we should probably do this smarter, but this works for now
                location_rules[location] = static_rule & HasAll(*weapons)
            else:
                location_rules[location] = static_rule & HasAny(*weapons)

    for location in STATIC_LOCATION_RULES:
        if location not in location_rules:
            location_rules[location] = STATIC_LOCATION_RULES[location]

    # Handle entrance rules
    for region, info in mm5_regions.items():
        entrance = world.get_entrance(f"To {region}")
        static_rule = STATIC_ENTRANCE_RULES.get(entrance.name, True_())
        location_rule = True_()
        for location in info.required_locations:
            location_rule &= CanReachLocation(location)
        world.set_rule(entrance, static_rule & location_rule & HasAll(*info.required_items))

    # Consumable rules
    if world.options.consumables in (world.options.consumables.option_1up_etank,
                                     world.options.consumables.option_all):
        for location in STATIC_1UP_RULES:
            location_rules[location] = STATIC_1UP_RULES[location]

    if world.options.consumables in (world.options.consumables.option_weapon_health,
                                     world.options.consumables.option_all):
        for location in STATIC_ENERGY_RULES:
            location_rules[location] = STATIC_ENERGY_RULES[location]

    for location, rule in location_rules.items():
        world.set_rule(world.get_location(location), rule)