# Written in Aug 2024, by Will Solow
# Basic code to support training a few Deep RL Agents

import sys
import tyro
from dataclasses import dataclass
from rl_algs.ppo import Args as PPO_Args
from rl_algs.dqn import Args as DQN_Args
from rl_algs.sac import Args as SAC_Args

import rl_algs.ppo as ppo
import rl_algs.dqn as dqn
import rl_algs.sac as sac

@dataclass
class Args:
    """Algorithm Parameters for PPO"""
    ppo: PPO_Args
    """Algorithm Parameters for DQN"""
    dqn: DQN_Args
    """Algorithm Parameters for SAC"""
    sac: SAC_Args

    """RL Agent Type: PPO, SAC, DQN"""
    agent_type: str = 'PPO'




if __name__ == "__main__":
    
    args = tyro.cli(Args)

    if args.agent_type == 'PPO':
        ppo.main(args.ppo)

    if args.agent_type == 'DQN':
        dqn.main(args.dqn)

    if args.agent_type == 'SAC':
        sac.main(args.sac)