import logging
import time
from enum import IntEnum
from base64 import b64encode
from typing import TYPE_CHECKING, Any
from NetUtils import ClientStatus, color, NetworkItem
from worlds._bizhawk.client import BizHawkClient

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext, BizHawkClientCommandProcessor

nes_logger = logging.getLogger("NES")
logger = logging.getLogger("Client")

    MM5_CURRENT_STAGE = 0x26
    MM5_MEGAMAN_STATE = 0x30
    MM5_MEGAMAN_SPIKE = 0x36
    MM5_LIVES = 0xBF
    MM5_E_TANKS = 0xBD
    MM5_M_TANKS = 0xBE
    MM5_ROBOT_MASTERS_DEFEATED = 0x6E
    MM5_CASTLE_STATUS = 0xAA
    MM5_HEALTH = 0xB0
    MM5_WEAPON_ENERGY = 0xB1
MM5_WEAPONS = {
    1: 6, # Gravity Hold
    2: 0, # Water Wave
    3: 5, # Power Stone
    4: 1, # Gyro Attack
    5: 8, # Star Crash
    6: 7, # Charge Kick
    7: 3, # Napalm Bomb
    8: 2, # Crystal Eye
    0x11: 9, # Rush Coil
    0x12: 0xA, # Rush Jet
    0x13: 4, # Super Arrow
    0x14: 0xB, # Beat
}
MM5_CONSUMABLES = 0x100
MM5_ENERGY_BAR = 0x02D
MM5_RECEIVED_ITEMS = 0x000
MM5_ROBOT_MASTERS_UNLOCKED = 0x001
MM5_PROTO_MAN_UNLOCKED = 0x002
MM5_RBM_STROBE = 0x004
MM5_SFX_QUEUE = 0x005
MM5_ENERGYLINK_HEALTH = 0x007
MM5_ENERGYLINK_WEAPON = 0x008
MM5_ENERGYLINK_1UP = 0x009
MM5_CHARGE_BUSTER = 0x00B
MM5_SENT_WEAPONS = 0x0B1

MM5_CONSUMABLE_TABLE: dict[int, dict[int, tuple[int, int]]] = {
    # Stage:
    #   Item: (byte offset, bit mask)
    0: {
        0x0200: (1, 3),
        0x0201: (3, 1),
        0x0202: (3, 2),
        0x0203: (4, 7),
    },
    1: {
        0x0204: (1, 0),
        0x0205: (1, 1),
        0x0206: (8, 0),
    },
    2: {
        0x0207: (2, 7),
        0x0208: (3, 7),
        0x0209: (5, 2),
        0x020A: (8, 2),
        0x020B: (9, 3),
        0x020C: (0xA, 0),
        0x020D: (0xA, 1),
        0x020E: (1, 3),
    },
    3: {
        0x020F: (1, 6),
        0x0210: (2, 1),
        0x0211: (2, 3),
        0x0212: (5, 4),
    },
    4: {
        0x0213: (4, 6),
        0x0214: (2, 2),
    },
    5: {
        0x0215: (4, 3),
    },
    6: {
        0x0216: (0, 7),
        0x0217: (1, 6),
        0x0218: (4, 7),
        0x0219: (4, 4),
    },
    7: {
        0x021A: (4, 3),
        0x021B: (5, 1),
        0x021C: (5, 6),
    },
    8: {
        0x021D: (2, 3),
        0x021E: (2, 4),
        0x021F: (4, 3),
        0x0220: (5, 1),
        0x0221: (5, 2),
    },
    9: {
        0x0222: (0, 3),
        0x0223: (4, 1),
        0x0224: (4, 6),
        0x0225: (4, 7),
        0x0226: (5, 1),
        0x0227: (6, 0),
    },
    0xA: {
        0x0228: (1, 4),
        0x0229: (4, 5),
        0x022A: (4, 6),
        0x022B: (6, 4),
    },
    0xB: {

    },
    0xC: {
        0x022C: (0, 0),
        0x022D: (0, 1),
        0x022E: (2, 0),
    },
    0xD: {
        0x022F: (0, 7),
        0x0230: (1, 0),
        0x0231: (2, 5),
        0x0232: (5, 7),
    },
    0xE: {
        0x0233: (0, 0),
        0x0234: (0, 1),
    },
    0xF: {},
}


