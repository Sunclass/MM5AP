import hashlib
import os
import pkgutil
import Utils

from worlds.Files import APProcedurePatch, APTokenMixin, APTokenTypes
from typing import TYPE_CHECKING, Iterable

from .color import write_palette_shuffle
from .rules import bosses
from .options import MusicShuffle

if TYPE_CHECKING:
    from . import MM5World

MM5LCHASH = "0292adc9e38e77687f5d09718a768b45"
PROTEUSHASH = "0292adc9e38e77687f5d09718a768b45"
MM5NESHASH = "4482fbbbc77e03266b979f5028d4b51d"
MM5VCHASH = "8453ea3f3096412bff739d48aa386146"

ENERGYLINK = 0x3AA90
WILY3REQ = 0x163D0
JAMMED = 0x37E80
MTANKS = 0X3AE07

enemy_ids: dict[str, int] = {
    # these are Object IDs in the Matrixz doc
    "Pukapucker (Lower)": 0x10,
    "Pukapucker (Upper)": 0x11,
    "Kouker Q": 0x12,
    "Bombier": 0x13,
    "Space Metall": 0x15,
    "Sumatran": 0x16,
    "Mousubeil": 0x17,
    "New Shield Attacker": 0x18,
    "Rembakun": 0x19,
    "Rembakun Missiles": 0x1A,
    "Metall Cannon": 0x1B,
    "Metall K1000": 0x1D,
    "V": 0x1F,
    "Power Muscler": 0x20,
    "Apache Joe": 0x21,
    "Mizzile": 0x25,
    "Graviton": 0x28,
    "Crystal Joe": 0x2A,
    "Tatepakkan": 0x2B,
    "Foojeen": 0x31,
    "Bomb Thrown": 0x33,
    "Rider Joe": 0x35,
    "Suzy G": 0x36,
    "Asteroid": 0x39,
    "Nobita": 0x3A,
    "Bounder": 0x3B,
    "Giree": 0x3D,
    "Toss Machine": 0x3E,
    "Rolling Drill": 0x40,
    "Octoper OA": 0x44,
    "Big Pets": 0x4F,
    "Corocoro": 0x52,
    "Subeil": 0x53,
    "Tondeall": 0x54,
    "Taban": 0x56,
    "Yudon": 0x59,
    "Jet Bomb": 0x5A,
    "Rounder": 0x5C,
    "Cocco": 0x5D,
    "Irucan": 0x5F,
    "B Bitter": 0x60,
    "Yudon Missiles": 0x62,
    "Hirarian 427": 0x63,
    "Twin Cannon": 0x64,
    "Pukapelly": 0x66,
    "Camon": 0x67,
    "Lyric": 0x68,
    "Stone Man": 0x69,
    "Charge Man": 0x6B,
    "Gyro Man": 0x6E,
    "Circring Q9": 0x7C,
    "Gravity Man": 0x81,
    "Crystal Man": 0x83,
    "Wave Man": 0x86,
    "Napalm Man": 0x89,
    "Star Man": 0x8D,
    "Dark Man 2": 0x91,
    "Dark Man 3": 0x93,
    "Dark Man 1": 0x96,
    "Dark Man 4": 0x98,
    "Dachone": 0x9C,
    "Metall Swim": 0x9E,
    "Wily Press": 0xA0,
    "Wily Machine 5": 0xA5,
    "Wily Capsule II": 0xAA,
    "Rock Thrown": 0xBD,
}

enemy_weakness_ptrs: dict[int, int] = {
    0: 0x00810,
    1: 0x0E810,
    2: 0x02810,
    3: 0x0C810,
    4: 0x04810,
    5: 0x12810,
    6: 0x10810,
    7: 0x08810,
    8: 0x06810,
    9: 0x14810,
    10: 0x16810,
    11: 0x0A810,
    12: 0x18810,
}


