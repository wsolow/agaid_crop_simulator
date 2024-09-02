#!/bin/bash
#SBATCH -J npk_test-%j
#SBATCH -p eecs,gpu,share
#SBATCH --array=0-1
#SBATCH -o output/npk_test-%A-%a.out
#SBATCH -e output/npk_test-%A-%a.err
#SBATCH -t 1-06:00:00
#SBATCH --gres=gpu:1

cd ../

python3 gen_data.py --wf-args.RDMSOL 50 --save-path data/farm_RDMSOL_50.csv
python3 gen_data.py --save-path data/farm_default.csv
python3 gen_data.py --wf-args.SMLIM .4 --save-path data/farm_SMLIM_.4.csv
python3 gen_data.py --wf-args.RDMSOL 200 --save-path data/farm_RDMSOL_200.csv
python3 gen_data.py --wf-args.SSI 2 --save-path data/farm_SSI_2.csv
python3 gen_data.py --wf-args.CO2 100 --save-path data/farm_CO2_100.csv
python3 gen_data.py --wf-args.CO2 450 --save-path data/farm_CO2_450.csv
python3 gen_data.py --wf-args.KSUB .7 --save-path data/farm_KSUB_.7.csv
