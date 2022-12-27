import h3
import numpy as np
from shapely import geometry

import matplotlib as mpl
import matplotlib.pyplot as plt
import cartopy.feature as cfeature
import cartopy.crs as ccrs

from matplotlib.colors import ListedColormap

from obspy.geodetics import gps2dist_azimuth

KMA_MMI_COLORS = [
    (255, 255, 255),  # <= 0.07
    (185, 221, 231),  # <= 0.23
    (136, 202, 84),  # <= 0.76
    (255, 254, 62),  # <= 2.56
    (255, 182, 46),  # <= 6.86
    (233, 0, 11),    # <= 14.73
    (155, 31, 105),  # <= 31.66
    (90, 32, 32),    # <= 68.01
    (68, 33, 6),     # <= 146.14
    (0, 0, 0)
]

KMA_MMI_STEPS = [0, 0.07, 0.23, 0.76, 2.56,
                 6.86, 14.73, 31.66, 68.01, 146.14, 980.0]

KMA_MMI_COLORS = np.asarray(KMA_MMI_COLORS)
KMA_MMI_COLORS = KMA_MMI_COLORS / 255

IMAGE_BASE_SIZE = 24

KMA_MMI_CMAP = ListedColormap(KMA_MMI_COLORS)
KMA_MMI_NORM = mpl.colors.BoundaryNorm(KMA_MMI_STEPS, KMA_MMI_CMAP.N)

KMA_MAP_EXTENT = [124.5, 132, 33, 39]

def draw_pga_cells_map(lat, lng, cell, *, figsize=(24, 24), stations_pga=None, distance_threshold=None, title=None):
    fig, ax = plt.subplots(1, 1, figsize=figsize, subplot_kw={
                           'projection': ccrs.PlateCarree()})

    ax.coastlines()
    ax.add_feature(cfeature.OCEAN)
    marker_ratio = figsize[0] / IMAGE_BASE_SIZE
    origin_marker_size = 36 * marker_ratio
    ax.plot(lng, lat, marker='*',
            markersize=origin_marker_size, color='r', zorder=10)
    ax.set_extent([lng - 2.5, lng + 2.5, lat - 2.5, lat + 2.5])

    if title is not None:
        ax.set_title(title)

    if stations_pga is not None:
        # Select stations only distance is less than threshold
        if distance_threshold is not None:
            stations_pga = stations_pga[stations_pga['distance'] <= distance_threshold]
        scatter_lng = stations_pga['lng'].values
        scatter_lat = stations_pga['lat'].values
        pgas = stations_pga['pga'].values
        scatter_order = np.argsort(pgas)
        ax.scatter(scatter_lng[scatter_order], scatter_lat[scatter_order],
                   c=pgas[scatter_order], s=40, zorder=5,
                   cmap = KMA_MMI_CMAP, norm = KMA_MMI_NORM, edgecolors = 'black',
                   transform = ccrs.PlateCarree())

    for k, v in cell.items():
        h_geom=h3.h3_to_geo_boundary(h = k, geo_json = True)
        boundary_child=geometry.Polygon(h_geom)

        i=1
        for lhs, rhs in zip(KMA_MMI_STEPS[:-1], KMA_MMI_STEPS[1:]):
            if lhs < v < rhs:
                break
            i += 1

        if i <= 2 or i >= 10:
            continue

        rgba=KMA_MMI_CMAP(i - 1)
        chex=mpl.colors.rgb2hex(rgba)

        centroid_lat, centroid_lng=h3.h3_to_geo(k)

        dist_between=gps2dist_azimuth(
            lat, lng, centroid_lat, centroid_lng)[0]
        dist_between /= 1000.

        flag_draw = True
        if distance_threshold is not None:
            if dist_between >= distance_threshold:
                flag_draw = False

        if flag_draw:
            ax.fill(*boundary_child.exterior.coords.xy, color=chex,
                    facecolor=chex, edgecolor='k', alpha=1)
            ax.text(x=boundary_child.centroid.x - .03,
                    y=boundary_child.centroid.y,
                    s=f'{i}',
                    fontsize=10, c='w', weight="bold")

    return fig, ax


def draw_pga_cells_map_v2(lat, lng, cell, *, figsize=(4, 4), stations_pga=None, distance_threshold=None, title=None):
    fig, ax = plt.subplots(1, 1, figsize=figsize, subplot_kw={
                           'projection': ccrs.PlateCarree()})

    ax.coastlines(linewidth=0.5)
    # Draw state boundary
    ax.add_feature(cfeature.STATES, linestyle=':', zorder=2, linewidth=0.5)
    marker_ratio = figsize[0] / IMAGE_BASE_SIZE
    origin_marker_size = 36 * marker_ratio
    ax.plot(lng, lat, marker='*',
            markersize=origin_marker_size, color='b', zorder=10)
    ax.set_extent(KMA_MAP_EXTENT)

    if title is not None:
        ax.set_title(title)

    if stations_pga is not None:
        # Select stations only distance is less than threshold
        if distance_threshold is not None:
            stations_pga = stations_pga[stations_pga['distance'] <= distance_threshold]
        scatter_lng = stations_pga['lng'].values
        scatter_lat = stations_pga['lat'].values
        pgas = stations_pga['pga'].values
        scatter_order = np.argsort(pgas)
        ax.scatter(scatter_lng[scatter_order], scatter_lat[scatter_order],
                   c=pgas[scatter_order], s=40, zorder=5,
                   cmap = KMA_MMI_CMAP, norm = KMA_MMI_NORM, edgecolors = 'black',
                   transform = ccrs.PlateCarree())

    for k, v in cell.items():
        h_geom=h3.h3_to_geo_boundary(h = k, geo_json = True)
        boundary_child=geometry.Polygon(h_geom)

        i=1
        for lhs, rhs in zip(KMA_MMI_STEPS[:-1], KMA_MMI_STEPS[1:]):
            if lhs < v < rhs:
                break
            i += 1

        if i <= 2 or i >= 10:
            continue

        rgba=KMA_MMI_CMAP(i - 1)
        chex=mpl.colors.rgb2hex(rgba)

        centroid_lat, centroid_lng=h3.h3_to_geo(k)

        dist_between=gps2dist_azimuth(
            lat, lng, centroid_lat, centroid_lng)[0]
        dist_between /= 1000.

        flag_draw = True
        if distance_threshold is not None:
            if dist_between >= distance_threshold:
                flag_draw = False

        if flag_draw:
            ax.fill(*boundary_child.exterior.coords.xy, color=chex,
                    facecolor=chex, edgecolor='k', zorder=1, linewidth=0.5)

    return fig, ax