class MM5ProcedurePatch(APProcedurePatch, APTokenMixin):
    hash = [MM5LCHASH, MM5NESHASH, MM5VCHASH]
    game = "Mega Man 5"
    patch_file_ending = ".apmm5"
    result_file_ending = ".nes"
    name: bytearray
    procedure = [
        ("apply_bsdiff4", ["mm5_basepatch.bsdiff4"]),
        ("apply_tokens", ["token_patch.bin"]),
    ]

    @classmethod
    def get_source_data(cls) -> bytes:
        return get_base_rom_bytes()

    def write_byte(self, offset: int, value: int) -> None:
        self.write_token(APTokenTypes.WRITE, offset, value.to_bytes(1, "little"))

    def write_bytes(self, offset: int, value: Iterable[int]) -> None:
        self.write_token(APTokenTypes.WRITE, offset, bytes(value))


def patch_rom(world: "MM5World", patch: MM5ProcedurePatch) -> None:
    patch.write_file("mm5_basepatch.bsdiff4", pkgutil.get_data(__name__, os.path.join("data", "mm5_basepatch.bsdiff4")))

    enemy_weaknesses: dict[str, dict[int, int]] = {}

    if world.options.strict_weakness or world.options.random_weakness or world.options.plando_weakness:
        # we need to write boss weaknesses
        for boss in bosses:
            enemy_weaknesses[boss] = {i: world.weapon_damage[i][bosses[boss]] for i in world.weapon_damage}

            if world.options.strict_weakness:
                extra_damage = 0
            else:
                extra_damage = world.weapon_damage[0][bosses[boss]]
            if not world.options.random_rush:
                enemy_weaknesses[boss][9] = extra_damage
                enemy_weaknesses[boss][10] = extra_damage
            enemy_weaknesses[boss][11] = extra_damage
            enemy_weaknesses[boss][12] = extra_damage


    if world.options.enemy_weakness:
        for enemy in enemy_ids:
            enemy_weaknesses[enemy] = {weapon: world.random.randint(-4, 4) for weapon in enemy_weakness_ptrs}
            if enemy in ["Octoper OA"] and enemy_weaknesses[enemy][0] <= 0:
                enemy_weaknesses[enemy][0] = 1

    for enemy, damage in enemy_weaknesses.items():
        for weapon in enemy_weakness_ptrs:
            if damage[weapon] < 0:
                damage[weapon] = 0
            patch.write_byte(enemy_weakness_ptrs[weapon] + enemy_ids[enemy], damage[weapon])


    patch.write_byte(WILY3REQ + 1, world.options.wily_3_requirement.value)
    patch.write_byte(ENERGYLINK + 1, world.options.energy_link.value)
    patch.write_byte(JAMMED + 1, world.options.jammed_buster.value)

