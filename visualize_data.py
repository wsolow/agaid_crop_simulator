# Written Sept 2024, by Will Solow
# Code to support data generation given a single policy and single farm
# Allows the user to specify a set of years and locations (thus historical weather data)
# And a specific farm from which to gather data from 

import gymnasium as gym
import numpy as np
import wofost_gym
import matplotlib.pyplot as plt
import pandas as pd
import torch
import sys
import yaml

from utils import NPK_Args
import tyro
import utils
import policies

np.set_printoptions(precision=3)
def norm(x):
    return (x-np.nanmin(x))/(np.nanmax(x)-np.nanmin(x))

def plot_average_farms(args, filenames):
    fname = f'env_config/units.yaml'
    with open(fname) as fp:
        try:
            r = yaml.safe_load(fp)
        except yaml.YAMLError as e:
            msg = "Failed parsing agromanagement file %s: %s" % (fname, e)
            print(msg)
            

    farm_avg = []
    farm_std = []
    for f in filenames:
        df = pd.read_csv(f'{args.save_folder}{f}.csv', index_col=0)
        np_arr = df.to_numpy()

        sim_starts = np.argwhere(np_arr[:,-2]==1).flatten().astype('int32')

        arr = []
        # Get all the individual runs within the data file 
        for i in range(len(sim_starts)):
            if i+1 >= len(sim_starts):
                arr.append(np_arr[sim_starts[i]:])
            else:
                arr.append(np_arr[sim_starts[i]:sim_starts[i+1]])

        # Clip the length of the simulation to the minimum value 
        # Deals with data from leap years 
        clipped_length = np.min([arr[i].shape[0] for i in range(len(arr))])

        clipped_arr = np.array([arr[i][:clipped_length] for i in range(len(arr))])[:,:,4:].astype('float32')

        #print(np.array(clipped_arr[:,:,4:]).dtype)
        farm_avg.append(np.mean(clipped_arr, axis=0))
        farm_std.append(np.std(clipped_arr, axis=0))
        
    farm_avg = np.array(farm_avg)
    farm_std = np.array(farm_std)
    plt.figure(0)
    plt.title('Average Rewards')

    for i in range(len(farm_avg)):
        plt.plot(farm_avg[i,:,-1],label=filenames[i])
        plt.fill_between(np.arange(clipped_length),farm_avg[i,:,-1]-farm_std[i,:,-1],farm_avg[i,:,-1]+farm_std[i,:,-1], alpha=.5, linestyle='solid')
        plt.xlabel('Days')
    plt.legend()
    plt.show()


    all_vars = args.output_vars + args.weather_vars
    for j in range(len(all_vars)):
        plt.figure(j+1)
        plt.title(all_vars[j])
        plt.xlabel('Days')
        plt.ylabel(r[all_vars[j]])
        for i in range(len(farm_avg)):
            plt.plot(farm_avg[i,:,j],label=filenames[i])
            plt.fill_between(np.arange(clipped_length),farm_avg[i,:,j]-farm_std[i,:,j],farm_avg[i,:,j]+farm_std[i,:,j], alpha=.5, linestyle='solid')
        plt.legend()
        plt.show()

def plot_matrix(args, data_files, agents):
    ag_avg = []
    ag_std = []
    for j in range(len(agents)):
        farm_avg = []
        farm_std = []
        for i in range(len(data_files)):
            print(f'[{j},{i}], {agents[j]}, {data_files[i]}' )
            df = pd.read_csv(f'{args.save_folder}tot_growth_ppo_{agents[j]}_{data_files[i]}.csv', index_col=0)
            np_arr = df.to_numpy()

            sim_starts = np.argwhere(np_arr[:,-2]==1).flatten().astype('int32')

            arr = []
            # Get all the individual runs within the data file 
            for k in range(len(sim_starts)):
                if k+1 >= len(sim_starts):
                    arr.append(np_arr[sim_starts[k]:])
                else:
                    arr.append(np_arr[sim_starts[k]:sim_starts[k+1]])

            # Clip the length of the simulation to the minimum value 
            # Deals with data from leap years 
            clipped_length = np.min([arr[k].shape[0] for k in range(len(arr))])

            clipped_arr = np.array([arr[k][:clipped_length] for k in range(len(arr))])[:,:,4:].astype('float32')

            farm_avg.append(np.mean(clipped_arr, axis=0))
            farm_std.append(np.std(clipped_arr, axis=0))

        ag_avg.append(farm_avg)
        ag_std.append(farm_std)

    ag_avg = np.array(ag_avg)
    ag_std = np.array(ag_std)

    avg_cum_reward = np.cumsum(ag_avg[:,:,:,-1],axis=2)[:,:,-1]
    plt.figure(0)
    plt.imshow(norm(avg_cum_reward))
    yticks = [''+a for a in agents]
    xticks = [f.replace('farm_','') for f in data_files]
    plt.ylabel('Agent')
    plt.xlabel('Farm')
    plt.yticks(np.arange(len(agents)),labels=yticks, rotation=30)
    plt.xticks(np.arange(len(data_files)),labels=xticks, rotation=-30)
    plt.title('Normalized Returns across Agents and Farms')
    plt.colorbar()

    plt.show()
        
if __name__ == "__main__":

    args = tyro.cli(NPK_Args)

    env_kwargs = {'args':args}
    env_id = args.env_id

    # Make the gym environment - should be as a SyncVectorEnv to support
    # Easy loading from PPO/SAC/DQN agentzs

    data_files = ['farm_default', 'farm_CO2_100', 'farm_CO2_450', 'farm_KSUB_.7', \
                  'farm_RDMSOL_50', 'farm_RDMSOL_200', 'farm_SMLIM_.4', 'farm_SSI_2']
    
    agents = ['default', 'ksub_.7', 'co2_100', 'co2_450', 'rdmsol_50', 'rdmsol_200', 'ssi_2', 'smlim_.4']

    #plot_average_farms(args, data_files)
    plot_matrix(args, data_files, agents)

    sys.exit(0)
    plt.figure(0)
    plt.title('Cumulative Rewards')
    for j in range(len(arr)):
        curr_arr = [arr[j][k][-1] for k in range(len(arr[j]))]
        plt.plot(np.cumsum(curr_arr))
    plt.show()

    
    all_vars = args.output_vars + args.weather_vars
    for i in range(len(all_vars)):
        plt.figure(i+1)
        plt.title(all_vars[i])
        for j in range(len(arr)):
            plt.plot(np.array(arr[j])[:,i+4])  
        plt.show()
