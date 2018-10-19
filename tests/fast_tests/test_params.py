import unittest
from flow.core.params import SumoLaneChangeParams, SumoCarFollowingParams, \
    Vehicles
from flow.controllers import IDMController, SumoCarFollowingController
from tests.setup_scripts import ring_road_exp_setup
import os

os.environ["TEST_FLAG"] = "True"


class TestSumoCarFollowingParams(unittest.TestCase):
    """Tests flow.core.params.SumoCarFollowingParams"""

    def test_params(self):
        """Tests that the various parameters lead to correct assignments in the
        controller_params attribute of the class."""
        # start a SumoCarFollowingParams with some attributes
        cfm_params = SumoCarFollowingParams(
            accel=1.0,
            decel=1.5,
            sigma=0.5,
            tau=0.5,
            min_gap=1.0,
            max_speed=30,
            speed_factor=1.0,
            speed_dev=0.1,
            impatience=0.5,
            car_follow_model="IDM")

        # ensure that the attributes match their correct element in the
        # "controller_params" dict
        self.assertEqual(cfm_params.controller_params["accel"], 1)
        self.assertEqual(cfm_params.controller_params["decel"], 1.5)
        self.assertEqual(cfm_params.controller_params["sigma"], 0.5)
        self.assertEqual(cfm_params.controller_params["tau"], 0.5)
        self.assertEqual(cfm_params.controller_params["minGap"], 1)
        self.assertEqual(cfm_params.controller_params["maxSpeed"], 30)
        self.assertEqual(cfm_params.controller_params["speedFactor"], 1)
        self.assertEqual(cfm_params.controller_params["speedDev"], 0.1)
        self.assertEqual(cfm_params.controller_params["impatience"], 0.5)
        self.assertEqual(cfm_params.controller_params["carFollowModel"], "IDM")

    def test_deprecated(self):
        """Ensures that deprecated forms of the attribute still return proper
        values to the correct attributes"""
        # start a SumoCarFollowingParams with some attributes, using the
        # deprecated attributes
        cfm_params = SumoCarFollowingParams(
            accel=1.0,
            decel=1.5,
            sigma=0.5,
            tau=0.5,
            minGap=1.0,
            maxSpeed=30,
            speedFactor=1.0,
            speedDev=0.1,
            impatience=0.5,
            carFollowModel="IDM")

        # ensure that the attributes match their correct element in the
        # "controller_params" dict
        self.assertEqual(cfm_params.controller_params["accel"], 1)
        self.assertEqual(cfm_params.controller_params["decel"], 1.5)
        self.assertEqual(cfm_params.controller_params["sigma"], 0.5)
        self.assertEqual(cfm_params.controller_params["tau"], 0.5)
        self.assertEqual(cfm_params.controller_params["minGap"], 1)
        self.assertEqual(cfm_params.controller_params["maxSpeed"], 30)
        self.assertEqual(cfm_params.controller_params["speedFactor"], 1)
        self.assertEqual(cfm_params.controller_params["speedDev"], 0.1)
        self.assertEqual(cfm_params.controller_params["impatience"], 0.5)
        self.assertEqual(cfm_params.controller_params["carFollowModel"], "IDM")


class TestSumoLaneChangeParams(unittest.TestCase):
    """Tests flow.core.params.SumoLaneChangeParams"""

    def test_lc_params(self):
        """Test basic usage of the SumoLaneChangeParams object. Ensures that
        the controller_params attribute contains different elements depending
        on whether LC2103 or SL2015 is being used as the model."""
        # test for LC2013
        lc_params_1 = SumoLaneChangeParams(model="LC2013")
        attributes_1 = list(lc_params_1.controller_params.keys())
        # TODO: modify with all elements once the fix is added to sumo
        expected_attributes_1 = [
            "laneChangeModel", "lcStrategic", "lcCooperative", "lcSpeedGain",
            "lcKeepRight"
        ]
        self.assertCountEqual(attributes_1, expected_attributes_1)

        # test for SL2015
        lc_params_2 = SumoLaneChangeParams(model="SL2015")
        attributes_2 = list(lc_params_2.controller_params.keys())
        expected_attributes_2 = \
            ["laneChangeModel", "lcStrategic", "lcCooperative", "lcSpeedGain",
             "lcKeepRight", "lcLookaheadLeft", "lcSpeedGainRight", "lcSublane",
             "lcPushy", "lcPushyGap", "lcAssertive", "lcImpatience",
             "lcTimeToImpatience", "lcAccelLat"]
        self.assertCountEqual(attributes_2, expected_attributes_2)

    def test_wrong_model(self):
        """Tests that a wrongly specified model defaults the sumo lane change
        model to LC2013."""
        # input a wrong lane change model
        lc_params = SumoLaneChangeParams(model="foo")

        # ensure that the model is set to "LC2013"
        self.assertEqual(lc_params.controller_params["laneChangeModel"],
                         "LC2013")

        # ensure that the correct parameters are currently present
        attributes = list(lc_params.controller_params.keys())
        expected_attributes = [
            "laneChangeModel", "lcStrategic", "lcCooperative", "lcSpeedGain",
            "lcKeepRight"
        ]
        self.assertCountEqual(attributes, expected_attributes)

    def test_deprecated(self):
        """Ensures that deprecated forms of the attribute still return proper
        values to the correct attributes"""
        # start a SumoLaneChangeParams with some attributes
        lc_params = SumoLaneChangeParams(
            model="SL2015",
            lcStrategic=1.0,
            lcCooperative=1.0,
            lcSpeedGain=1.0,
            lcKeepRight=1.0,
            lcLookaheadLeft=2.0,
            lcSpeedGainRight=1.0,
            lcSublane=1.0,
            lcPushy=0,
            lcPushyGap=0.6,
            lcAssertive=1,
            lcImpatience=0,
            lcTimeToImpatience=float("inf"))

        # ensure that the attributes match their correct element in the
        # "controller_params" dict
        self.assertAlmostEqual(
            float(lc_params.controller_params["lcStrategic"]), 1)
        self.assertAlmostEqual(
            float(lc_params.controller_params["lcCooperative"]), 1)
        self.assertAlmostEqual(
            float(lc_params.controller_params["lcSpeedGain"]), 1)
        self.assertAlmostEqual(
            float(lc_params.controller_params["lcKeepRight"]), 1)
        self.assertAlmostEqual(
            float(lc_params.controller_params["lcSublane"]), 1)
        self.assertAlmostEqual(
            float(lc_params.controller_params["lcPushy"]), 0)
        self.assertAlmostEqual(
            float(lc_params.controller_params["lcPushyGap"]), 0.6)
        self.assertAlmostEqual(
            float(lc_params.controller_params["lcAssertive"]), 1)
        self.assertAlmostEqual(
            float(lc_params.controller_params["lcImpatience"]), 0)


