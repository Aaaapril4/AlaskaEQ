import itertools
import numpy as np
import scipy.optimize
import shelve
from pathlib import Path
from numba import jit
import pandas as pd
from pyproj import Proj

###################################### Traveltime based on Eikonal Timetable ######################################
@jit
def get_values_from_table(ir0, iz0, time_table):
    v = np.zeros_like(ir0, dtype=np.float64)
    for i in range(ir0.shape[0]):
        r = ir0[i, 0]
        z = iz0[i, 0]
        v[i, 0] = time_table[r, z]
    return v


@jit
def _interp(time_table, r, z, rgrid, zgrid, h):
    ir0 = np.floor((r - rgrid[0, 0]) / h).clip(0, rgrid.shape[0] - 2).astype(np.int64)
    iz0 = np.floor((z - zgrid[0, 0]) / h).clip(0, zgrid.shape[1] - 2).astype(np.int64)
    ir1 = ir0 + 1
    iz1 = iz0 + 1

    ## https://en.wikipedia.org/wiki/Bilinear_interpolation
    x1 = ir0 * h + rgrid[0, 0]
    x2 = ir1 * h + rgrid[0, 0]
    y1 = iz0 * h + zgrid[0, 0]
    y2 = iz1 * h + zgrid[0, 0]

    Q11 = get_values_from_table(ir0, iz0, time_table)
    Q12 = get_values_from_table(ir0, iz1, time_table)
    Q21 = get_values_from_table(ir1, iz0, time_table)
    Q22 = get_values_from_table(ir1, iz1, time_table)

    t = (
        1
        / (x2 - x1)
        / (y2 - y1)
        * (
            Q11 * (x2 - r) * (y2 - z)
            + Q21 * (r - x1) * (y2 - z)
            + Q12 * (x2 - r) * (z - y1)
            + Q22 * (r - x1) * (z - y1)
        )
    )

    return t


def traveltime(event_loc, station_loc, time_table, rgrid, zgrid, h, **kwargs):
    r = np.linalg.norm(event_loc[:, :2] - station_loc[:, :2], axis=-1, keepdims=True)
    z = event_loc[:, 2:] - station_loc[:, 2:]
    if (event_loc[:, 2:] < 0).any():
        print(f"Warning: depth is defined as positive down: {event_loc[:, 2:].detach().numpy()}")

    tt = _interp(time_table, r, z, rgrid, zgrid, h)

    return tt


##################################################################################################################


def calc_time(event_loc, station_loc, phase_type, vel={"p": 6.0, "s": 6.0 / 1.75}, eikonal=None, **kwargs):

    ev_loc = event_loc[:, :-1]
    ev_t = event_loc[:, -1:]

    if eikonal is None:
        v = np.array([vel[x] for x in phase_type])[:, np.newaxis]
        tt = np.linalg.norm(ev_loc - station_loc, axis=-1, keepdims=True) / v + ev_t
    else:
        tp = traveltime(
            ev_loc,
            station_loc[phase_type == "p"],
            eikonal["up"],
            eikonal["rgrid"],
            eikonal["zgrid"],
            eikonal["h"],
            **kwargs,
        )
        ts = traveltime(
            ev_loc,
            station_loc[phase_type == "s"],
            eikonal["us"],
            eikonal["rgrid"],
            eikonal["zgrid"],
            eikonal["h"],
            **kwargs,
        )

        tt = np.zeros(len(phase_type), dtype=np.float32)[:, np.newaxis]
        tt[phase_type == "p"] = tp
        tt[phase_type == "s"] = ts
        tt = tt + ev_t

    return tt


################################################ Location ################################################
def calc_td(r, z, phase_type, eikonal):
    t_d = np.zeros([phase_type.shape[0], 3])
    t_r_p = _interp(eikonal['dp_r'],
                    r[phase_type == 'p'], 
                    z[phase_type == 'p'], 
                    eikonal['rgrid'], 
                    eikonal['zgrid'], 
                    eikonal['h'])
    t_z_p = _interp(eikonal['dp_z'],
                    r[phase_type == 'p'], 
                    z[phase_type == 'p'], 
                    eikonal['rgrid'], 
                    eikonal['zgrid'], 
                    eikonal['h'])
    t_r_s = _interp(eikonal['ds_r'],
                    r[phase_type == 's'], 
                    z[phase_type == 's'], 
                    eikonal['rgrid'], 
                    eikonal['zgrid'], 
                    eikonal['h'])
    t_z_s = _interp(eikonal['ds_z'],
                    r[phase_type == 's'], 
                    z[phase_type == 's'], 
                    eikonal['rgrid'], 
                    eikonal['zgrid'], 
                    eikonal['h'])
    
    t_d[phase_type == "p"] = np.column_stack([t_r_p, t_r_p, t_z_p])
    t_d[phase_type == "s"] = np.column_stack([t_r_s, t_r_s, t_z_s])
    
    return t_d


