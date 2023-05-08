# json_order.py
import json
import os


def reorder_json(input_file, output_file):
    with open(input_file, 'r') as f:
        data = json.load(f)

    sorted_data = dict(sorted(data.items(), key=lambda x: int(x[0])))

    with open(output_file, 'w') as f:
        json.dump(sorted_data, f, indent=4)