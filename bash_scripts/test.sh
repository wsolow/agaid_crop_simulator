#!/bin/bash
#SBATCH -J npk_test-%j
#SBATCH -p eecs,gpu,share
#SBATCH --array=0-1
#SBATCH -o output/npk_test-%A-%a.out
#SBATCH -e output/npk_test-%A-%a.err
#SBATCH -t 1-06:00:00
#SBATCH --gres=gpu:1

cd ../

python3 test_wofost.py