# To Make sure you can have more than one M-Tank to not despawn them

    patch.write_byte(MTANKS, 0x89)
    patch.write_byte(MTANKS + 1, 0x90)

    write_palette_shuffle(world, patch)

    # music shuffle
    if world.options.music_shuffle:
        if world.options.music_shuffle == MusicShuffle.option_no_music:
            pool = [0xF0] * 24
            patch.write_byte(0x18011, 0xF0)  # intro 0B
            patch.write_byte(0x2E09D, 0xF0)  # Title Screen 49
            patch.write_byte(0x36B17, 0xF0)  # Stage Clear 11
            patch.write_byte(0x36C0E, 0xF0)  # Wily 4 Escape 4A
            patch.write_byte(0x36C34, 0xF0)  # Wily 4 Clear 15
            patch.write_byte(0x2F2AB, 0xF0)  # Protoman Castle Intro 0F
            patch.write_byte(0x2F30E, 0xF0)  # Wily Fortress Intro 10
            patch.write_byte(0x2E60B, 0xF0)  # Game Over 12
            patch.write_byte(0x2E28A, 0xF0)  # Boss Select 0E
        elif world.options.music_shuffle == MusicShuffle.option_randomized:
            pool = world.random.choices([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0xB, 0x13,
                                         0xD, 0xA, 0x49, 0xC, 0x14, 0x08, 0x09, 0x16], k=24)
        else:
            pool = [0, 1, 2, 3, 4, 5, 6, 7, 8, 1, 3, 7, 8, 9, 9, 0x14, 0x16, 0x49, 0xD, 0xA, 0x13, 0xB, 0x09, 0xC,0xB]
        world.random.shuffle(pool)
        patch.write_bytes(0x3D4E2, pool[:16])
        patch.write_byte(0x18011, pool[16])  # Intro
        patch.write_byte(0x2E09D, pool[17])  # Title Screen
        patch.write_byte(0x2E13D, pool[18])  # Stage Select
        patch.write_byte(0x2E28A, pool[19])  # Boss Select
        patch.write_byte(0x384C9, pool[20])  # Wily Capsule Boss theme
        patch.write_byte(0x1430E, pool[21])  # Regular boss theme
        patch.write_byte(0x1C0D4, pool[22])  # Credits
        patch.write_byte(0x2E63F, pool[23])  # Password
        patch.write_byte(0x2E90A, pool[24])  # Weapon Get


    from Utils import __version__
    patch.name = bytearray(f'MM5{__version__.replace(".", "")[0:3]}_{world.player}_{world.multiworld.seed:11}\0',
                           'utf8')[:21]
    patch.name.extend([0] * (21 - len(patch.name)))
    patch.write_bytes(0x3FDA0, patch.name)
    deathlink_byte = world.options.death_link.value | (world.options.energy_link.value << 1)
    patch.write_byte(0x3FDB5, deathlink_byte)

    patch.write_bytes(0x3FDB6, world.world_version)

    version_map = {
        "0": 0x18,
        "1": 0x01,
        "2": 0x02,
        "3": 0x03,
        "4": 0x04,
        "5": 0x05,
        "6": 0x06,
        "7": 0x07,
        "8": 0x08,
        "9": 0x09,
        ".": 0x24
    }

    

    patch.write_file("token_patch.bin", patch.get_token_binary())


header = b"\x4E\x45\x53\x1A\x10\x20\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00"


def read_headerless_nes_rom(rom: bytes) -> bytes:
    if rom[:4] == b"NES\x1A":
        return rom[16:]
    else:
        return rom


def get_base_rom_bytes(file_name: str = "") -> bytes:
    base_rom_bytes: bytes | None = getattr(get_base_rom_bytes, "base_rom_bytes", None)
    if not base_rom_bytes:
        file_name = get_base_rom_path(file_name)
        base_rom_bytes = read_headerless_nes_rom(bytes(open(file_name, "rb").read()))

        basemd5 = hashlib.md5()
        basemd5.update(base_rom_bytes)
        if basemd5.hexdigest() == PROTEUSHASH:
            base_rom_bytes = extract_mm5(base_rom_bytes)
            basemd5 = hashlib.md5()
            basemd5.update(base_rom_bytes)
        if basemd5.hexdigest() not in {MM5LCHASH, MM5NESHASH, MM5VCHASH}:
            print(basemd5.hexdigest())
            if basemd5.hexdigest() == "ab9ad69f29f812cb520dd49b39805491":
                raise Exception("Supplied Base Rom is a Rev 1 copy of Mega Man 5. Please contact the developer to "
                                "add support for this version.")
            raise Exception("Supplied Base Rom does not match known MD5 for US, LC, or US VC release. "
                            "Get the correct game and version, then dump it")
        headered_rom = bytearray(base_rom_bytes)
        headered_rom[0:0] = header
        setattr(get_base_rom_bytes, "base_rom_bytes", bytes(headered_rom))
        return bytes(headered_rom)
    return base_rom_bytes


def get_base_rom_path(file_name: str = "") -> str:
    from . import MM5World
    if not file_name:
        file_name = MM5World.settings.rom_file
    if not os.path.exists(file_name):
        file_name = Utils.user_path(file_name)
    return file_name


prg_offset = 0x1AF230
prg_size = 0x40000


def extract_mm5(proteus: bytes) -> bytes:
    mm5 = bytearray(proteus[prg_offset:prg_offset + prg_size])
    return bytes(mm5)
