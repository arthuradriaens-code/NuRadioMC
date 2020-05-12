from NuRadioMC.utilities.Veff import export, get_Veff, get_Veff_array
from NuRadioReco.utilities import units
import matplotlib.pyplot as plt
import numpy as np
import argparse
import json

"""
This file explains how to use the utilities.Veff module to calculate and plot
the effective volumes of a set of NuRadioMC simulations. The path given to the
program should have previously merged output HDF5 files.

To run it, use:

python T03EffectiveVolumes.py --folder path/to/results_folder --output_file output_file.json
"""

parser = argparse.ArgumentParser(description='Check NuRadioMC output')
parser.add_argument('--folder', type=str, default='results',
                    help='path to NuRadioMC simulation output folder')
parser.add_argument('--output_file', type=str, default='results/Veffs.json',
                    help='path to NuRadioMC simulation output folder')
args = parser.parse_args()

folder = args.folder
output_file = args.output_file

"""
The function get_Veff in utilities.Veff calculates effective volumes using the
path to a folder with NuRadioMC outputs as an argument. In this folder there
should be several files containing the simulation results for different energies,
although in our example we will only use one. There can also be several sets
of files for different zenith bands. get_Veff will return a dictionary with all
the information to calculate effective volumes for different energies and
zenith bands.

We have used the keyword argument point_bins=False because the bins for our example
are extended, that is, they contain a range of energies.

IMPORTANT: if the n_events_per_file argument has been used so that the NuRadioMC
files are split, the module utilities.merge_hdf5 should be used to merge the files.
Once every energy bin has a unique HDF5 output file, the Veff module can be run.
"""
data_Veff = get_Veff(folder, point_bins=False)

"""
Although data_Veff has all the information we need, it is a bit cumbersome
to read directly, so that's why we resort to the function get_Veff_array. This
function returns a 5-element tuple with:
- An 4-D array with the effective volumes
- A 1-D array with the centre energies for each bin (if point_bins=False)
- The zenith bins for each one of the zenith band simulations (in our case, we
only have a single zenith band equal to the whole sky)
- A list with the trigger names
- A 1-D array with the angular weights for each zenith band simulation. If the solid
angle for a simulation set is larger than for the other, it should carry more weight
when we try to patch them all together to get the total volumes.
"""
Veff_array, energies, zenith_bins, trigger_names, weights = get_Veff_array(data_Veff)

"""
There are some functions with the same syntax to calculate effective areas for
atmospheric muon simulations: get_Aeff and get_Aeff_array. Keep in mind that the
latter returns a 4-element tuple, with no weights.

The structure of the 4-D Veff_array returned is as follows: the first dimension
chooses the energy, the second chooses the zenith band and the third chooses
the trigger:

Veff_item = Veff_array[i_energy, i_zenith, i_trigger]

Then, each Veff_item has three numbers.
- Veff_item[0] is the effective volume
- Veff_item[1] is the poissonian uncertainty of the effective volume
- Veff_item[2] is the sum of the weights of all the triggering events contained
in a given energy and zenith band for the chosen trigger.

For our example, we only have a single file, so we choose the only zenith index.
We choose as well the first trigger (index 0) just as an example.
"""
zenith_index = 0
trigger_index = 0

# Selecting the effective volumes
Veffs = Veff_array[:, zenith_index, trigger_index, 0]
# Selecting the uncertainties
unc_Veffs = Veff_array[:, zenith_index, trigger_index, 1]

"""
We plot now the effective volumes in cubic kilometres as a function of the
neutrino energy in electronvolts, with the uncertainty in cubic kilometres
as an error bar. For our example, this is going to look just a sad, lonely point,
but as an exercise you can create more simulations with different energy bins
and plot the effective volumes with this same file.
"""
plt.errorbar(energies/units.eV, Veffs/units.km3, unc_Veffs/units.km3, marker='o')
plt.ylabel(r'Effective volume [km$^{3}$]')
plt.xlabel('Neutrino energy [eV]')
plt.xscale('log')
plt.yscale('log')
plt.show()

"""
To end with, we can export the data to a human-readable json (or yaml) file.
This file can then be used for quick plotting or sensitivity calculations.
I'm going to use the following method instead of using the export function
in Veff.py because I prefer the following way of storing the information.
"""
output_dict = {}

for trigger_index, trigger_name in enumerate(trigger_names):

    output_dict[trigger_name] = {}

    Veffs = Veff_array[:, zenith_index, trigger_index, 0]
    output_dict[trigger_name]['Veffs'] = list(Veffs)

    unc_Veffs = Veff_array[:, zenith_index, trigger_index, 1]
    output_dict[trigger_name]['Veffs_uncertainty'] = list(unc_Veffs)

output_dict['energies'] = list(energies)

with open(output_file, 'w') as fout:
    json.dump(output_dict, fout, sort_keys=True, indent=4)
