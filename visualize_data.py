# Written Sept 2024, by Will Solow
# Code to support data generation given a single policy and single farm
# Allows the user to specify a set of years and locations (thus historical weather data)
# And a specific farm from which to gather data from 

import gymnasium as gym
import numpy as np
import wofost_gym
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import torch
import sys
import yaml

from utils import Args
import tyro
import utils
import wofost_gym.policies as policies

np.set_printoptions(precision=3)
def norm(x):
    return (x-np.nanmin(x))/(np.nanmax(x)-np.nanmin(x))

def load_labels(args):
    unit_fname = args.unit_fpath
    title_fname = args.name_fpath
    with open(unit_fname) as fp:
        try:
            r = yaml.safe_load(fp)
        except yaml.YAMLError as e:
            msg = "Failed parsing agromanagement file %s: %s" % (unit_fname, e)
            print(msg)
    with open(title_fname) as jp:
        try:
            y = yaml.safe_load(jp)
        except yaml.YAMLError as e:
            msg = "Failed parsing agromanagement file %s: %s" % (title_fname, e)
            print(msg)

    return r, y
    
def plot_average_farms(args, filenames, agents):
    r, y = load_labels(args)

    
    for a in agents:
        farm_avg = []
        farm_std = []
        for f in filenames:
            df = pd.read_csv(f'{args.save_folder}{f}_{a}.csv', index_col=0)
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
        ind = 2
        for i in range(len(farm_avg)):
            plt.plot(farm_avg[i,:,ind],label=filenames[i])
            plt.fill_between(np.arange(clipped_length),farm_avg[i,:,ind]-farm_std[i,:,ind],farm_avg[i,:,ind]+farm_std[i,:,ind], alpha=.5, linestyle='solid')
            plt.xlabel('Days')
        plt.legend()
        plt.show()


    '''all_vars = args.output_vars + args.weather_vars
    for j in range(len(all_vars)):
        plt.figure(j+1)
        plt.title(y[all_vars[j]])
        plt.xlabel('Days')
        plt.ylabel(r[all_vars[j]])
        for i in range(len(farm_avg)):
            #plt.plot(farm_avg[i,:,j],label=filenames[i])
            plt.plot(farm_avg[i,:,j])
            plt.fill_between(np.arange(clipped_length),farm_avg[i,:,j]-farm_std[i,:,j],farm_avg[i,:,j]+farm_std[i,:,j], alpha=.5, linestyle='solid')
        plt.plot(np.arange(len(farm_avg[i,:,j])), np.tile([15],len(farm_avg[i,:,j])), c='k', linestyle='dashed', label='Threshold')
        plt.legend()
        plt.show()'''

def plot_matrix(args, data_files, agents):
    ag_avg = []
    ag_std = []
    for j in range(len(agents)):
        farm_avg = []
        farm_std = []
        for i in range(len(data_files)):
            print(f'[{j},{i}], {agents[j]}, {data_files[i]}' )
            df = pd.read_csv(f'{args.save_folder}{data_files[i]}_{agents[j]}.csv', index_col=0)
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

def plot_season(dfs, names):
    """
    Plot the season where we represent each season's actions as 
    fertilization and irrigation and plot the total growth
    """
    labels = [s.strip('.csv') for s in names]
    labels = [s.strip('data/') for s in labels]

    REQUIRED_VARS = ["TOTN", "TOTP", "TOTK", "TOTIRRIG", "WSO"]

    cols = ['#377eb8', '#ff7f00', '#4daf4a',
                  '#f781bf', '#a65628', '#984ea3',
                  '#999999', '#e41a1c', '#dede00']
    linestyles = ['solid', 'dashed', 'dotted', 'dashdot']

    """Assert all necessary params are present"""
    for df in dfs:
        print(df["GWSO"])
        print(np.cumsum(df["GWSO"]))
        df.insert(6, "WSO", np.cumsum(df["GWSO"]))
    for df in dfs:
        utils.assert_vars(df, REQUIRED_VARS)
    new_dfs = []
    for i in range(len(dfs)):
        new_dfs.append(dfs[i].iloc[0:323])

    dfs = new_dfs
    print(new_dfs[0])

    """Create fertilizer/irrigation values"""
    new_totn = [np.array(df["TOTN"].copy()) for df in dfs]
    new_totp = [np.array(df["TOTP"].copy()) for df in dfs]
    new_totk = [np.array(df["TOTK"].copy()) for df in dfs]
    new_totirrig = [np.array(df["TOTIRRIG"].copy()) for df in dfs]
    
    for i in range(len(dfs)): new_totn[i][1:] -= new_totn[i][:-1].copy()
    for i in range(len(dfs)): new_totp[i][1:] -= new_totp[i][:-1].copy()
    for i in range(len(dfs)): new_totk[i][1:] -= new_totk[i][:-1].copy()
    for i in range(len(dfs)): new_totirrig[i][1:] -= new_totirrig[i][:-1].copy()

    """Create indicies for graphing"""
    totn_inds = [np.argwhere(new_totn[i] != 0).flatten() for i in range(len(dfs))]
    totn_vals = [new_totn[i][totn_inds[i]] for i in range(len(dfs))]
    totp_inds = [np.argwhere(new_totp[i] != 0).flatten() for i in range(len(dfs))]
    totp_vals = [new_totp[i][totp_inds[i]] for i in range(len(dfs))]
    totk_inds = [np.argwhere(new_totk[i] != 0).flatten() for i in range(len(dfs))]
    totk_vals = [new_totk[i][totk_inds[i]] for i in range(len(dfs))]
    totirrig_inds = [np.argwhere(new_totirrig[i] != 0).flatten() for i in range(len(dfs))]
    totirrig_vals = [new_totirrig[i][totirrig_inds[i]] for i in range(len(dfs))]

    fig, ax = plt.subplots(1)
    ax.set_xlim(0, len(dfs[0]))
    ax.set_xlabel('Days')
    ax.set_ylabel('Mineral Applied (kg/ha) (cm/ha)')
    ax.set_title('Yield Comparison of Two Fertilization Policies')

    max_y = np.max([np.max(new_totn), np.max(new_totp), np.max(new_totk), np.max(new_totirrig)])
    ax.set_ylim(0, 10)
    twinax = plt.twinx(ax)
    twinax.set_ylabel('Yield (kg/ha)')
    
    """Add fertilizer and irrigation patches to plot"""
    print(totirrig_inds)
    n = [[patches.Rectangle((totn_inds[j][i],0), 1, totn_vals[j][i], color='g', linestyle=linestyles[j], alpha=.6) \
          for i in range(len(totn_inds[j]))] for j in range(len(totn_inds))]
    [[ax.add_patch(ni) for ni in nj] for nj in n]
    p = [[patches.Rectangle((totp_inds[j][i],0), 1, totp_vals[j][i], color='m', linestyle=linestyles[j], alpha=.6) \
          for i in range(len(totp_inds[j]))] for j in range(len(totn_inds))]
    [[ax.add_patch(pi) for pi in pj] for pj in p]
    k = [[patches.Rectangle((totk_inds[j][i],0), 1, totk_vals[j][i], color='y', linestyle=linestyles[j], alpha=.6) \
          for i in range(len(totk_inds[j]))] for j in range(len(totn_inds))]
    [[ax.add_patch(ki) for ki in kj] for kj in k]
    w = [[patches.Rectangle((totirrig_inds[j][i],0), 1, totirrig_vals[j][i], color='b', linestyle=linestyles[j], alpha=.6) \
          for i in range(len(totirrig_inds[j]))] for j in range(len(totn_inds))]
    [[ax.add_patch(wi) for wi in wj] for wj in w]

    labs = [twinax.plot(dfs[i]["WSO"], color=cols[i], label=labels[i], linestyle=linestyles[i]) for i in range(len(dfs))]
    
    n = patches.Patch(color='g', alpha=.6, label='Nitrogen')
    p = patches.Patch(color='m', alpha=.6, label='Phosphorous')
    k = patches.Patch(color='y', alpha=.6, label='Potassium')
    w = patches.Patch(color='b', alpha=.6, label='Water')
    print(labs)
    print([n,p,k,w])
    print([n,p,k,w]+labs)
    hands = [n,p,k,w]
    [hands.append(labs[i][0]) for i in range(len(labs))]
    print(hands)
    plt.legend(handles=hands)
    plt.show()

