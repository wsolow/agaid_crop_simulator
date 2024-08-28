# Project Title

This is the Crop Simulator for the joint [AgAid](https://agaid.org/) Project between Oregon State 
University (OSU) and Washington State University (WSU).

## Description

An in-depth paragraph about your project and overview of use.

## Getting Started

### Dependencies

* This project is entirely self contained and built to run with Python 3.10.9
* Install using miniconda3 

### Installing

Recommended Installation Method:

1. Navigate to desired installation directory
2. git clone https://github.com/wsolow/agaid_crop_simulator.git
3. conda create -n cropsim python=3.10.9
4. conda activate cropsim
5. pip install -r requirements.txt

These commands will install all the required packages into the conda environment
needed to run all scripts in the agaid_crop_simulator package

### Executing program

* How to run the program
* Step-by-step bullets
```
code blocks for commands
```

## Help

Each subfolder has an associated README with information on configuring a 
crop simulation. Please read these carefully before attempting to modify a 
configuration

Email soloww@oregonstate.edu with any questions

## Authors

Contributors names and contact info

Will Solow (soloww@oregonstate.edu)

Dr. Sandhya Saisubramanian (sandhya.sai@oregonstate.edu)

## Version History

* 1.0.0
    * Initial Release

## License

This project is licensed under the [NAME HERE] License - see the LICENSE.md file for details

## Acknowledgments

The PCSE codebase and WOFOST8 Crop Simulator can be found at:
* [pcse](https://github.com/ajwdewit/pcse)

While we made meaningful modifications to the PCSE codebase to suit our needs, 
the vast majority of the working code in the PCSE directory the property of
Dr. Allard de Wit and Wageningen-UR Group. Please see the following paper for an
overview of WOFOST:
* [wofost](https://www-sciencedirect-com.oregonstate.idm.oclc.org/science/article/pii/S0308521X17310107)

The original inspiration for a crop simulator gym environment came from the paper:
* [crop_gym](https://arxiv.org/pdf/2104.04326)

However, only a small amount of the original code was used. We have since extended
their work to interface with multiple Reinforcement Learning Agents, have added
support for perennial fruit tree crops, multi-year simulations, and different sowing
and harvesting actions. 

The Python Crop Simulation Environment (PCSE) is well documented. Resources can 
be found here:
* [pcse_docs](https://pcse.readthedocs.io/en/stable/)

The WOFOST crop simulator is also well documented, and we use the WOFOST8 model
in our crop simulator. Documentation can be found here:
* [wofost_docs](https://wofost.readthedocs.io/en/latest/)