class TestVehiclesClass(unittest.TestCase):
    """
    Tests various functions in the vehicles class
    """

    def test_speed_lane_change_modes(self):
        """
        Check to make sure vehicle class correctly specifies lane change and
        speed modes
        """
        vehicles = Vehicles()
        vehicles.add(
            "typeA",
            acceleration_controller=(IDMController, {}),
            sumo_car_following_params=SumoCarFollowingParams(
                speed_mode='no_collide',
            ),
            sumo_lc_params=SumoLaneChangeParams(
                lane_change_mode="no_lat_collide",
            ))
        env, _ = ring_road_exp_setup(vehicles=vehicles)

        self.assertEqual(env.k.vehicle.get_speed_mode("typeA_0"), 1)
        self.assertEqual(env.k.vehicle.get_lane_change_mode("typeA_0"), 256)

        env.terminate()

        vehicles.add(
            "typeB",
            acceleration_controller=(IDMController, {}),
            sumo_car_following_params=SumoCarFollowingParams(
                speed_mode='aggressive',
            ),
            sumo_lc_params=SumoLaneChangeParams(
                lane_change_mode="strategic",
            ))
        env, _ = ring_road_exp_setup(vehicles=vehicles)

        self.assertEqual(env.k.vehicle.get_speed_mode("typeB_0"), 0)
        self.assertEqual(env.k.vehicle.get_lane_change_mode("typeB_0"), 853)

        env.terminate()

        vehicles.add(
            "typeC",
            acceleration_controller=(IDMController, {}),
            sumo_car_following_params=SumoCarFollowingParams(
                speed_mode=31,
            ),
            sumo_lc_params=SumoLaneChangeParams(
                lane_change_mode=277,
            ))
        env, _ = ring_road_exp_setup(vehicles=vehicles)

        self.assertEqual(env.k.vehicle.get_speed_mode("typeC_0"), 31)
        self.assertEqual(env.k.vehicle.get_lane_change_mode("typeC_0"), 277)

        env.terminate()

    def test_controlled_id_params(self):
        """
        Ensure that, if a vehicle is not a sumo vehicle, then minGap is set to
        zero so that all headway values are correct.
        """
        # check that, if the vehicle is not a SumoCarFollowingController
        # vehicle, then its minGap is equal to 0
        vehicles = Vehicles()
        vehicles.add(
            "typeA",
            acceleration_controller=(IDMController, {}),
            sumo_car_following_params=SumoCarFollowingParams(
                speed_mode="no_collide",
            ),
            sumo_lc_params=SumoLaneChangeParams(
                lane_change_mode="no_lat_collide",
            ))
        self.assertEqual(vehicles.types[0]["type_params"]["minGap"], 0)

        # check that, if the vehicle is a SumoCarFollowingController vehicle,
        # then its minGap, accel, and decel are set to default
        vehicles = Vehicles()
        vehicles.add(
            "typeA",
            acceleration_controller=(SumoCarFollowingController, {}),
            sumo_car_following_params=SumoCarFollowingParams(
                speed_mode="no_collide",
            ),
            sumo_lc_params=SumoLaneChangeParams(
                lane_change_mode="no_lat_collide",
            ))
        default_mingap = SumoCarFollowingParams().controller_params["minGap"]
        self.assertEqual(vehicles.types[0]["type_params"]["minGap"],
                         default_mingap)


if __name__ == '__main__':
    unittest.main()