def to_oneup_format(val: int) -> int:
    return ((val // 10) * 0x10) + val % 10


def from_oneup_format(val: int) -> int:
    return ((val // 0x10) * 10) + val % 0x10


class MM5EnergyLinkType(IntEnum):
    Life = 0
    GravityHold = 1
    WaterWave = 2
    PowerStone = 3
    GyroAttack = 4
    StarCrash = 5
    ChargeKick = 6
    NapalmBomb = 7
    CrystalEye = 8
    OneUP = 12
    RushCoil = 0x11
    RushJet = 0x12
    SuperArrow = 0x13
    Beat = 0x14


request_to_name: dict[str, str] = {
    "HP": "health",
    "GH": "Gravity Hold energy",
    "WW": "Water Wave energy",
    "PS": "Power Stone energy",
    "GA": "Gyro Attack energy",
    "SC": "Star Crash energy",
    "CK": "Charge Kick energy",
    "NB": "Napalm Bomb energy",
    "CE": "Crystal Eye energy",
    "RC": "Rush Coil energy",
    "RJ": "Rush Jet energy",
    "SA": "Super Arrow energy",
    "BE": "Beat energy",
    "1U": "lives"
}

HP_EXCHANGE_RATE = 500000000
WEAPON_EXCHANGE_RATE = 250000000
ONEUP_EXCHANGE_RATE = 14000000000

MM5_ENERGYLINK_EXCHANGE_RATES: dict[int, int] = {
    0: HP_EXCHANGE_RATE,
    1: WEAPON_EXCHANGE_RATE,
    2: ONEUP_EXCHANGE_RATE,
}


def cmd_pool(self: "BizHawkClientCommandProcessor") -> None:
    """Check the current pool of EnergyLink, and requestable refills from it."""
    if self.ctx.game != "Mega Man 5":
        logger.warning("This command can only be used when playing Mega Man 5.")
        return
    if not self.ctx.server or not self.ctx.slot:
        logger.warning("You must be connected to a server to use this command.")
        return
    energylink = self.ctx.stored_data.get(f"EnergyLink{self.ctx.team}", 0)
    health_points = energylink // HP_EXCHANGE_RATE
    weapon_points = energylink // WEAPON_EXCHANGE_RATE
    lives = energylink // ONEUP_EXCHANGE_RATE
    logger.info(f"Healing available: {health_points}\n"
                f"Weapon refill available: {weapon_points}\n"
                f"Lives available: {lives}")


def cmd_request(self: "BizHawkClientCommandProcessor", amount: str, target: str) -> None:
    """Request a refill from EnergyLink."""
    from worlds._bizhawk.context import BizHawkClientContext
    if self.ctx.game != "Mega Man 5":
        logger.warning("This command can only be used when playing Mega Man 5.")
        return
    if not self.ctx.server or not self.ctx.slot:
        logger.warning("You must be connected to a server to use this command.")
        return
    valid_targets: dict[str, MM5EnergyLinkType] = {
        "HP": MM5EnergyLinkType.Life,
        "GH": MM5EnergyLinkType.GravityHold,
        "WW": MM5EnergyLinkType.WaterWave,
        "PS": MM5EnergyLinkType.PowerStone,
        "GA": MM5EnergyLinkType.GyroAttack,
        "SC": MM5EnergyLinkType.StarCrash,
        "CK": MM5EnergyLinkType.ChargeKick,
        "NB": MM5EnergyLinkType.NapalmBomb,
        "CE": MM5EnergyLinkType.CrystalEye,
        "RC": MM5EnergyLinkType.RushCoil,
        "RJ": MM5EnergyLinkType.RushJet,
        "SA": MM5EnergyLinkType.SuperArrow,
        "BE": MM5EnergyLinkType.Beat,
        "1U": MM5EnergyLinkType.OneUP
    }
    if target.upper() not in valid_targets:
        logger.warning(f"Unrecognized target {target.upper()}. Available targets: {', '.join(valid_targets.keys())}")
        return
    ctx = self.ctx
    assert isinstance(ctx, BizHawkClientContext)
    client = ctx.client_handler
    assert isinstance(client, MegaMan5Client)
    client.refill_queue.append((valid_targets[target.upper()], int(amount)))
    logger.info(f"Restoring {amount} {request_to_name[target.upper()]}.")


def cmd_autoheal(self: "BizHawkClientCommandProcessor") -> None:
    """Enable auto heal from EnergyLink."""
    if self.ctx.game != "Mega Man 5":
        logger.warning("This command can only be used when playing Mega Man 5.")
        return
    if not self.ctx.server or not self.ctx.slot:
        logger.warning("You must be connected to a server to use this command.")
        return
    else:
        assert isinstance(self.ctx.client_handler, MegaMan5Client)
        if self.ctx.client_handler.auto_heal:
            self.ctx.client_handler.auto_heal = False
            logger.info(f"Auto healing disabled.")
        else:
            self.ctx.client_handler.auto_heal = True
            logger.info(f"Auto healing enabled.")


def get_sfx_writes(sfx: int) -> tuple[int, bytes, str]:
    return MM5_SFX_QUEUE, sfx.to_bytes(1, 'little'), "WRAM"


class MegaMan5Client(BizHawkClient):
    game = "Mega Man 5"
    system = "NES"
    patch_suffix = ".apmm5"
    item_queue: list[NetworkItem] = []
    pending_death_link: bool = False
    # default to true, as we don't want to send a deathlink until Mega Man's HP is initialized once
    sending_death_link: bool = True
    death_link: bool = False
    energy_link: bool = False
    rom: bytes | None = None
    weapon_energy: int = 0
    health_energy: int = 0
    auto_heal: bool = False
    refill_queue: list[tuple[MM5EnergyLinkType, int]] = []
    last_death_link: float = 0.0

    async def validate_rom(self, ctx: "BizHawkClientContext") -> bool:
        from worlds._bizhawk import RequestFailedError, read, get_memory_size
        from . import MM5World

        try:

            if (await get_memory_size(ctx.bizhawk_ctx, "PRG ROM")) < 0x7FFF0:
                # not the entire size, but enough to check validation
                if "pool" in ctx.command_processor.commands:
                    ctx.command_processor.commands.pop("pool")
                if "request" in ctx.command_processor.commands:
                    ctx.command_processor.commands.pop("request")
                if "autoheal" in ctx.command_processor.commands:
                    ctx.command_processor.commands.pop("autoheal")
                return False

            game_name, version = (await read(ctx.bizhawk_ctx, [(0x7EF00, 21, "PRG ROM"),
                                                               (0x7EF16, 3, "PRG ROM")]))
            if game_name[:3] != b"MM5" or version != bytes(MM5World.world_version):
                if game_name[:3] == b"MM5":
                    # I think this is an easier check than the other?
                    older_version = f"{version[0]}.{version[1]}.{version[2]}"
                    logger.warning(f"This Mega Man 5 patch was generated for an different version of the apworld. "
                                   f"Please use that version to connect instead.\n"
                                   f"Patch version: ({older_version})\n"
                                   f"Client version: ({'.'.join([str(i) for i in MM5World.world_version])})")
                if "pool" in ctx.command_processor.commands:
                    ctx.command_processor.commands.pop("pool")
                if "request" in ctx.command_processor.commands:
                    ctx.command_processor.commands.pop("request")
                if "autoheal" in ctx.command_processor.commands:
                    ctx.command_processor.commands.pop("autoheal")
                return False
        except UnicodeDecodeError:
            return False
        except RequestFailedError:
            return False  # Should verify on the next pass

        ctx.game = self.game
        self.rom = game_name
        ctx.items_handling = 0b111
        ctx.want_slot_data = False
        deathlink = (await read(ctx.bizhawk_ctx, [(0x7EF15, 1, "PRG ROM")]))[0][0]
        if deathlink & 0x01:
            self.death_link = True
            await ctx.update_death_link(self.death_link)
        if deathlink & 0x02:
            self.energy_link = True

        if self.energy_link:
            if "pool" not in ctx.command_processor.commands:
                ctx.command_processor.commands["pool"] = cmd_pool
            if "request" not in ctx.command_processor.commands:
                ctx.command_processor.commands["request"] = cmd_request
            if "autoheal" not in ctx.command_processor.commands:
                ctx.command_processor.commands["autoheal"] = cmd_autoheal

        return True

    async def set_auth(self, ctx: "BizHawkClientContext") -> None:
        if self.rom:
            ctx.auth = b64encode(self.rom).decode()

    def on_package(self, ctx: "BizHawkClientContext", cmd: str, args: dict[str, Any]) -> None:
        if cmd == "Bounced":
            if "tags" in args:
                assert ctx.slot is not None
                if "DeathLink" in args["tags"] and (args["data"]["source"] != ctx.slot_info[ctx.slot].name or
                                                    args["data"]["time"] != self.last_death_link):
                    self.on_deathlink(ctx)
        elif cmd == "Connected":
            if self.energy_link:
                ctx.set_notify(f"EnergyLink{ctx.team}")
                if ctx.ui:
                    ctx.ui.enable_energy_link()

    async def send_deathlink(self, ctx: "BizHawkClientContext") -> None:
        self.sending_death_link = True
        self.last_death_link = time.time()
        await ctx.send_death("Mega Man was defeated.")

    def on_deathlink(self, ctx: "BizHawkClientContext") -> None:
        self.last_death_link = time.time()
        self.pending_death_link = True

    async def game_watcher(self, ctx: "BizHawkClientContext") -> None:
        from worlds._bizhawk import read, write

        if ctx.server is None:
            return

        if ctx.slot is None:
            return

        # get our relevant bytes
        (robot_masters_unlocked, robot_masters_defeated, castle_status, proto_man_unlocked,
         sent_weapons, received_items, consumable_checks, e_tanks, m_tanks, lives, weapon_energy, health, state, bar_state,
         current_stage, energy_link_packet,) = await read(ctx.bizhawk_ctx, [
            (MM5_ROBOT_MASTERS_UNLOCKED, 1, "WRAM"),
            (MM5_ROBOT_MASTERS_DEFEATED, 1, "RAM"),
            (MM5_CASTLE_STATUS, 1, "RAM"),
            (MM5_PROTO_MAN_UNLOCKED, 1, "WRAM"),
            (MM5_SENT_WEAPONS, 15, "WRAM"),
            (MM5_RECEIVED_ITEMS, 1, "WRAM"),
            (MM5_CONSUMABLES, 32, "RAM"),  # Could be more but 16 definitely catches all current
            (MM5_E_TANKS, 1, "RAM"),
            (MM5_M_TANKS, 1, "RAM"),
            (MM5_LIVES, 1, "RAM"),
            (MM5_WEAPON_ENERGY, 15, "RAM"),
            (MM5_HEALTH, 1, "RAM"),
            (MM5_MEGAMAN_STATE, 1, "RAM"),
            (MM5_ENERGY_BAR, 2, "RAM"),
            (MM5_CURRENT_STAGE, 1, "RAM"),
            (MM5_ENERGYLINK_HEALTH, 3, "WRAM"),
        ])

        if bar_state[0] not in (0x00, 0x80):
            return  # Game is not initialized
            # Bit of a trick here, bar state can only be 0x00 or 0x80 (display health bar, or don't)
            # This means it can double as init guard and in-stage tracker

        if not ctx.finished_game and castle_status[0] & 0x80:
            await ctx.send_msgs([{
                "cmd": "StatusUpdate",
                "status": ClientStatus.CLIENT_GOAL
            }])
        writes = []

        # deathlink
        # only handle deathlink in bar state 0x80 (in stage)
        if bar_state[0] == 0x80:
            if self.pending_death_link:
                writes.append((MM5_MEGAMAN_SPIKE, bytes([0xF0]), "RAM"))
                self.pending_death_link = False
                self.sending_death_link = True
            if "DeathLink" in ctx.tags and ctx.last_death_link + 1 < time.time():
                if state[0] == 0x07 and not self.sending_death_link:
                    await self.send_deathlink(ctx)
                elif state[0] != 0x07:
                    self.sending_death_link = False

        weapon_energy = bytearray(weapon_energy)
        # handle receiving items
        recv_amount = received_items[0]
        if recv_amount < len(ctx.items_received):
            item = ctx.items_received[recv_amount]
            logging.info('Received %s from %s (%s) (%d/%d in list)' % (
                color(ctx.item_names.lookup_in_slot(item.item), 'red', 'bold'),
                color(ctx.player_names[item.player], 'yellow'),
                ctx.location_names.lookup_in_slot(item.location, item.player), recv_amount, len(ctx.items_received)))

            if item.item & 0x120 == 0:
                # Robot Master Weapon, or Rush
                new_weapons = item.item & 0xFF
                weapon_energy[MM5_WEAPONS[new_weapons]] |= 0x9C
                writes.append((MM5_WEAPON_ENERGY, weapon_energy, "RAM"))
                writes.append(get_sfx_writes(0x33))
            elif item.item & 0x20 == 0:
                # Robot Master Stage Access
                # Catch Cossack here
                if item.item & 0x10:
                    ptr = MM5_PROTO_MAN_UNLOCKED
                    unlocked = proto_man_unlocked
                    new = (1 << (item.item & 0xF))
                else:
                    ptr = MM5_ROBOT_MASTERS_UNLOCKED
                    unlocked = robot_masters_unlocked
                    new = (1 << ((item.item & 0xF) - 1))
                new_stages = unlocked[0] | new
                print(new_stages)
                writes.append((ptr, new_stages.to_bytes(1, 'little'), "WRAM"))
                writes.append(get_sfx_writes(0x2C))
                writes.append((MM5_RBM_STROBE, b"\x01", "WRAM"))
            elif item.item == 0x25:
                # Charge Buster
                writes.append((MM5_CHARGE_BUSTER, int.to_bytes(1, 1, "little"), "WRAM"))
                writes.append(get_sfx_writes(0x2F))
            else:
                # append to the queue, so we handle it later
                self.item_queue.append(item)
            recv_amount += 1
            writes.append((MM5_RECEIVED_ITEMS, recv_amount.to_bytes(1, 'little'), "WRAM"))

        for i in range(3):
            value = energy_link_packet[i]
            if not value:
                continue
            exchange_rate = MM5_ENERGYLINK_EXCHANGE_RATES[i]
            contribution = (value * exchange_rate) >> 1
            if contribution:
                await ctx.send_msgs([{
                    "cmd": "Set", "key": f"EnergyLink{ctx.team}", "slot": ctx.slot, "operations":
                        [{"operation": "add", "value": contribution},
                         {"operation": "max", "value": 0}]}])
            logger.info(f"Deposited {contribution / HP_EXCHANGE_RATE} health into the pool.")
            writes.append((MM5_ENERGYLINK_HEALTH + i, 0x00.to_bytes(1, "little"), "WRAM"))

        if self.weapon_energy:
            # Weapon Energy
            # We parse the whole thing to spread it as thin as possible
            current_energy = self.weapon_energy
            for i, weapon in zip(range(len(weapon_energy)), weapon_energy):
                if weapon & 0x80 and (weapon & 0x7F) < 0x1C:
                    missing = 0x1C - (weapon & 0x7F)
                    if missing > self.weapon_energy:
                        missing = self.weapon_energy
                    self.weapon_energy -= missing
                    weapon_energy[i] = weapon + missing
                    if not self.weapon_energy:
                        writes.append((MM5_WEAPON_ENERGY, weapon_energy, "RAM"))
                        break
            else:
                if current_energy != self.weapon_energy:
                    writes.append((MM5_WEAPON_ENERGY, weapon_energy, "RAM"))

        if self.health_energy or self.auto_heal:
            # Health Energy
            # We save this if the player has not taken any damage
            current_health = health[0]
            if 0 < (current_health & 0x7F) < 0x1C:
                health_diff = 0x1C - (current_health & 0x7F)
                if self.health_energy:
                    if health_diff > self.health_energy:
                        health_diff = self.health_energy
                    self.health_energy -= health_diff
                else:
                    pool = ctx.stored_data.get(f"EnergyLink{ctx.team}", 0)
                    if health_diff * HP_EXCHANGE_RATE > pool:
                        health_diff = int(pool // HP_EXCHANGE_RATE)
                    await ctx.send_msgs([{
                        "cmd": "Set", "key": f"EnergyLink{ctx.team}", "slot": ctx.slot, "operations":
                            [{"operation": "add", "value": -health_diff * HP_EXCHANGE_RATE},
                             {"operation": "max", "value": 0}]}])
                current_health += health_diff
                writes.append((MM5_HEALTH, current_health.to_bytes(1, 'little'), "RAM"))

        if self.refill_queue:
            refill_type, refill_amount = self.refill_queue.pop()
            if refill_type == MM5EnergyLinkType.Life:
                exchange_rate = HP_EXCHANGE_RATE
            elif refill_type == MM5EnergyLinkType.OneUP:
                exchange_rate = ONEUP_EXCHANGE_RATE
            else:
                exchange_rate = WEAPON_EXCHANGE_RATE
            pool = ctx.stored_data.get(f"EnergyLink{ctx.team}", 0)
            request = exchange_rate * refill_amount
            if request > pool:
                logger.warning(
                    f"Not enough energy to fulfill the request. Maximum request: {pool // exchange_rate}")
            else:
                await ctx.send_msgs([{
                    "cmd": "Set", "key": f"EnergyLink{ctx.team}", "slot": ctx.slot, "operations":
                        [{"operation": "add", "value": -request},
                         {"operation": "max", "value": 0}]}])
                if refill_type == MM5EnergyLinkType.Life:
                    refill_ptr = MM5_HEALTH
                elif refill_type == MM5EnergyLinkType.OneUP:
                    refill_ptr = MM5_LIVES
                else:
                    refill_ptr = MM5_WEAPON_ENERGY + MM5_WEAPONS[refill_type]
                current_value = (await read(ctx.bizhawk_ctx, [(refill_ptr, 1, "RAM")]))[0][0]
                if refill_type == MM5EnergyLinkType.OneUP:
                    current_value = from_oneup_format(current_value)
                new_value = min(0x9C if refill_type != MM5EnergyLinkType.OneUP else 9, current_value + refill_amount)
                writes.append((refill_ptr, new_value.to_bytes(1, "little"), "RAM"))

        if len(self.item_queue):
            item = self.item_queue.pop(0)
            idx = item.item & 0xF
            if idx == 0:
                # 1-Up
                current_lives = lives[0]
                if current_lives > 9:
                    self.item_queue.append(item)
                else:
                    current_lives += 1
                    writes.append((MM5_LIVES, current_lives.to_bytes(1, 'little'), "RAM"))
                    writes.append(get_sfx_writes(0x1F))
            elif idx == 1:
                self.weapon_energy += 0xE
                writes.append(get_sfx_writes(0x29))
            elif idx == 2:
                self.health_energy += 0xE
                writes.append(get_sfx_writes(0x29))
            elif idx == 3:
                current_e_tanks = e_tanks[0]
                if current_e_tanks > 9:
                    self.item_queue.append(item)
                else:
                    current_e_tanks += 1
                    writes.append((MM5_E_TANKS, current_e_tanks.to_bytes(1, 'little'), "RAM"))
                    writes.append(get_sfx_writes(0x1F))
            elif idx == 4:
                current_m_tanks = m_tanks[0]
                if current_m_tanks > 9:
                    self.item_queue.append(item)
                else:
                    current_m_tanks += 1
                    writes.append((MM5_M_TANKS, current_m_tanks.to_bytes(1, 'little'), "RAM"))
                    writes.append(get_sfx_writes(0x1F))
        new_checks = []

        update_castle = castle_status[0]
        for i in range(7):
            # Wily 4 does not have a boss check
            boss_id = 0x0009 + i
            if castle_status[0] & (1 << i) != 0:
                if boss_id not in ctx.checked_locations:
                    new_checks.append(boss_id)
            elif i < 4 and boss_id in ctx.checked_locations:
                # collect here
                update_castle |= (1 << i)
        if update_castle != castle_status[0]:
            writes.append((MM5_CASTLE_STATUS, update_castle.to_bytes(1, 'little'), "RAM"))

        await write(ctx.bizhawk_ctx, writes)


        # check for locations
        for i in range(8):
            flag = 1 << i
            if robot_masters_defeated[0] & flag:
                rbm_id = 0x0001 + i
                if rbm_id not in ctx.checked_locations:
                    new_checks.append(rbm_id)

        for i, ofs in MM5_WEAPONS.items():
            if sent_weapons[ofs]:
                itm_id = 0x0100 + i
                if itm_id not in ctx.checked_locations:
                    new_checks.append(itm_id)



        if bar_state[0] == 0x80:  # currently in stage
            stage_consumables = MM5_CONSUMABLE_TABLE.get(current_stage[0], [])
            for consumable in stage_consumables:
                consumable_info = stage_consumables[consumable]
                if consumable not in ctx.checked_locations:
                    is_checked = consumable_checks[consumable_info[0]] & (1 << consumable_info[1])
                    if is_checked:
                        new_checks.append(consumable)

        for new_check_id in new_checks:
            ctx.locations_checked.add(new_check_id)
            location = ctx.location_names.lookup_in_game(new_check_id)
            nes_logger.info(
                f'New Check: {location} ({len(ctx.locations_checked)}/'
                f'{len(ctx.missing_locations) + len(ctx.checked_locations)})')
            await ctx.send_msgs([{"cmd": 'LocationChecks', "locations": [new_check_id]}])
