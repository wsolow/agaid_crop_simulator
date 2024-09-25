"""File for testing the installation and setup of the WOFOST Gym Environment
with a few simple plots for output 

Written by: Will Solow, 2024
"""

import gymnasium as gym
import numpy as np
import tyro
import matplotlib.pyplot as plt
import re

import wofost_gym
import wofost_gym.policies as policies
from wofost_gym.envs.wofost_base import NPK_Env, Plant_NPK_Env, Harvest_NPK_Env
from utils import Args
import utils
import sys
from pathlib import Path
import ruamel.yaml
import copy
from ruamel.yaml.comments import CommentedMap

if __name__ == "__main__":
    plot = True
    graph = False
    args = tyro.cli(Args)

    yaml = ruamel.yaml.YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.preserve_quotes = True
    crops = ['barley', 'seed_onion', 'cassava', 'chickpea', 'cotton', 'cowpea', 'fababean', 'groundnut', 'maize', \
                'millet', 'mungbean', 'pigeonpea', 'rapeseed', 'rice', 'sorghum', \
                'soybean', 'sugarbeet', 'sugarcane', 'sunflower', 'sweetpotato', 'tobacco', 'wheat',\
                'pear', 'jujube']
    crops = ['potato', 'jujube']

    def order(template, data, template_write):
        for key in template:
            if key in data:
                if isinstance(data[key], ruamel.yaml.comments.CommentedMap):
                    order(template[key], data[key], template_write[key])
                else:
                    template_write[key] = data[key]
            else:
                template_write.pop(key)

    for c in crops:
        template_file = 'env_config/crop_config/template.yaml'
        data_file = f'env_config/crop_config/{c}.yaml'
        output_file = f'test_crops/{c}.yaml'

        with open(template_file, 'r') as f:
            content = f.read()
            content_new = re.sub(r"crop", c, content)
            top_template = yaml.load(content_new)

        with open(data_file, 'r') as f:
            top_data = yaml.load(f)

        with open(template_file, 'r') as f:
            content = f.read()
            content_new = re.sub(r"crop", c, content)
            template_write = yaml.load(content_new)
        
        order(top_template, top_data, template_write)

        with open(output_file, 'w') as f:
            yaml.dump(template_write, f)


