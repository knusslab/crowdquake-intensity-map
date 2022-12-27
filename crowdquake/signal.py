import os

import h3
import numpy as np
import obspy
import pandas as pd
from obspy.core.stream import Stream
from obspy.core.trace import Trace
from obspy.geodetics.base import kilometers2degrees
from obspy.taup.tau import TauPyModel
from scipy import signal

EQMS_COUNT_TO_G = (2.5 / 2 ** 15)

travel_model = TauPyModel(model='ak135')

def fix_rotation(s: Stream):
    if len(s) != 3:
        return None
    
    # Prepare data from MSEED stream
    raws = []
    means = []
    
    for t in s:
        d = t.data
        means.append(np.mean(d))
        
        raws.append(d)
    
    raws = np.asarray(raws)
    means = np.asarray(means)
    
    # Creating rotation matrix
    idx = np.argsort(np.abs(means))
    raws = raws[idx, :]
    
    m1, m2, m3 = means[idx[0]], means[idx[1]], means[idx[2]]
    
    if m3 > 0:
        r3_theta = np.arctan(m1 / m2)
        r2_theta = -np.arctan(m1 / m3)
        r1_theta = np.arctan(m2 / m3)
    else:
        r3_theta = np.arctan(m1 / m2)
        r2_theta = -np.arctan(m1 / m3) + np.pi
        r1_theta = np.arctan(m2 / m3)
        
    
    v3 = np.asarray([np.cos(r3_theta), -np.sin(r3_theta), 0, np.sin(r3_theta), np.cos(r3_theta), 0, 0, 0, 1])
    v2 = np.asarray([np.cos(r2_theta), 0, np.sin(r2_theta), 0, 1, 0, -np.sin(r2_theta), 0, np.cos(r2_theta)])
    v1 = np.asarray([1, 0, 0, 0, np.cos(r1_theta), -np.sin(r1_theta), 0, np.sin(r1_theta), np.cos(r1_theta)])
    
    v3 = v3.reshape((-1, 3))
    v2 = v2.reshape((-1, 3))
    v1 = v1.reshape((-1, 3))
    
    vtemp = np.matmul(v3, v2)
    vtemp = np.matmul(vtemp, v1)
    rotated = np.matmul(vtemp, raws)
    
    stream_new = Stream()
    for i, t in enumerate(s):
        trace_new = Trace()
        trace_new.stats = t.stats
        d = rotated[i, :]    
        trace_new.data = d
        stream_new += trace_new
    
    return stream_new

def apply_filter(s: Stream, *, freq, order=5, fs=100):
    s_new = s.copy()
    sos = signal.butter(order, freq, 'bandpass', fs=fs, output='sos')
    for t in s_new:
        d = t.data
        d -= np.mean(d)
        d = signal.sosfilt(sos, d)
        t.data = d
    return s_new

def eval_pga(stream, usim, source_depth_in_km, df_amp=None, distance=0):
    max_idx = 0
    if len(stream) != 3:
        return 0

    # hgz = stream[0]

    degree = kilometers2degrees(distance)
    a = travel_model.get_travel_times(source_depth_in_km=source_depth_in_km, distance_in_degree=degree,
                                      phase_list=['p', 's'])
    s_time = a[1].time

    ref_start = stream[0].stats.starttime + s_time
    ref_end = ref_start + 10
    sliced = stream.slice(ref_start, ref_end)
    # sliced = stream

    def _eval_max(t):
        d = t.data.copy()
        d -= np.mean(d)
        pga = np.max(np.abs(d))

        return pga

    hge, hgn = _eval_max(sliced[0]), _eval_max(sliced[1])

    return hge if hge > hgn else hgn

def iter_mseed_for_pga(df, dt, home_path, *, 
                       source_depth_in_km, 
                       df_amp=None,
                       inspect_time_sec=80, 
                       filt=(1.5, 25), 
                       resolution=5,
                       dB_thres=-70,
                       distance_thres=None,
                       verbose=False):
    
    impact_time = obspy.core.utcdatetime.UTCDateTime(dt)
    
    results = {}
    scatter_dict = {'lat': [], 'lng': [], 'pga': []}
    
    
    for i, d in df.iterrows():
        try:
            filename = os.path.join(home_path, f'{d["usim"]}.mseed')
            s = obspy.read(filename)
            s_temp = s.slice(impact_time - inspect_time_sec, impact_time)
            
            # Check dB
            s_temp_adj = fix_rotation(s_temp, calib=EQMS_COUNT_TO_G * 9.80665, filt=filt)
            d_temp = s_temp_adj[0].data.copy()
            d_temp = d_temp - np.mean(d_temp)
            
            d_peak = 2.5 * 9.80665
            d_rms = np.sqrt(np.mean(d_temp ** 2))
            
            d_dB = 20 * np.log10(d_rms / d_peak)
            
            if d_dB >= dB_thres:
                if verbose:
                    print(f"excluding noisy sensor {d['usim']} from pga dict")
                continue
            
            s = s.slice(impact_time, impact_time + inspect_time_sec)
            s_adj = fix_rotation(s, calib=EQMS_COUNT_TO_G * 100, filt=filt)
            pga = eval_pga(s_adj, d['usim'], 
                           source_depth_in_km=source_depth_in_km, 
                           df_amp=df_amp, 
                           distance=d['distance'])
            
            if verbose:
                print(f'dB = {d_dB}, pga = {pga}')

            scatter_dict['lat'].append(d['latitude'])
            scatter_dict['lng'].append(d['longitude'])
            scatter_dict['pga'].append(pga)
            
            h = d[f'cell_{resolution}']
            if h not in results:
                results[h] = []
            results[h].append(pga)
            
        except Exception as e:
            if verbose:
                print(e)
            
    return results, scatter_dict

def eval_cells_pga(target_cells, pga_dict, *, K=1, interpolate_threshold=0, verbose=False):
    results = {}
    for c in target_cells:
        do_interpolate = False
        empty_cell = False
        list_pga = []
        if c not in pga_dict:
            if verbose:
                print(f"{c} has no sensor, do interpolation")
            do_interpolate = True
            empty_cell = True
        else:
            pga_vals = pga_dict[c]
            list_pga += pga_vals
            num_sensor_within = len(pga_vals)
            if num_sensor_within <= interpolate_threshold:
                if verbose:
                    print(f"{c} hasn't enough sensors ({num_sensor_within}), do interpolation")
                do_interpolate = True
        
        if do_interpolate:
            targets = list(h3.hex_range_distances(h=c, K=K))[K]
            for t in targets:
                if t in pga_dict:
                    list_pga += pga_dict[t]
        if len(list_pga) == 0:
            list_pga += [0]
        results[c] = np.mean(list_pga)
    
    return results

def apply_calib(s: Stream, calib) -> Stream:
    for tr in s:
        tr.data = tr.data.astype(np.float32) * calib
    return s

def apply_amplitude(s: Stream, amp_table: pd.DataFrame, usim: str) -> Stream:
    s_new = s.copy()
    try:
        amp = amp_table.loc[amp_table.usim == usim]['TF'].values[0]
    except IndexError:
        amp = 100
    for tr in s_new:
        tr.data = tr.data / (amp / 100)
    return s_new