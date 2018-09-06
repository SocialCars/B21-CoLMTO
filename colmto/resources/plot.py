import numpy as np
import h5py
from matplotlib import pyplot as plt
import sys

def set_box_color(bp, color):
    plt.setp(bp['boxes'], color=color)
    plt.setp(bp['whiskers'], color=color)
    plt.setp(bp['caps'], color=color)
    plt.setp(bp['medians'], color=color)

def main(argv):
    '''
    main
    :param argv: cmdline args
    '''
    l_sensors = (68//4, 408//4, 1088//4, 1360//4)
    l_aadt = ('4800', '8400', '12000', '13000', '15600', '19200', '22800', '26400', '30000', '33600', '37200', '40800', '44400', '48000')
    l_colors = dict(zip(l_sensors, ('#e66101','#fdb863','#b2abd2','#5e3c99')))
    l_color_labels = dict(zip(('#e66101','#fdb863','#b2abd2','#5e3c99'), l_sensors))

    if len(sys.argv) != 2:
        print('Usage: plot.py hdf5-input-file')
        return

    with h5py.File(argv[1], 'r') as f_hdf5:

    	rtls = {
    		i_sensor: [h5[f'BASELINE/{i_aadt}/random/passenger/relative_time_loss'][:,340] for i_aadt in l_aadt]
    	} for i_sensor in l_sensors

    	plt.figure()

    	for i_sensor in zip(l_sensors, list(range(-len(l_sensors)//2, 0))+list(range(1, len(l_sensors)//2+1))):
    		pb = plt.boxplot(rtls[i_sensor[0]], positions=np.array(range(len(rtls[i_sensor[0]])))*2.0+i_sensor[1]*0.4, sym='', widths=0.6)
    		set_box_color(bp, l_colors[i_sensor[0]])

    	for i_color, i_label in enumerate(l_color_labels):
    		plt.plot([], c=i_color, label=str(i_label))
		
		plt.legend()
		plt.xticks(range(0, len(l_aadt) * 2, 2), l_aadt)
		plt.xlim(-2, len(l_aadt)*2)
		plt.ylim(-0.1, 1)
		plt.tight_layout()
		plt.savefig('baseline.png')


if __name__ == '__main__':
    main(sys.argv)
