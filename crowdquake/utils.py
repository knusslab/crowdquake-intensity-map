import obspy
import pandas as pd
import os

def intToRoman(num):

    # Storing roman values of digits from 0-9
    # when placed at different places
    m = ["", "M", "MM", "MMM"]
    c = ["", "C", "CC", "CCC", "CD", "D",
         "DC", "DCC", "DCCC", "CM "]
    x = ["", "X", "XX", "XXX", "XL", "L",
         "LX", "LXX", "LXXX", "XC"]
    i = ["", "I", "II", "III", "IV", "V",
         "VI", "VII", "VIII", "IX"]

    # Converting to roman
    thousands = m[num // 1000]
    hundreds = c[(num % 1000) // 100]
    tens = x[(num % 100) // 10]
    ones = i[num % 10]

    ans = (thousands + hundreds +
           tens + ones)

    return ans


class EventData:
    def __init__(self, lat, lng, depth, magnitude, max_intensity,
                 origin_time, basepath, pga_eval_distance=100., *, inspection_adj=0,
                 distance_threshold: int = 40) -> None:
        self.lat = lat
        self.lng = lng
        self.depth = depth
        self.origin_time = obspy.core.UTCDateTime(origin_time)
        self.magnitude = magnitude
        self.max_intensity = max_intensity
        self.pga_eval_distance = pga_eval_distance
        self.health_table_fname = os.path.join('dataset', basepath, 'sensor_health.xlsx')
        self.basepath = basepath
        df_health = pd.read_excel(self.health_table_fname, dtype={'usim': str})
        # usim as index
        self.df_health = df_health.set_index('usim')
        self.lookup_secs = 10
        self.inspection_adjustment = inspection_adj
        self.distance_threshold = distance_threshold


    def is_usim_available(self, usim):
        if usim not in self.df_health.index:
            return False
        return not any(self.df_health.loc[usim, 'health'].apply(lambda x: 'RED' in x or 'NOT_AVAILABLE' in x))

    def is_usim_has_best_condition(self, usim):
        if usim not in self.df_health.index:
            return False
        return all(self.df_health.loc[usim, 'health'].apply(lambda x: 'GREEN' in x))

    def readable_name(self) -> str:
        return f"M{self.magnitude}_{intToRoman(self.max_intensity)}_{self.lat}_{self.lng}_{self.depth}_{self.origin_time}"

KMA_MMI_STEPS = [0, 0.07, 0.23, 0.76, 2.56,
                 6.86, 14.73, 31.66, 68.01, 146.14, 980.0]

MMI_LABELS = {
    "1": "I",
    "2": "II",
    "3": "III",
    "4": "IV",
    "5": "V",
    "6": "VI",
    "7": "VII",
    "8": "VIII",
    "9": "IX",
    "10": "X",
}