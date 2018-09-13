import numpy as np
import h5py
from matplotlib import pyplot as plt
import sys

def main(argv):
    '''
    main
    :param argv: cmdline args
    '''
    l_sensors = (68//4, 408//4, 1088//4, 1360//4)
    l_aadt = ('4800', '8400', '12000', '13000', '15600', '19200', '22800', '26400', '30000', '33600', '37200', '40800', '44400', '48000')
    l_colors = dict(zip(l_sensors, ['#e66101','#fdb863','#b2abd2','#5e3c99']))
    l_color_labels = dict(zip(['#e66101','#fdb863','#b2abd2','#5e3c99'], l_sensors))

    if len(sys.argv) != 2:
        print('Usage: plot.py hdf5-input-file')
        return

    with h5py.File(argv[1], 'r') as f_hdf5:
        for i_metric in ('dissatisfaction', 'relative_time_loss'):
            for i_ordering in ('best', 'random', 'worst'):
                for i_run in ('BASELINE', 'NOUGHT', 'ALPHA', 'BRAVO'):
                    for i_vtype in ('all','passenger', 'truck', 'tractor'):
                        rtls = {
                            i_sensor: [f_hdf5[f'{i_run}/{i_aadt}/{i_ordering}/{i_vtype}/{i_metric}'][:,i_sensor] for i_aadt in l_aadt]
                            for i_sensor in l_sensors
                        }
                        plt.figure()

                        for i_sensor in zip(l_sensors, list(range(-len(l_sensors)//2, 0))+list(range(1, len(l_sensors)//2+1))):
                            bp = plt.boxplot(rtls[i_sensor[0]], positions=np.array(range(len(rtls[i_sensor[0]])))*2.0+i_sensor[1]*0.4, sym='', widths=0.6)
                            plt.setp(bp['boxes'], color=l_colors[i_sensor[0]])
                            plt.setp(bp['whiskers'], color=l_colors[i_sensor[0]])
                            plt.setp(bp['caps'], color=l_colors[i_sensor[0]])
                            plt.setp(bp['medians'], color=l_colors[i_sensor[0]])

                        for i_color, i_label in l_color_labels.items():
                            plt.plot([], c=i_color, label=f'{i_label*4}m')

                        plt.legend()
                        plt.xticks(rotation=70)
                        plt.xticks(range(0, len(l_aadt) * 2, 2), l_aadt)
                        plt.xlim(-2, len(l_aadt)*2)
                        plt.ylim(-0.1, 3)
                        plt.tight_layout()
                        plt.savefig(f'{i_run}_{i_ordering}_{i_vtype}_{i_metric}.pdf')
                        plt.close()


if __name__ == '__main__':
    main(sys.argv)
