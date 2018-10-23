import matplotlib.pyplot as plt
import numpy as np
import json
from pathlib import Path
import argparse

def flatten(sequences):
    for seq in sequences:
        yield from seq

Path('pdf').mkdir(exist_ok=True)
Path('stats').mkdir(exist_ok=True)

g_parser = argparse.ArgumentParser(
    prog='colmto',
    description='Process parameters for CoLMTO.'
)
g_parser.add_argument(
    '--jsondir', dest='jsondir', type=Path,
    default='json'
)
g_args = g_parser.parse_args()
g_policies = ('BASELINE', 'NOUGHT', 'ALPHA', 'BRAVO')
g_orderings = ('best', 'random', 'worst')
g_aadt = ('4800', '8400', '12000', '13000', '15600', '19200', '22800', '26400', '30000', '33600', '37200', '40800', '44400', '48000')
g_ordering_colors = dict(zip(g_orderings, ('#1b9e77','#7570b3','#d95f02')))
g_ordering_color_labels = dict(zip(('#1b9e77','#7570b3','#d95f02'), g_orderings))
g_lane_colors = dict(zip(('21edge_0', '21edge_1'), ('#fdae61','#2c7bb6')))
g_lane_labels = dict(zip(g_lane_colors, ('right lane', 'overtaking lane')))
g_data = {
    i_policy: {
        i_aadt: {
            i_ordering: json.load(open(g_args.jsondir / f'occupancy-{i_policy}-{i_aadt}-{i_ordering}.json'))
            for i_ordering in g_orderings
        } for i_aadt in g_aadt
    } for i_policy in g_policies
}

# adjust data
g_min = min(
    flatten(
        [g_data[i_policy][i_aadt][i_ordering][i_lane]
         for i_lane in g_lane_labels
         for i_ordering in g_orderings
         for i_aadt in g_aadt
         for i_policy in g_policies]
    )
)
if g_min < 0:
    for i_policy in g_policies:
        for i_aadt in g_aadt:
             for i_ordering in g_orderings:
                 for i_lane in g_lane_labels:
                    g_data[i_policy][i_aadt][i_ordering][i_lane] = [v-g_min for v in g_data[i_policy][i_aadt][i_ordering][i_lane]]

g_stats = {
    i_policy: {
        i_ordering: {
            i_aadt: {
                i_lane: {}
                for i_lane in g_lane_labels
            } for i_aadt in g_aadt
        } for i_ordering in g_orderings
    } for i_policy in g_policies
}

g_ylim = max(
    flatten(
        [g_data[i_policy][i_aadt][i_ordering][i_lane]
         for i_policy in g_policies
         for i_aadt in g_aadt
         for i_ordering in g_orderings
         for i_lane in g_lane_labels]
    )
)

for i_policy in g_policies:
    for i_lane in g_lane_labels:
        plt.figure()
        plt.grid(b=True, which='both', color='lightgray', axis='y', linestyle='--')
        for i_ordering in zip(g_ordering_colors, (-1, 0, 1)):
            bp = plt.boxplot(
                [g_data[i_policy][i_aadt][i_ordering[0]][i_lane]
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
            plt.plot([], c=i_color, label=f'{i_label} (median: {np.round(np.median(list(flatten((g_data[i_policy][i_aadt][i_label][i_lane] for i_aadt in g_aadt)))), 2)}, max: {round(max(flatten([g_data[i_policy][i_aadt][i_label][i_lane] for i_aadt in g_aadt])), 2)})')

        plt.legend(title='Initial ordering of vehicles')
        plt.xticks(rotation=70)
        plt.xticks(range(0, len(g_aadt) * 2, 2), g_aadt)
        plt.xlim(-2, len(g_aadt)*2)
        plt.ylim(-0.005, g_ylim)
        plt.title(f'Occupancy of {g_lane_labels[i_lane]} vs. demand')
        plt.ylabel('Occupancy')
        plt.xlabel('Demand as annual average daily traffic (AADT)')
        plt.tight_layout()
        plt.savefig(f'pdf/{i_policy}-{i_lane}.pdf')
        plt.close()

for i_policy in g_policies:
    for i_ordering in g_ordering_colors:
        for i_aadt in g_aadt:
            plt.figure()
            plt.grid(b=True, which='both', color='lightgray', axis='y', linestyle='--')
            for i_lane in g_lane_labels:
                l_min = round(min(g_data[i_policy][i_aadt][i_ordering][i_lane]), 12)
                l_median = np.round(np.median(g_data[i_policy][i_aadt][i_ordering][i_lane]), 12)
                l_max = round(max(g_data[i_policy][i_aadt][i_ordering][i_lane]), 12)
                lp = plt.plot(g_data[i_policy][i_aadt][i_ordering][i_lane])
                plt.setp(lp, color=g_lane_colors[i_lane])
                plt.plot([], c=g_lane_colors[i_lane], label=f'{g_lane_labels[i_lane]} (max: {round(l_max, 2)})')
                lp = plt.plot([l_median]*len(g_data[i_policy][i_aadt][i_ordering][i_lane]))
                plt.setp(lp, color=g_lane_colors[i_lane], linestyle='--')
                plt.plot([], c=g_lane_colors[i_lane], label=f'{g_lane_labels[i_lane]} median ({round(l_median, 2)})')
                g_stats[i_policy][i_ordering][i_aadt][i_lane] = {
                    'min': l_min,
                    'median': l_median,
                    'max': l_max
                }

            plt.legend()
            plt.title(f'Lane occupancy for {i_aadt} AADT and {i_ordering} ordering')
            plt.ylabel('Occupancy')
            plt.ylim(-0.005, g_ylim)
            plt.xlabel('Simulation steps, i.e. seconds')
            plt.xticks(rotation=70)
            plt.tight_layout()
            plt.savefig(f'pdf/{i_policy}-{i_aadt}-{i_ordering}.pdf')
            plt.close()

with open('stats/stats.json', 'w') as f_json:
    json.dump(g_stats, f_json, sort_keys=True, indent=4, separators=(', ', ' : '))