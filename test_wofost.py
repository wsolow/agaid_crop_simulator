"""File for testing the installation and setup of the WOFOST Gym Environment
with a few simple plots for output 

Written by: Will Solow, 2024
"""

import gymnasium as gym
import numpy as np
import pandas as pd
import tyro
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import sys
from datetime import datetime

import wofost_gym
import wofost_gym.policies as policies
from wofost_gym.envs.wofost_base import NPK_Env, Plant_NPK_Env, Harvest_NPK_Env
from utils import Args
import utils
import yaml

import visualize_data

if __name__ == "__main__":
    plot = False
    plot2 = False
    graph = False
    plot_dates = True
    args = tyro.cli(Args)

    env_id, env_kwargs = utils.get_gym_args(args)
    if graph:
        env_kwargs["args"].output_vars = wofost_gym.args.GRAPH_OUTPUT_VARS

    # Make the gym environment with wrappers
    env = gym.make(env_id, **env_kwargs)
    env = wofost_gym.wrappers.RewardFertilizationThresholdWrapper(env, max_n=5)
    env = wofost_gym.wrappers.NPKDictActionWrapper(env)
    env = wofost_gym.wrappers.NPKDictObservationWrapper(env)
    
    # Set default policy for use
    if isinstance(env.unwrapped, Harvest_NPK_Env):
        policy = policies.No_Action_Harvest(env)
    elif isinstance(env.unwrapped, Plant_NPK_Env):
        policy = policies.No_Action_Plant(env)
    else:
        policy = policies.Interval_N(env, amount=0, interval=7)
        #policy = policies.Below_N(env, threshold=10, amount=1)

    obs_arr = []
    obs, info = env.reset()
    term = False
    #trunc = False
    obs_arr = []
    reward_arr = []

    # Run simulation and store data
    k = 0
    while not term:
        action = policy(obs)
        next_obs, rewards, term, trunc, info = env.step(action)
        obs_arr.append(obs)
        reward_arr.append(rewards)
        obs = next_obs
        k+=1
        if term or trunc:
            obs, info = env.reset()
            break
    all_obs = np.array([list(d.values()) for d in obs_arr])

    df = pd.DataFrame(data=np.array(all_obs), columns=env.get_output_vars())
    df.to_csv("data/below_n.csv")


    all_vars = args.npk_args.output_vars + args.npk_args.forecast_length * args.npk_args.weather_vars
    print(f'SUCCESS in {args.env_id}')
    
    if plot:
        # Plot Data
        plt.figure(0)
        plt.title('Cumulative Rewards')
        plt.xlabel('Days')
        plt.plot(np.cumsum(reward_arr))

        plt.figure()
        for i in range(len(all_vars)):
            plt.figure(i+1)
            plt.title(all_vars[i])
            plt.plot(all_obs[ :, i])
            plt.xlim(0-10, all_obs.shape[0]+10) 
            plt.xlabel('Days')
        plt.show()
    
    if graph:
        for i in range(len(all_vars)):
            plt.figure(i)
            plt.title(all_vars[i])
            plt.plot(all_obs[ :, i])
            plt.xlim(0-10, all_obs.shape[0]+10) 
            plt.xlabel('Days')
            plt.savefig(f'figs/{env_kwargs["args"].ag_args.crop_name}_{all_vars[i]}')
            plt.close()
        
    if plot2: 

        visualize_data.plot_season(args, [df])

    DOP = np.unique(df["DOP"])
    DOB = np.unique(df["DOB"])
    DOL = np.unique(df["DOL"])
    DOV = np.unique(df["DOV"])
    DOR = np.unique(df["DOR"])
    DOC = np.unique(df["DOC"])
    DON = np.unique(df["DON"])

    DOP = DOP[~np.isnan(DOP)]
    DOB = DOB[~np.isnan(DOB)]
    DOL = DOL[~np.isnan(DOL)]
    DOV = DOV[~np.isnan(DOV)]
    DOR = DOR[~np.isnan(DOR)]
    DOC = DOC[~np.isnan(DOC)]
    DON = DON[~np.isnan(DON)]

    if plot_dates:
        fig,ax = plt.subplots(1,1,figsize=(10,6))
        ax.set_title("Grape Phenology as Development Stage")
        ax.plot(df["DVS"], color='k', label='Development Stage')

        ymin,ymax = ax.get_ylim()
        ax.set_ylim(ymin, ymax)

        CB = ['#377eb8', '#ff7f00', '#4daf4a',
                  '#f781bf', '#a65628', '#984ea3',
                  '#999999', '#e41a1c', '#dede00']
        
        for dob in DOB:
            delta = (datetime.strptime(str(int(dob)), '%Y%m%d') - datetime.strptime(str(int(DOP[0])), '%Y%m%d')).days
            ax.vlines(delta, ymin, df["DVS"][delta], linestyle='dashed', color=CB[0], label='Bud Break')
            ax.text(delta, (ymin+df["DVS"][delta])/2, f"{datetime.strptime(str(int(dob)), '%Y%m%d'):%m-%d }", rotation=30)
        for dol in DOL:
            delta = (datetime.strptime(str(int(dol)), '%Y%m%d') - datetime.strptime(str(int(DOP[0])), '%Y%m%d')).days
            ax.vlines(delta, ymin, df["DVS"][delta], linestyle='dashed', color=CB[1], label='Flowering')
            ax.text(delta, (ymin+df["DVS"][delta])/2, f"{datetime.strptime(str(int(dol)), '%Y%m%d'):%m-%d }", rotation=30)
        for dov in DOV:
            delta = (datetime.strptime(str(int(dov)), '%Y%m%d') - datetime.strptime(str(int(DOP[0])), '%Y%m%d')).days
            ax.vlines(delta, ymin, df["DVS"][delta], linestyle='dashed', color=CB[2], label='Verasion')
            ax.text(delta, (ymin+df["DVS"][delta])/2, f"{datetime.strptime(str(int(dov)), '%Y%m%d'):%m-%d }", rotation=30)
        for dor in DOR:
            delta = (datetime.strptime(str(int(dor)), '%Y%m%d') - datetime.strptime(str(int(DOP[0])), '%Y%m%d')).days
            ax.vlines(delta, ymin, df["DVS"][delta], linestyle='dashed', color=CB[3], label='Ripe')
            ax.text(delta, (ymin+df["DVS"][delta])/2, f"{datetime.strptime(str(int(dor)), '%Y%m%d'):%m-%d }", rotation=30)
        for doc in DOC:
            delta = (datetime.strptime(str(int(doc)), '%Y%m%d') - datetime.strptime(str(int(DOP[0])), '%Y%m%d')).days
            ax.vlines(delta, ymin, df["DVS"][delta], linestyle='dashed', color=CB[4], label='Endodormancy')
            ax.text(delta, (ymin+df["DVS"][delta])/2, f"{datetime.strptime(str(int(doc)), '%Y%m%d'):%m-%d }", rotation=30)
        for don in DON:
            delta = (datetime.strptime(str(int(don)), '%Y%m%d') - datetime.strptime(str(int(DOP[0])), '%Y%m%d')).days
            ax.vlines(delta, ymin, df["DVS"][delta], linestyle='dashed', color=CB[5], label='Ecodormancy')
            ax.text(delta, (ymin+df["DVS"][delta])/2, f"{datetime.strptime(str(int(don)), '%Y%m%d'):%m-%d }", rotation=30)
        
        cb0 = patches.Patch(color=CB[0], label='Bud Break')
        cb1 = patches.Patch(color=CB[1], label='Flowering')
        cb2 = patches.Patch(color=CB[2], label='Verasion')
        cb3 = patches.Patch(color=CB[3], label='Ripe')
        cb4 = patches.Patch(color=CB[4], label='Endodormancy')
        cb5 = patches.Patch(color=CB[5], label='Ecodormancy')
        dvs = patches.Patch(color='k', label="Development Stage")

        ax.set_xlabel('Days Elapsed')
        ax.set_ylabel('Development Stage (No Units)')
        plt.legend(handles=[dvs, cb0, cb1, cb2, cb3, cb4, cb5])
        plt.show()




