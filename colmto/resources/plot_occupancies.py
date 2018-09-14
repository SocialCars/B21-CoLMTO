import matplotlib.pyplot as plt
import numpy as np
import json

g_aadt = ('4800', '8400', '12000', '13000', '15600', '19200', '22800', '26400', '30000', '33600', '37200', '40800', '44400', '48000')
g_ordering_colors = dict(zip(('best', 'random', 'worst'), ('#1b9e77','#7570b3','#d95f02')))
g_ordering_color_labels = dict(zip(('#1b9e77','#7570b3','#d95f02'), ('best', 'random', 'worst')))
g_lane_colors = dict(zip(('21edge_0', '21edge_1'), ('#fdae61','#2c7bb6')))
g_lane_labels = dict(zip(g_lane_colors, ('right lane', 'overtaking lane')))
g_data = {
    i_aadt: {
        i_ordering: json.load(open(f'occupancy-{i_aadt}-{i_ordering}.json'))
        for i_ordering in ('best', 'random', 'worst')
    } for i_aadt in g_aadt
}

for i_lane in g_lane_labels:
    plt.figure()
    plt.grid(b=True, which='both', color='lightgray', axis='y', linestyle='--')
    for i_ordering in zip(g_ordering_colors, (-1, 0, 1)):
        bp = plt.boxplot(
            [g_data[i_aadt][i_ordering[0]][i_lane]
             for i_aadt in g_aadt],
            positions=np.array(range(14))*2.0+i_ordering[1]*0.6,
            sym='',
            widths=0.4
        )
        plt.setp(bp['boxes'], color=g_ordering_colors[i_ordering[0]])
        plt.setp(bp['whiskers'], color=g_ordering_colors[i_ordering[0]])
        plt.setp(bp['caps'], color=g_ordering_colors[i_ordering[0]])
        plt.setp(bp['medians'], color=g_ordering_colors[i_ordering[0]])

    for i_color, i_label in g_ordering_color_labels.items():
        plt.plot([], c=i_color, label=i_label)
    plt.legend(title='Initial ordering of vehicles')
    plt.xticks(rotation=70)
    plt.xticks(range(0, len(g_aadt) * 2, 2), g_aadt)
    plt.xlim(-2, len(g_aadt)*2)
    plt.ylim(-0.005, 0.17)
    plt.title(f'Occupancy of {g_lane_labels[i_lane]} vs. demand')
    plt.ylabel('Occupancy')
    plt.xlabel('Demand as annual average daily traffic (AADT)')
    plt.tight_layout()
    plt.savefig(f'pdf/{i_lane}.pdf')
    plt.close()

for i_ordering in g_ordering_colors:
    for i_aadt in g_aadt:
        plt.figure()
        plt.grid(b=True, which='both', color='lightgray', axis='y', linestyle='--')
        for i_lane in g_lane_labels:
            lp = plt.plot(g_data[i_aadt][i_ordering][i_lane])
            plt.setp(lp, color=g_lane_colors[i_lane])
            plt.plot([], c=g_lane_colors[i_lane], label=f'{g_lane_labels[i_lane]} (max: {round(max(g_data[i_aadt][i_ordering][i_lane]), 2)}, median: {round(np.median(g_data[i_aadt][i_ordering][i_lane]), 2)})')
        plt.legend()
        plt.title(f'Lane occupancy for {i_aadt} AADT and {i_ordering} ordering')
        plt.ylabel('Occupancy')
        plt.ylim(-0.005, 0.17)
        plt.xlabel('Simulation steps, i.e. seconds')
        plt.xticks(rotation=70)
        plt.tight_layout()
        plt.savefig(f'pdf/{i_aadt}-{i_ordering}.pdf')
        plt.close()