def plot_vars(dfs, names):
    labels = [s.strip('.csv') for s in names]
    labels = [s.strip('data/') for s in labels]

    REQUIRED_VARS = []

    cols = ['#377eb8', '#ff7f00', '#4daf4a',
                  '#f781bf', '#a65628', '#984ea3',
                  '#999999', '#e41a1c', '#dede00']

    """Assert all necessary params are present"""
    for df in dfs:
        utils.assert_vars(df, REQUIRED_VARS)

    for i in range(len(dfs[0].columns)):
        plt.figure(i)
        plt.title(dfs[0].columns[i])
        for j in range(len(dfs)):
            plt.plot(dfs[j].iloc[:,i], label=dfs[j].columns[i],c=cols[j])
    
    plt.show()

if __name__ == "__main__":
    names = ["data/tot_growth_ppo_default_farm_DEFAULT.csv", "data/tot_growth_ppo_co2_100_farm_DEFAULT.csv"]
    dfs = utils.load_data_files(names)
    plot_season(dfs, names)
    #plot_vars(dfs, names)

    sys.exit(0)
    args = tyro.cli(Args)

    env_id, env_kwargs = utils.get_gym_args(args)

    # Farm
    output_vars = ['TOTN', 'TOTP', 'TOTK', 'GWSO', 'TOTIRRIG', 'DVS', 'LAI','RD', 'WSO','NAVAIL','PAVAIL','KAVAIL','WC','SM']
    # PPO
    output_vars = ['TOTN',	'TOTP',	'TOTK',	'TOTIRRIG',	'NAVAIL', 'PAVAIL',	'KAVAIL',	'SM',	'GWSO',	'DVS']
    # PPO Farm
    output_vars = ['TOTN','TOTP',	'TOTK',	'TOTIRRIG',	'GWSO',	'DVS',	'LAI',	'RD',	'WSO',	'NAVAIL',	'PAVAIL',	'KAVAIL',	'WC',	'SM']
    args.output_vars = output_vars

    # Make the gym environment - should be as a SyncVectorEnv to support
    # Easy loading from PPO/SAC/DQN agentzs

    data_files = ['farm_DEFAULT', 'farm_CO2_100', 'farm_CO2_450', 'farm_KSUB_.7', \
                  'farm_RDMSOL_50', 'farm_RDMSOL_200', 'farm_SMLIM_.4', 'farm_SSI_2']
    data_files = ['farm_DEFAULT', 'farm_CO2_100', 'farm_CO2_450', 'farm_KSUB_.7', \
                  'farm_RDMSOL_50', 'farm_RDMSOL_200', 'farm_SSI_2']
    
    #agents = ['default', 'ksub_.7', 'co2_100', 'co2_450', 'rdmsol_50', 'rdmsol_200', 'ssi_2', 'smlim_.4']
    agents = ['belowi_0.3_2', 'belowi_0.4_1', 'belown_5_3', 'belown_10_1', 'intervaln_7_1', 'intervaln_28_3', 'intervalw_7_1', 'intervalw_28_3']

    #plot_average_farms(args, data_files, agents)
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
