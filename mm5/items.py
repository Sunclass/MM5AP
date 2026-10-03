from BaseClasses import Item
from typing import NamedTuple
from .names import (gravity_hold, water_wave, power_stone, gyro_attack, star_crash, charge_kick, napalm_bomb,
                    crystal_eye, rush_coil, rush_jet, super_arrow, beat, charge_buster,
                    gravity_man_stage, wave_man_stage, stone_man_stage, gyro_man_stage, star_man_stage,
                    charge_man_stage, napalm_man_stage, crystal_man_stage, proto_man_1_stage, proto_man_2_stage, proto_man_3_stage,
                    proto_man_4_stage, e_tank, weapon_energy, health_energy, one_up)


class ItemData(NamedTuple):
    code: int
    progression: bool
    useful: bool = False  # primarily use this for incredibly useful items of their class, like Metal Blade
    skip_balancing: bool = False


class MM5Item(Item):
    game = "Mega Man 5"


robot_master_weapon_table = {
    gravity_hold: ItemData(0x0001, True,True),
    water_wave: ItemData(0x0002, True),
    power_stone: ItemData(0x0003, True),
    gyro_attack: ItemData(0x0004, True),
    star_crash: ItemData(0x0005, True),
    charge_kick: ItemData(0x0006, True),
    napalm_bomb: ItemData(0x0007, True),
    crystal_eye: ItemData(0x0008, True),
}

stage_access_table = {
    gravity_man_stage: ItemData(0x0101, True),
    wave_man_stage: ItemData(0x0102, True),
    stone_man_stage: ItemData(0x0103, True),
    gyro_man_stage: ItemData(0x0104, True),
    star_man_stage: ItemData(0x0105, True),
    charge_man_stage: ItemData(0x0106, True),
    napalm_man_stage: ItemData(0x0107, True),
    crystal_man_stage: ItemData(0x0108, True),
    proto_man_1_stage: ItemData(0x0110, True, True),
    proto_man_2_stage: ItemData(0x0111, True, True),
    proto_man_3_stage: ItemData(0x0112, True, True),
    proto_man_4_stage: ItemData(0x0113, True, True),
}

extra_item_table = {
    rush_coil: ItemData(0x0011, True, True),
    rush_jet: ItemData(0x0012, True, True),
    super_arrow: ItemData(0x0013, True, True),
    beat: ItemData(0x0014, True, True),
    charge_buster: ItemData(0x0025, False, True),
}

filler_item_table = {
    one_up: ItemData(0x0020, False),
    weapon_energy: ItemData(0x0021, False),
    health_energy: ItemData(0x0022, False),
    e_tank: ItemData(0x0023, False, True),
}



filler_item_weights = {
    one_up: 1,
    weapon_energy: 4,
    health_energy: 1,
    e_tank: 2,
}

item_table = {
    **robot_master_weapon_table,
    **stage_access_table,
    **extra_item_table,
    **filler_item_table,
}

item_names = {
    "Weapons": {name for name in robot_master_weapon_table.keys()},
    "Stages": {name for name in stage_access_table.keys()},
    "Rush": {name for name in extra_item_table.keys() if "Rush" in name},
}

lookup_item_to_id: dict[str, int] = {item_name: data.code for item_name, data in item_table.items() if data.code}