def huber_loss_grad(event_loc, phase_time, phase_type, station_loc, weight, vel={"p": 6.0, "s": 6.0 / 1.75}, sigma=1, eikonal=None):
    event_loc = event_loc[np.newaxis, :]
    predict_time = calc_time(event_loc, station_loc, phase_type, vel, eikonal)
    t_diff = predict_time - phase_time
    
    l1 = np.squeeze((np.abs(t_diff) > sigma))
    l2 = np.squeeze((np.abs(t_diff) <= sigma))

    # loss
    loss = np.sum((sigma * np.abs(t_diff[l1]) - 0.5 * sigma**2) * weight[l1]) + np.sum(0.5 * t_diff[l2] ** 2 * weight[l2])
    J = np.zeros([phase_time.shape[0], event_loc.shape[1]])

    # gradient
    if eikonal is None:
        v = np.array([vel[p] for p in phase_type])[:, np.newaxis]
        dist = np.linalg.norm(event_loc[:, :-1] - station_loc, axis=-1, keepdims=True)
        J[:, :-1] = (event_loc[:, :-1] - station_loc) / (dist + 1e-6) / v
    else:
        r = np.linalg.norm(event_loc[:, :-2] - station_loc[:, :-1], axis=-1, keepdims=True)
        z = event_loc[:, -2:-1] - station_loc[:, -1:]
        d_x = np.column_stack([(event_loc[:, :-2] - station_loc[:, :-1]) / (r + 1e-6), 
                               np.ones_like(station_loc[:, 0:1])])
        t_d = calc_td(r, z, phase_type, eikonal)
        J[:, :-1] = d_x * t_d
    J[:, -1] = 1

    J_ = np.sum(sigma * np.sign(t_diff[l1]) * J[l1] * weight[l1], axis=0, keepdims=True) + np.sum(
        t_diff[l2] * J[l2] * weight[l2], axis=0, keepdims=True
    )

    return loss, J_


def calc_loc(
    phase_time,
    phase_type,
    station_loc,
    weight,
    event_loc0,
    eikonal=None,
    vel={"p": 6.0, "s": 6.0 / 1.75},
    bounds=None,
    max_iter=100,
    convergence=1e-6,
    depth_slice=1
): 
    if bounds != None:
        depths = np.linspace(bounds[2][0], bounds[2][1], depth_slice+1)
        depths = [(depths[i], depths[i+1]) for i in range(len(depths)-1)]
    
    losses = np.zeros(depth_slice)
    locs = np.zeros([depth_slice, event_loc0.shape[0]])
    for i in range(len(depths)):
        bounds = (bounds[0], bounds[1], depths[i], bounds[3])
        opt = scipy.optimize.minimize(
            huber_loss_grad,
            np.squeeze(event_loc0),
            method="L-BFGS-B",
            jac=True,
            args=(phase_time, phase_type, station_loc, weight, vel, 1, eikonal),
            bounds=bounds,
            options={"maxiter": max_iter, "gtol": convergence, "iprint": -1},
        )
        losses[i] = opt.fun
        locs[i, :] = opt.x

    minindex = np.argmin(losses)

    return locs[minindex][np.newaxis, :], losses[minindex]


def convert_ev(event, t0):
    proj = Proj(f"+proj=sterea +lon_0={config['center'][0]} +lat_0={config['center'][1]} +units=km")
    event_loc = np.zeros_like(event)
    event_loc[:2] = proj(longitude = event[0], latitude = event[1])
    event_loc[2] = event[2]
    event_loc[3] = (pd.Timestamp(event[3]) - t0).total_seconds()
    return event_loc.astype(np.float64)


if __name__ == '__main__':
    #1_52006 252
    # ev = '1_52006'
    ev = '1_52336'

    t0 = pd.Timestamp(2009,12,1)
    config={
        "center":(-178, -19),
        "xlim_degree":[176,-172],
        "ylim_degree":[-24,-14],
        }
    proj = Proj(f"+proj=sterea +lon_0={config['center'][0]} +lat_0={config['center'][1]} +units=km")
    xd = proj(longitude=config["xlim_degree"][0], latitude=config["ylim_degree"][0])
    yd = proj(longitude=config["xlim_degree"][1], latitude=config["ylim_degree"][1])
    config["x(km)"] = [xd[0], yd[0]]
    config["y(km)"] = [xd[1], yd[1]]
    config["z(km)"] = (0, 800)
    config["bfgs_bounds"] = (
        (config["x(km)"][0] - 1, config["x(km)"][1] + 1),  # x
        (config["y(km)"][0] - 1, config["y(km)"][1] + 1),  # y
        (0, config["z(km)"][1] + 1),  # z
        (None, None),  # t
    )

    with shelve.open(r"eikonal/0_1680_0_800_1") as e:
        up = e['up']
        us = e['us']
        rgrid = e['rgrid']
        zgrid = e['zgrid']
        dp_r = e['dp_r']
        dp_z = e['dp_z']
        ds_r = e['ds_r']
        ds_z = e['ds_z']
    eikonal = {"up": up, "us": us, "rgrid": rgrid, "zgrid": zgrid, "h": 1, "dp_r": dp_r, "ds_r": ds_r, "dp_z": dp_z, "ds_z": ds_z}

    picks_all = pd.read_csv('tonga/test.csv')
    picks_all['timestamp'] = picks_all['timestamp'].apply(lambda x: pd.Timestamp(x))

    picks_test = picks_all[picks_all['event_id'] == ev]
    data = (picks_test['timestamp'] - t0).apply(lambda x: x.total_seconds()).to_numpy()[:, np.newaxis]
    phase_type = picks_test['type'].to_numpy()
    station_loc = picks_test[['x(km)', 'y(km)', 'z(km)']].to_numpy()
    weight = picks_test['prob'].to_numpy()[:, np.newaxis]
    event_loc0 = np.array([0, 0, 0, 0])
    calc_loc(data, phase_type, station_loc, weight, event_loc0, eikonal, bounds=config['bfgs_bounds'], depth_slice=1)
    calc_loc(data, phase_type, station_loc, weight, event_loc0, eikonal, bounds=config['bfgs_bounds'], depth_slice=3)