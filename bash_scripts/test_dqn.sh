#!/bin/bash
#SBATCH -J npk_test-%j
#SBATCH -p eecs,gpu,share
#SBATCH --array=0-1
#SBATCH -o output/npk_test-%A-%a.out
#SBATCH -e output/npk_test-%A-%a.err
#SBATCH -t 1-06:00:00
#SBATCH --gres=gpu:1

echo "Job ID: $SLURM_JOB_ID"
echo "Array Job ID: $SLURM_ARRAY_JOB_ID"
echo "Task ID: $SLURM_ARRAY_TASK_ID"

SEED="${SLURM_ARRAY_JOB_ID}${SLURM_ARRAY_TASK_ID}"
cd ../
python3 train_agent.py --agent-type "DQN"
