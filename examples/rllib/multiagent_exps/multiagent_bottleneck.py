"""Multi-agent Bottleneck example.

In this example, the actions are accelerations for all of the agents.
The agents all share a single model.


"""
import json
import os

import ray
import ray.rllib.agents.ppo as ppo
from ray.rllib.agents.ppo.ppo_policy_graph import PPOPolicyGraph
from ray import tune
from ray.tune.registry import register_env
from ray.tune import run_experiments

from flow.controllers import ContinuousRouter
from flow.controllers import RLController
from flow.controllers import SumoLaneChangeController
from flow.core.params import EnvParams
from flow.core.params import InFlows
from flow.core.params import InitialConfig
from flow.core.params import NetParams
from flow.core.params import SumoParams
from flow.core.traffic_lights import TrafficLights
from flow.core.vehicles import Vehicles
from flow.utils.registry import make_create_env
from flow.utils.rllib import FlowParamsEncoder

# time horizon of a single rollout
HORIZON = 2000
# number of parallel workers
N_CPUS = 50
# number of rollouts per training iteration
N_ROLLOUTS = N_CPUS

SCALING = 1
NUM_LANES = 4 * SCALING  # number of lanes in the widest highway
DISABLE_TB = True
DISABLE_RAMP_METER = True
AV_FRAC = 0.10
os.environ['MULTIAGENT'] = 'True'

vehicles = Vehicles()
vehicles.add(
    veh_id='human',
    speed_mode='all_checks',
    lane_change_controller=(SumoLaneChangeController, {}),
    routing_controller=(ContinuousRouter, {}),
    lane_change_mode=0,
    num_vehicles=1 * SCALING)
vehicles.add(
    veh_id='followerstopper',
    acceleration_controller=(RLController, {}),
    lane_change_controller=(SumoLaneChangeController, {}),
    routing_controller=(ContinuousRouter, {}),
    speed_mode=9,
    lane_change_mode=0,
    num_vehicles=1 * SCALING)

controlled_segments = [('1', 1, False), ('2', 2, True), ('3', 2, True),
                       ('4', 2, True), ('5', 1, False)]
num_observed_segments = [('1', 1), ('2', 3), ('3', 3), ('4', 3), ('5', 1)]
additional_env_params = {
    'target_velocity': 40,
    'disable_tb': True,
    'disable_ramp_metering': True,
    'controlled_segments': controlled_segments,
    'symmetric': False,
    'observed_segments': num_observed_segments,
    'reset_inflow': False,
    'lane_change_duration': 5,
    'max_accel': 3,
    'max_decel': 3,
    'inflow_range': [1000, 2000],
    'communicate': True
}

# flow rate
flow_rate = 1900 * SCALING

# percentage of flow coming out of each lane
inflow = InFlows()
inflow.add(
    veh_type='human',
    edge='1',
    vehs_per_hour=flow_rate * (1 - AV_FRAC),
    departLane='random',
    departSpeed=10)
inflow.add(
    veh_type='followerstopper',
    edge='1',
    vehs_per_hour=flow_rate * AV_FRAC,
    departLane='random',
    departSpeed=10)

traffic_lights = TrafficLights()
if not DISABLE_TB:
    traffic_lights.add(node_id='2')
if not DISABLE_RAMP_METER:
    traffic_lights.add(node_id='3')

additional_net_params = {'scaling': SCALING}
net_params = NetParams(
    inflows=inflow,
    no_internal_links=False,
    additional_params=additional_net_params)

flow_params = dict(
    # name of the experiment
    exp_tag='MultiBottleneckCommunicate',

    # name of the flow environment the experiment is running on
    env_name='MultiBottleneckEnv',

    # name of the scenario class the experiment is running on
    scenario='BottleneckScenario',

    # name of the generator used to create/modify network configuration files
    generator='BottleneckGenerator',

    # sumo-related parameters (see flow.core.params.SumoParams)
    sumo=SumoParams(
        sim_step=0.5,
        render=False,
        print_warnings=False,
        restart_instance=True,
    ),

    # environment related parameters (see flow.core.params.EnvParams)
    env=EnvParams(
        warmup_steps=40,
        sims_per_step=1,
        horizon=HORIZON,
        additional_params=additional_env_params,
    ),

    # network-related parameters (see flow.core.params.NetParams and the
    # scenario's documentation or ADDITIONAL_NET_PARAMS component)
    net=NetParams(
        inflows=inflow,
        no_internal_links=False,
        additional_params=additional_net_params,
    ),

    # vehicles to be placed in the network at the start of a rollout (see
    # flow.core.vehicles.Vehicles)
    veh=vehicles,

    # parameters specifying the positioning of vehicles upon initialization/
    # reset (see flow.core.params.InitialConfig)
    initial=InitialConfig(
        spacing='uniform',
        min_gap=5,
        lanes_distribution=float('inf'),
        edges_distribution=['2', '3', '4', '5'],
    ),

    # traffic lights to be introduced to specific nodes (see
    # flow.core.traffic_lights.TrafficLights)
    tls=traffic_lights,
)

if __name__ == '__main__':
    ray.init()

    config = ppo.DEFAULT_CONFIG.copy()
    config['num_workers'] = N_CPUS
    config['train_batch_size'] = HORIZON * N_ROLLOUTS
    config['simple_optimizer'] = True
    config['gamma'] = 0.999  # discount rate
    config['model'].update({'fcnet_hiddens': [32, 32]})
    config['model']['use_lstm'] = True
    config['use_gae'] = True
    config['lambda'] = 0.97
    config['kl_target'] = 0.02
    config['vf_clip_param'] = 10000
    config['lr'] = tune.grid_search([1e-3, 1e-4, 1e-5, 1e-6])
    config['vf_loss_coeff'] = tune.grid_search([1, 10, 100])
    config['num_sgd_iter'] = tune.grid_search([10, 30])
    config['horizon'] = HORIZON
    config['observation_filter'] = 'NoFilter'
    config['model']['squash_to_range'] = True
    config['model']['max_seq_len'] = 10
    # Size of the LSTM cell
    config['model']['lstm_cell_size'] = 32

    # save the flow params for replay
    flow_json = json.dumps(
        flow_params, cls=FlowParamsEncoder, sort_keys=True, indent=4)
    config['env_config']['flow_params'] = flow_json

    create_env, env_name = make_create_env(params=flow_params, version=0)

    # Register as rllib env
    register_env(env_name, create_env)

    test_env = create_env()
    obs_space = test_env.observation_space
    act_space = test_env.action_space

    def gen_policy():
        return (PPOPolicyGraph, obs_space, act_space, {})

    # Setup PG with an ensemble of `num_policies` different policy graphs
    policy_graphs = {'av': gen_policy()}

    def policy_mapping_fn(agent_id):
        return 'av'

    policy_ids = list(policy_graphs.keys())
    config.update({
        'multiagent': {
            'policy_graphs': policy_graphs,
            'policy_mapping_fn': tune.function(policy_mapping_fn),
            'policies_to_train': ['av']
        }
    })

    run_experiments({
        flow_params['exp_tag']: {
            'run': 'PPO',
            'env': env_name,
            'checkpoint_freq': 50,
            'stop': {
                'training_iteration': 400
            },
            'config': config,
            'upload_dir': 's3://<BUCKET NAME>'
        },
    })
