import pandas as pd
import json

def strip(text):
    try:
        return text.strip()
    except AttributeError:
        return text

def load_sensor_df(filepath):
    convs = {
        'manufacturer': strip,
        'address': strip,
        'facility': strip,
        'floor': strip,
        'notice': strip
    }

    df = pd.read_csv(filepath, sep='\t', converters=convs, dtype={
        'latitude': float,
        'longitude': float
    })

    fill_vals = {
        'axis_inclination': 0,
        'sampling_rate': 100,
        'version_code': 0,
        'version': 0,
    }

    df = df.fillna(value=fill_vals)
    usim_code = df['usim']

    def split_code_from_usim(x):
        try:
            return x.strip().split()[1].strip('()')
        except:
            return '0'

    df['coded_number'] = usim_code.map(lambda x: split_code_from_usim(x))
    df['usim'] = usim_code.map(lambda x: x.strip().split()[0])
    
    return df

def load_annoymized_sensor_df(filepath):
    df_ann = pd.read_csv(filepath, sep='\t', dtype={'usim': str})
    return df_ann

def export_h3_cell_coverage(cells, filepath):
    with open(filepath, 'w') as f:
        json.dump(cells, f, indent=4)

def import_h3_cell_coverage(filepath):
    with open(filepath, 'r') as f:
        result = json.load(f)
        return result
    
def import_amplitude_table(filepath, sep='\t'):
    df_amp = pd.read_csv(filepath, sep=sep)
    df_amp['usim'] = [d.strip().split()[0] for d in df_amp['usim']]
    return df_amp