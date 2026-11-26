"""Автотесты для Ultimatum Overlay."""
import json
import os
import sys
import tempfile
import unittest
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import i18n
import paths
import preview
import prices
import screen
import watcher


class TestOverlay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = prices.Prices()

    def test_i18n_completeness(self):
        for k, pair in i18n.S.items():
            self.assertEqual(len(pair), 2, f"Key {k} must have (ru, en)")
            self.assertTrue(pair[0] and pair[1], f"Empty translation for {k}")
        for k, pair in i18n.CATS.items():
            self.assertEqual(len(pair), 2, f"Cat {k} must have (ru, en)")
            self.assertTrue(pair[0] and pair[1], f"Empty cat translation for {k}")

    def test_ensure_initial_file_modes(self):
        with tempfile.TemporaryDirectory() as app_dir, tempfile.TemporaryDirectory() as bnd_dir:
            orig_app, orig_bnd = paths.APP_DIR, paths.BUNDLE_DIR
            try:
                paths.APP_DIR = app_dir
                paths.BUNDLE_DIR = bnd_dir
                src = os.path.join(bnd_dir, "prices_cache.json")
                dst = os.path.join(app_dir, "prices_cache.json")

                with open(src, "w", encoding="utf-8") as f:
                    json.dump({"updated": 100, "chaos": {"a": 1}}, f)
                with open(dst, "w", encoding="utf-8") as f:
                    json.dump({"updated": 200, "chaos": {"a": 1, "b": 2}}, f)
                paths.ensure_initial_file("prices_cache.json", mode="json_updated")
                with open(dst, encoding="utf-8") as f:
                    self.assertEqual(json.load(f)["updated"], 200, "Newer dst must not be overwritten")

                with open(src, "w", encoding="utf-8") as f:
                    json.dump({"updated": 300, "chaos": {"a": 3}}, f)
                paths.ensure_initial_file("prices_cache.json", mode="json_updated")
                with open(dst, encoding="utf-8") as f:
                    self.assertEqual(json.load(f)["updated"], 300, "Older dst must be updated from newer src")

                lsrc = os.path.join(bnd_dir, "leagues.json")
                ldst = os.path.join(app_dir, "leagues.json")
                with open(lsrc, "w", encoding="utf-8") as f:
                    json.dump(["Old"], f)
                with open(ldst, "w", encoding="utf-8") as f:
                    json.dump(["UserLeague"], f)
                paths.ensure_initial_file("leagues.json", mode="missing")
                with open(ldst, encoding="utf-8") as f:
                    self.assertEqual(json.load(f), ["UserLeague"], "missing mode must not overwrite existing file")
            finally:
                paths.APP_DIR = orig_app
                paths.BUNDLE_DIR = orig_bnd

    def test_russian_and_english_monster_life(self):
        ru_txt = (
            "Класс предмета: Прочие предметы карт\n"
            "Редкость: Валюта\n"
            "Начертанный ультиматум\n"
            "--------\n"
            "Уровень области: 83\n"
            "--------\n"
            "На 200% больше здоровья монстров\n"
            "Требуется жертвоприношение: Божественная сфера x4\n"
            "Награда: Удваивает принесённую в жертву валюту\n"
        )
        it = prices.parse_item(ru_txt)
        self.assertEqual(it["monster_life"], 200)
        self.assertEqual(it["life_lang"], "ru")
        val, why = prices.value_of(ru_txt, self.p)
        self.assertIsNotNone(val)
        self.assertGreater(val, 400)

        en_txt = (
            "Item Class: Misc Map Items\n"
            "Rarity: Currency\n"
            "Inscribed Ultimatum\n"
            "--------\n"
            "70% more Monster Life\n"
            "Requires Sacrifice: 2x Divine Orb\n"
            "Reward: Doubles sacrificed Currency\n"
        )
        it_en = prices.parse_item(en_txt)
        self.assertEqual(it_en["monster_life"], 70)
        self.assertEqual(it_en["life_lang"], "en")

    def test_multivariant_uniques_and_unidentified(self):
        voices_3 = (
            "Item Class: Jewels\nRarity: Unique\nVoices\nLarge Cluster Jewel\n"
            "--------\nAdds 3 Small Passive Skills which grant nothing\n"
        )
        v3, why3 = prices.value_of(voices_3, self.p)
        self.assertIsNotNone(v3)
        self.assertGreater(v3, 1000)
        self.assertIn("3 passives", why3)

        voices_7_ru = (
            "Класс предмета: Самоцветы\nРедкость: Уникальный\nГолоса\nБольшой кластерный самоцвет\n"
            "--------\nДобавляет малых пассивных умений, которые ничего не дают: 7\n"
        )
        v7, why7 = prices.value_of(voices_7_ru, self.p)
        self.assertIsNotNone(v7)
        self.assertLess(v7, 50)

        ff_en = (
            "Item Class: Jewels\nRarity: Unique\nForbidden Flesh\nCobalt Jewel\n"
            "--------\nAllocates Profane Bloom if you have the matching modifier on Forbidden Flame\n"
        )
        vff, whyff = prices.value_of(ff_en, self.p)
        self.assertIsNotNone(vff)
        self.assertGreater(vff, 1000)
        self.assertIn("Profane Bloom", whyff)

        ff_ru = (
            "Класс предмета: Самоцветы\nРедкость: Уникальный\nЗапретная плоть\nКобальтовый самоцвет\n"
            "--------\nДарует умение Расцвет греха, если у вас есть аналогичное свойство на Запретном пламени\n"
        )
        vff_ru, whyff_ru = prices.value_of(ff_ru, self.p)
        self.assertIsNotNone(vff_ru)
        self.assertGreater(vff_ru, 1000)

        unid_mb = (
            "Item Class: Belts\nRarity: Unique\nHeavy Belt\n--------\nUnidentified\n"
        )
        vu, whyu = prices.value_of(unid_mb, self.p)
        self.assertIsNone(vu)
        self.assertIn("Heavy Belt", whyu)

        # Inscribed Ultimatum with generic Voices reward must be marked unreliable + range
        ult_voices = (
            "Item Class: Misc Map Items\nRarity: Currency\nInscribed Ultimatum\n"
            "--------\nRequires Sacrifice: 1x Divine Orb\nReward: Voices\n"
        )
        info = watcher.price_info(ult_voices, self.p, div_threshold=1.0)
        self.assertTrue(info["shaky"])

    def test_russian_awakened_gems_and_special_ultimatums(self):
        aw_ru = (
            "Класс предмета: Камни поддержки\nРедкость: Камень\nПробуждённый: Наставник\n"
            "--------\nУровень: 5 (макс.)\n--------\nОсквернено\n"
        )
        vaw, _ = prices.value_of(aw_ru, self.p)
        self.assertIsNotNone(vaw)
        self.assertGreater(vaw, 100)

        mirror_ult = (
            "Item Class: Misc Map Items\nRarity: Currency\nInscribed Ultimatum\n"
            "--------\n30% more Monster Life\nRequires Sacrifice: Rare Belt\nReward: Mirrors Sacrificed Rare Item\n"
        )
        info = watcher.price_info(mirror_ult, self.p, div_threshold=1.0)
        self.assertIsNone(info["error"])
        self.assertTrue(info["special"])
        self.assertEqual(info["life"], 30)

        nocost_ult = (
            "Item Class: Misc Map Items\nRarity: Currency\nInscribed Ultimatum\n"
            "--------\nRequires Sacrifice: No Cost\nReward: 2x Divine Orb\n"
        )
        vnc, _ = prices.value_of(nocost_ult, self.p)
        self.assertIsNotNone(vnc)
        self.assertGreater(vnc, 300)

    def test_10_wave_advisor_ignores_greyed_out(self):
        adv = watcher.ModAdvisor.__new__(watcher.ModAdvisor)
        e_free = {"tier": "Free", "allowed": True, "name_en": "Limited Arena", "name_ru": "Ограниченная арена"}
        e_hard = {"tier": "DO NOT TAKE", "allowed": False, "name_en": "Ruin", "name_ru": "Гибель"}
        adv.lib = [e_free, e_hard]
        adv.cfg = {"waves": 10}
        mods = [
            {"i": 0, "colored": False, "entry": e_free, "score": 0.9},   # greyed out!
            {"i": 1, "colored": True, "entry": e_hard, "score": 0.9},    # forbidden
            {"i": 2, "colored": True, "entry": None, "score": 0.2},      # unknown
        ]
        marks, waves, _ = adv.advise(mods)
        self.assertEqual(waves, 10)
        codes = {i: code for i, code, _ in marks}
        self.assertNotIn(0, codes, "Greyed-out mod must not be suggested")
        self.assertEqual(codes[1], "no")
        self.assertEqual(codes[2], "unknown")

    def test_aspect_ratio_scaling(self):
        self.assertAlmostEqual(screen.Screen.scale_and_origin(1920, 1080), 1080 / 1125)
        self.assertAlmostEqual(screen.Screen.scale_and_origin(3440, 1440), 1440 / 1125)
        # 16:10 (1920x1200) must clamp by width (1920/2000 = 0.96 < 1200/1125 = 1.0667)
        self.assertAlmostEqual(screen.Screen.scale_and_origin(1920, 1200), 1920 / 2000)

    def test_preview_zip_and_lru(self):
        with tempfile.TemporaryDirectory() as td:
            zp = os.path.join(td, "preview_images.zip")
            sample_card = os.path.join(ROOT, "preview_images", "cards", "the_doctor.png")
            if os.path.exists(sample_card):
                with zipfile.ZipFile(zp, "w", compression=zipfile.ZIP_STORED) as zf:
                    zf.write(sample_card, "cards/the_doctor.png")
                with zipfile.ZipFile(zp, "r") as zf:
                    self.assertIn("cards/the_doctor.png", zf.namelist())


if __name__ == "__main__":
    unittest.main(verbosity=2)
