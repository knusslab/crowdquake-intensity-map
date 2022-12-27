import h3
import obspy

import geopandas as gpd
from shapely import ops
import pandas as pd

from crowdquake.io import load_sensor_df, load_annoymized_sensor_df

def load_shp_file(filepath, encoding='euc-kr'):
    CTP = gpd.read_file(filepath, encoding=encoding)
    CTP = CTP.to_crs(epsg=4326)
    return CTP


def fill_hexagons(geom_geojson, res, flag_swap = False, flag_return_df = False):
    """Fills a geometry given in geojson format with H3 hexagons at specified
    resolution. The flag_reverse_geojson allows to specify whether the geometry
    is lon/lat or swapped"""

    set_hexagons = h3.polyfill(geojson = geom_geojson,
                               res = res,
                               geo_json_conformant = flag_swap)
    print(set_hexagons)
    list_hexagons_filling = list(set_hexagons)

    if flag_return_df is True:
        # make dataframe
        df_fill_hex = pd.DataFrame({"hex_id": list_hexagons_filling})
        df_fill_hex["value"] = 0
        df_fill_hex['geometry'] = df_fill_hex.hex_id.apply(
                                    lambda x:
                                    {"type": "Polygon",
                                     "coordinates": [
                                        h3.h3_to_geo_boundary(h=x,
                                                              geo_json=True)
                                        ]
                                     })
        assert(df_fill_hex.shape[0] == len(list_hexagons_filling))
        return df_fill_hex
    else:
        return list_hexagons_filling
    
def get_cells_from_shp(shp, resolution=5):
    h3_total_set = set()

    for geo in shp.explode().geometry.map(lambda polygon: ops.transform(lambda x, y: (y, x), polygon)):
        set_hexagons = h3.polyfill(geojson=geo.__geo_interface__, res=5)
        h3_total_set.update(set_hexagons)
    
    return h3_total_set

def eval_observable_sets(shp_cells, sensor_cells):
    """
    Evaluate observable sets from (1) shp, and (2) deployed sensors
    
    return: all observable sets
    """
    set_total = set()
    set_total.update(shp_cells)
    set_total.update(sensor_cells)
    
    return set_total

def load_and_prepare_sensors(filepath, resolution=5):
    df_sensor = load_annoymized_sensor_df(filepath)
    set_sensors = set()
    sensor_cells = []
    for _, d in df_sensor.iterrows():
        h = h3.geo_to_h3(lat=d['latitude'], lng=d['longitude'], resolution=resolution)
        sensor_cells.append(h)
        set_sensors.add(h)
    df_sensor[f'cell_{resolution}'] = sensor_cells
    return df_sensor, set_sensors

def select_sensors_by_cells(df, cells, lat, lng, resolution=5):
    df_new = df.copy()
    df_new = df[df[f'cell_{resolution}'].isin(cells)]
    
    # Evaluate distance from lat, lng pair
    dis_from = []
    for i, d in df_new.iterrows():
        dis = obspy.geodetics.gps2dist_azimuth(lat, lng, d['latitude'], d['longitude'])[0]
        dis /= 1000.
        dis_from.append(dis)
    
    df_new.loc[:, 'distance'] = dis_from
    df_new = df_new.sort_values(by='distance')
    
    return df_new

def get_cells_within(lat, lng, distance, cells):
    result_set = set()
    for c in cells:
        target = h3.h3_to_geo(c)
        dist = h3.point_dist((lat, lng), target)
        if dist <= distance:
            result_set.add(c)
    return result_set