from BaseClasses import Location, Region
from typing import NamedTuple
from . import names


class MM5Location(Location):
    game = "Mega Man 5"


class MM5Region(Region):
    game = "Mega Man 5"


class LocationData(NamedTuple):
    location_id: int | None
    energy: bool = False
    oneup_tank: bool = False
    eddie : bool = False


class RegionData(NamedTuple):
    locations: dict[str, LocationData]
    required_items: list[str]
    required_locations: list[str]
    parent: str = ""


mm5_regions: dict[str, RegionData] = {
    "Gravity Man Stage": RegionData({
        names.gravity_man: LocationData(0x0001),
        names.get_gravity_hold: LocationData(0x0101),
        names.gravity_man_c1: LocationData(0x0200, oneup_tank=True),
        names.gravity_man_c2: LocationData(0x0201, energy=True),
        names.gravity_man_c3: LocationData(0x0202, energy=True),
        names.gravity_man_c4: LocationData(0x0203,oneup_tank = True, energy = True),
    }, [names.gravity_man_stage], []),

    "Wave Man Stage": RegionData({
        names.wave_man: LocationData(0x0002),
        names.get_water_wave: LocationData(0x0102),
        names.wave_man_c1: LocationData(0x0204, energy=True),
        names.wave_man_c2: LocationData(0x0205, oneup_tank=True),
        names.wave_man_c3: LocationData(0x0206,oneup_tank = True, energy = True),
    }, [names.wave_man_stage], []),

    "Stone Man Stage": RegionData({
        names.stone_man: LocationData(0x0003),
        names.get_stone_bomb: LocationData(0x0103),
        names.get_rush_jet: LocationData(0x0112),
        names.stone_man_c1: LocationData(0x0207, energy=True),
        names.stone_man_c2: LocationData(0x0208, energy=True),
        names.stone_man_c3: LocationData(0x0209, oneup_tank=True),
        names.stone_man_c4: LocationData(0x020A, oneup_tank=True),
        names.stone_man_c5: LocationData(0x020B, oneup_tank=True),
        #names.stone_man_c6: LocationData(0x020C, oneup_tank = True, eddie=True),
        names.stone_man_c7: LocationData(0x020C, energy=True),
        names.stone_man_c8: LocationData(0x020D, energy=True),
        names.stone_man_c9: LocationData(0x020E,oneup_tank = True, energy = True),
    }, [names.stone_man_stage], []),

    "Gyro Man Stage": RegionData({
        names.gyro_man: LocationData(0x0004),
        names.get_gyro_shot: LocationData(0x0104),
        names.gyro_man_c1: LocationData(0x020F, energy=True),
        names.gyro_man_c2: LocationData(0x0210, energy=True),
        names.gyro_man_c3: LocationData(0x0211, oneup_tank=True),
        names.gyro_man_c4: LocationData(0x0212,oneup_tank = True, energy = True),
    }, [names.gyro_man_stage], []),

    "Star Man Stage": RegionData({
        names.star_man: LocationData(0x0005),
        names.get_star_boomerang: LocationData(0x0105),
        names.get_super_arrow: LocationData(0x0113),
        names.star_man_c1: LocationData(0x0213, energy=True),
        names.star_man_c2: LocationData(0x0214,oneup_tank = True, energy = True),
    }, [names.star_man_stage], []),

    "Charge Man Stage": RegionData({
        names.charge_man: LocationData(0x0006),
        names.get_charge_crusher: LocationData(0x0106),
        names.charge_man_c1: LocationData(0x0215,oneup_tank = True, energy = True),
    }, [names.charge_man_stage], []),

    "Napalm Man Stage": RegionData({
        names.napalm_man: LocationData(0x0007),
        names.get_napalm_missile: LocationData(0x0107),
        names.napalm_man_c1: LocationData(0x0216, energy=True),
        names.napalm_man_c2: LocationData(0x0217, oneup_tank=True),
        #names.napalm_man_c3: LocationData(0x0219, oneup_tank = True, eddie=True),
        names.napalm_man_c4: LocationData(0x0218, oneup_tank=True),
        names.napalm_man_c5: LocationData(0x0219,oneup_tank = True, energy = True),
    }, [names.napalm_man_stage], []),

    "Crystal Man Stage": RegionData({
        names.crystal_man: LocationData(0x0008),
        names.get_crystal_barrier: LocationData(0x0108),
        #names.crystal_man_c1: LocationData(0x021C, oneup_tank = True, eddie=True),
        names.crystal_man_c2: LocationData(0x021A, oneup_tank=True),
        names.crystal_man_c3: LocationData(0x021B, oneup_tank=True),
        names.crystal_man_c4: LocationData(0x021C,oneup_tank = True, energy = True),
    }, [names.crystal_man_stage], []),

    "Proto Man 1 Fortress": RegionData({
        names.proto_man_1_boss: LocationData(0x0009),
        names.proto_man_1_c1: LocationData(0x021D, energy=True),
        names.proto_man_1_c2: LocationData(0x021E, energy=True),
        names.proto_man_1_c3: LocationData(0x021F, energy=True),
        names.proto_man_1_c4: LocationData(0x0220, energy=True),
        names.proto_man_1_c5: LocationData(0x0221, energy=True),
    }, [names.proto_man_1_stage], []),

    "Proto Man 2 Fortress": RegionData({
        names.proto_man_2_boss: LocationData(0x000A),
        names.proto_man_2_c1: LocationData(0x0222, oneup_tank=True),
        names.proto_man_2_c2: LocationData(0x0223, energy=True),
        names.proto_man_2_c3: LocationData(0x0224, energy=True),
        names.proto_man_2_c4: LocationData(0x0225, oneup_tank=True),
        names.proto_man_2_c5: LocationData(0x0226, oneup_tank=True),
        names.proto_man_2_c6: LocationData(0x0227, energy=True),
    }, [names.proto_man_2_stage], []),

    "Proto Man 3 Fortress": RegionData({
        names.proto_man_3_boss: LocationData(0x000B),
        names.proto_man_3_c1: LocationData(0x0228, energy=True),
        names.proto_man_3_c2: LocationData(0x0229, oneup_tank=True),
        names.proto_man_3_c3: LocationData(0x022A, oneup_tank=True),
        names.proto_man_3_c4: LocationData(0x022B, oneup_tank=True),
    }, [names.proto_man_3_stage], []),

    "Proto Man 4 Fortress": RegionData({
        names.proto_man_4_boss: LocationData(0x000C),
    }, [names.proto_man_4_stage], []),

    "Wily Stage 1": RegionData({
        names.wily_1_boss: LocationData(0x000D),
        names.wily_1_c1: LocationData(0x022C, oneup_tank=True),
        names.wily_1_c2: LocationData(0x022D, oneup_tank=True),
        names.wily_1_c3: LocationData(0x022E, energy=True),
    }, [], [names.proto_man_1_boss, names.proto_man_2_boss,
            names.proto_man_3_boss, names.proto_man_4_boss,]),

    "Wily Stage 2": RegionData({
        names.wily_2_boss: LocationData(0x000E),
        names.wily_2_c1: LocationData(0x022F, oneup_tank=True),
        names.wily_2_c2: LocationData(0x0230, oneup_tank=True),
        names.wily_2_c3: LocationData(0x0231, energy=True),
        names.wily_2_c4: LocationData(0x0232, energy=True),
    }, [], [names.wily_1_boss], parent="Wily Stage 1"),

    "Wily Stage 3": RegionData({
        names.wily_3_boss: LocationData(0x000F),
        names.wily_3_c1: LocationData(0x0233, oneup_tank=True),
        names.wily_3_c2: LocationData(0x0234, oneup_tank=True),
                

    }, [], [names.wily_2_boss], parent="Wily Stage 2"),

    "Wily Stage 4": RegionData({
        names.wily_4_boss: LocationData(None),
    }, [], [names.wily_3_boss], parent="Wily Stage 3"),
}


def get_boss_locations(region: str) -> list[str]:
    return [location for location, data in mm5_regions[region].locations.items()
            if not data.energy and not data.oneup_tank]


def get_energy_locations(region: str) -> list[str]:
    return [location for location, data in mm5_regions[region].locations.items() if data.energy]


def get_oneup_locations(region: str) -> list[str]:
    return [location for location, data in mm5_regions[region].locations.items() if data.oneup_tank]


location_table: dict[str, int | None] = {
    location: data.location_id for region in mm5_regions.values() for location, data in region.locations.items()
}


location_groups = {
    "Get Equipped": {
        names.get_gravity_hold,
        names.get_water_wave,
        names.get_power_stone,
        names.get_gyro_attack,
        names.get_star_crash,
        names.get_charge_kick,
        names.get_napalm_bomb,
        names.get_crystal_eye,
        names.get_rush_jet,
        names.get_super_arrow,
        names.get_beat,
    },
    **{name: {location for location, data in region.locations.items() if data.location_id} for name, region in mm5_regions.items()
       if name != "Wily Stage 4"}
}

lookup_location_to_id: dict[str, int] = {location: idx for location, idx in location_table.items() if idx is not None}
