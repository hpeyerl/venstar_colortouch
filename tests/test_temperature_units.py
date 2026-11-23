"""Temperature-unit regressions using a mocked thermostat, never a real device."""

import copy
import logging
import unittest
from urllib.parse import parse_qs
from unittest.mock import Mock, patch

from venstarcolortouch import VenstarColorTouch


class TemperatureUnitsTests(unittest.TestCase):
    def setUp(self):
        # Fail closed if a test accidentally bypasses the mocked device API.
        network = patch(
            "requests.sessions.Session.request",
            side_effect=AssertionError("Tests must not access a real thermostat"),
        )
        network.start()
        self.addCleanup(network.stop)

    def make_client(self, info=None, model=None, api=5,
                    device_type="residential", firmware="4.08"):
        client = VenstarColorTouch("thermostat.invalid", timeout=1)
        root = {"api_ver": api, "type": device_type, "firmware": firmware}
        if model is not None:
            root["model"] = model

        values = {
            "name": "Test thermostat",
            "tempunits": 1,
            "spacetemp": 22.5,
            "heattemp": 20.5,
            "cooltemp": 25.0,
            "setpointdelta": 2.0,
            "mode": client.MODE_HEAT,
            "state": client.STATE_IDLE,
            "fan": client.FAN_AUTO,
            "fanstate": client.FANSTATE_OFF,
            "away": client.AWAY_HOME,
            "schedule": 1,
            "hum_setpoint": 40,
            "dehum_setpoint": 45,
            "hum_active": 55,
            "cooltempmin": 7.0,
            "heattempmax": 35.0,
        }
        values.update(info or {})

        def request(endpoint, data=None):
            if data is not None:
                self.assertIn(endpoint, ("/control", "/settings"))
                payload = {"success": True}
            elif endpoint == "/":
                payload = root
            elif endpoint == "/query/info":
                payload = values
            elif endpoint == "/query/alerts":
                payload = {"alerts": [{"name": "Service", "active": True}]}
            else:
                self.fail("Unexpected mocked endpoint: " + endpoint)
            return Mock(json=Mock(return_value=copy.deepcopy(payload)))

        client._request = Mock(side_effect=request)
        return client

    def test_legacy_celsius_without_warning(self):
        client = self.make_client()
        with self.assertNoLogs(level=logging.WARNING):
            self.assertTrue(client.update_info())
        self.assertEqual(client.model, "COLORTOUCH (LEGACY)")
        self.assertEqual(client.tempunits, client.TEMPUNITS_C)
        self.assertEqual(client.display_tempunits, 1)
        self.assertEqual(client.get_info("spacetemp"), 22.5)
        self.assertEqual(client.heattemp, 20.5)

    def test_legacy_fahrenheit_without_warning(self):
        client = self.make_client({
            "tempunits": 0,
            "spacetemp": 72.5,
            "heattemp": 69.0,
            "cooltemp": 77.0,
            "cooltempmin": 45.0,
            "heattempmax": 95.0,
        })
        with self.assertNoLogs(level=logging.WARNING):
            self.assertTrue(client.update_info())
        self.assertEqual(client.model, "COLORTOUCH (LEGACY)")
        self.assertEqual(client.tempunits, client.TEMPUNITS_F)
        self.assertEqual(client.display_tempunits, 0)
        self.assertEqual(client.heattemp, 69.0)

    def test_legacy_uses_reported_units_not_heat_limit_heuristic(self):
        # Deliberately disagree with the heuristic to prove this model follows
        # the reported units, rather than merely suppressing a warning.
        for units, heat_max in ((0, 35.0), (1, 95.0)):
            with self.subTest(tempunits=units, heattempmax=heat_max):
                client = self.make_client({
                    "tempunits": units, "heattempmax": heat_max,
                })
                with self.assertNoLogs(level=logging.WARNING):
                    self.assertTrue(client.update_info())
                self.assertEqual(client.tempunits, units)

    def test_repeated_legacy_updates_do_not_warn(self):
        client = self.make_client()
        with self.assertNoLogs(level=logging.WARNING):
            for _ in range(5):
                self.assertTrue(client.update_info())
        self.assertEqual(client._request.call_count, 6)  # Login, then five polls.

    def test_unknown_model_still_warns_and_infers_units(self):
        for units, heat_max, label in ((1, 35.0, "Celsius"),
                                       (0, 95.0, "Fahrenheit")):
            with self.subTest(tempunits=units):
                client = self.make_client(
                    {"tempunits": units, "heattempmax": heat_max},
                    model="UNKNOWN_TEST_MODEL",
                )
                with self.assertLogs(level=logging.WARNING) as captured:
                    self.assertTrue(client.update_info())
                self.assertEqual(client.tempunits, units)
                self.assertEqual(
                    [record.getMessage() for record in captured.records],
                    ["Unknown thermostat model UNKNOWN_TEST_MODEL, "
                     "inferring API tempunits of " + label],
                )

    def test_existing_recognized_models_still_follow_reported_units(self):
        models = (
            "COLORTOUCH", "TOUCHSCREEN", "VYG-4900-VEN", "VYG-4800-VEN",
            "VYG-3800", "VYG-3900", "T2000", "T3950",
        )
        for model in models:
            for units in (0, 1):
                with self.subTest(model=model, tempunits=units):
                    client = self.make_client(
                        {"tempunits": units}, model=model, api=7,
                        firmware="6.79",
                    )
                    with self.assertNoLogs(level=logging.WARNING):
                        self.assertTrue(client.update_info())
                    self.assertEqual(client.tempunits, units)

    def test_older_t2_t3_firmware_still_forces_celsius(self):
        for model in ("T2000", "T3950"):
            with self.subTest(model=model):
                client = self.make_client(
                    {"tempunits": 0}, model=model, api=7, firmware="5.27",
                )
                self.assertTrue(client.update_info())
                self.assertEqual(client.display_tempunits, 0)
                self.assertEqual(client.tempunits, client.TEMPUNITS_C)

    def test_t2_t3_firmware_boundary_still_uses_reported_units(self):
        for model in ("T2000", "T3950"):
            with self.subTest(model=model):
                client = self.make_client(
                    {"tempunits": 0}, model=model, api=7, firmware="5.28",
                )
                self.assertTrue(client.update_info())
                self.assertEqual(client.tempunits, client.TEMPUNITS_F)

    def test_legacy_humidity_mapping_is_unchanged(self):
        client = self.make_client()
        client.update_info()
        self.assertEqual(client.hum_setpoint, 45)
        self.assertEqual(client.dehum_setpoint, 55)
        self.assertEqual(client.hum_active, 55)

    def test_commercial_api_v5_humidity_mapping_is_unchanged(self):
        client = self.make_client(device_type="commercial")
        client.update_info()
        self.assertEqual(client.model, "COLORTOUCH")
        self.assertEqual(client.hum_setpoint, 40)
        self.assertEqual(client.dehum_setpoint, 45)
        self.assertIsNone(client.away)

    def test_humidity_setting_payloads_are_unchanged(self):
        for method, value, expected in (
            ("set_hum_setpoint", 42,
             {"tempunits": ["1"], "hum_setpoint": ["42"],
              "dehum_setpoint": ["55"]}),
            ("set_dehum_setpoint", 58,
             {"tempunits": ["1"], "hum_setpoint": ["45"],
              "dehum_setpoint": ["58"]}),
        ):
            with self.subTest(method=method):
                client = self.make_client()
                client.update_info()
                client._request.reset_mock()
                self.assertTrue(getattr(client, method)(value))
                post, refresh = client._request.call_args_list
                self.assertEqual(post.args[0], "/settings")
                self.assertEqual(parse_qs(post.args[1]), expected)
                self.assertEqual(refresh.args, ("/query/info",))

    def test_heating_and_cooling_mode_payloads_are_unchanged(self):
        client = self.make_client()
        client.update_info()
        for mode in (client.MODE_HEAT, client.MODE_COOL,
                     client.MODE_AUTO, client.MODE_OFF):
            with self.subTest(mode=mode):
                self.assertTrue(client.set_mode(mode))
                endpoint, data = client._request.call_args.args
                self.assertEqual(endpoint, "/control")
                self.assertEqual(parse_qs(data), {
                    "mode": [str(mode)],
                    "heattemp": ["20.5"],
                    "cooltemp": ["25.0"],
                })

    def test_setpoints_and_rounding_are_unchanged(self):
        client = self.make_client()
        client.update_info()
        self.assertTrue(client.set_setpoints(20.555, 25.777))
        endpoint, data = client._request.call_args.args
        self.assertEqual(endpoint, "/control")
        self.assertEqual(parse_qs(data), {
            "heattemp": ["20.55"], "cooltemp": ["25.78"],
        })

    def test_auto_setpoint_delta_validation_is_unchanged(self):
        client = self.make_client()
        client.update_info()
        client.mode = client.MODE_AUTO
        client._request.reset_mock()
        with self.assertLogs(client.log, level=logging.WARNING):
            self.assertFalse(client.set_setpoints(24.0, 25.0))
        client._request.assert_not_called()

    def test_fan_payloads_are_unchanged(self):
        client = self.make_client()
        client.update_info()
        for fan in (client.FAN_AUTO, client.FAN_ON):
            with self.subTest(fan=fan):
                self.assertTrue(client.set_fan(fan))
                endpoint, data = client._request.call_args.args
                self.assertEqual(endpoint, "/control")
                self.assertEqual(parse_qs(data), {"fan": [str(fan)]})

    def test_polling_is_read_only_and_service_alert_is_independent(self):
        client = self.make_client()
        client.update_info()
        self.assertTrue(client.update_alerts())
        self.assertEqual(client.alerts, [{"name": "Service", "active": True}])
        self.assertTrue(all(len(call.args) == 1
                            for call in client._request.call_args_list))


if __name__ == "__main__":
    unittest.main()
