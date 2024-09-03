#!/bin/bash
#SBATCH -J npk_test-%j
#SBATCH -p eecs,gpu,share
#SBATCH --array=0-1
#SBATCH -o output/npk_test-%A-%a.out
#SBATCH -e output/npk_test-%A-%a.err
#SBATCH -t 1-06:00:00
#SBATCH --gres=gpu:1

cd ../

python3 gen_data.py --env-reward fertilization_threshold --agent-type PPO --agent-path wandb/run-20240903_122037-2x7eywfu/files/agent.pt --wf-args.RDMSOL 50 --save-folder data/ppo_farm_RDMSOL_50.csv
python3 gen_data.py --env-reward fertilization_threshold --agent-type PPO --agent-path wandb/run-20240903_122037-2x7eywfu/files/agent.pt --save-folder data/ppo_farm_default.csv
python3 gen_data.py --env-reward fertilization_threshold --agent-type PPO --agent-path wandb/run-20240903_122037-2x7eywfu/files/agent.pt --wf-args.SMLIM .4 --save-folder data/ppo_farm_SMLIM_.4.csv
python3 gen_data.py --env-reward fertilization_threshold --agent-type PPO --agent-path wandb/run-20240903_122037-2x7eywfu/files/agent.pt --wf-args.RDMSOL 200 --save-folder data/ppo_farm_RDMSOL_200.csv
python3 gen_data.py --env-reward fertilization_threshold --agent-type PPO --agent-path wandb/run-20240903_122037-2x7eywfu/files/agent.pt --wf-args.SSI 2 --save-folder data/ppo_farm_SSI_2.csv
python3 gen_data.py --env-reward fertilization_threshold --agent-type PPO --agent-path wandb/run-20240903_122037-2x7eywfu/files/agent.pt --wf-args.CO2 100 --save-folder data/ppo_farm_CO2_100.csv
python3 gen_data.py --env-reward fertilization_threshold --agent-type PPO --agent-path wandb/run-20240903_122037-2x7eywfu/files/agent.pt --wf-args.CO2 450 --save-folder data/ppo_farm_CO2_450.csv
python3 gen_data.py --env-reward fertilization_threshold --agent-type PPO --agent-path wandb/run-20240903_122037-2x7eywfu/files/agent.pt --wf-args.KSUB .7 --save-folder data/ppo_farm_KSUB_.7.csv


