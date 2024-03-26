
import pandas as pd
import numpy as np
from io import StringIO
import os
import configparser
from dataclasses import dataclass
import zipfile


@dataclass
class Channel:
    noise: float
    pathloss: str
    interference: str
    area: tuple[int, int]


    def to_ini(self):
        config = configparser.ConfigParser()
        config['channel'] = {
            'noise': str(self.noise),
            'pathloss': self.pathloss,
            'interference': self.interference,
            'area_width': str(self.area[0]),
            'area_height': str(self.area[1])
        }
        with StringIO() as strio:
            config.write(strio)
            strio.seek(0)
            return strio.read()


class NetworkData:
    def __init__(self):
        self.ues = pd.DataFrame()
        self.gnbs = pd.DataFrame()
        self.conns = pd.DataFrame()
        self.channel = Channel(0, 'None', 'None', (0, 0))


    def load(name, force_init=False):
        if not force_init:
            zipname = name + '.5gn.zip'
            if os.path.exists(zipname):
                print(f'Reading from {zipname}...')
                return NetworkData._load_zip(zipname)
        
        ininame = name + '.5gn.ini'
        if os.path.exists(ininame):
            print(f'Reading from {ininame}...')
            return NetworkData._load_ini(ininame)
        

    def _load_ini(name):
        config = configparser.ConfigParser()
        config.read(name)
        net = NetworkData()

        net.channel = NetworkData._load_channel_info(net, config['channel'])

        net.ues['x'], net.ues['y'] = NetworkData._gen_positions(net.channel, config['ues.pos'])
        net.ues['id'] = net.ues.index
        net.ues['max_power'] = float(config['ues']['max_power'])

        net.gnbs['x'], net.gnbs['y'] = NetworkData._gen_positions(net.channel, config['gnbs.pos'])
        net.gnbs['id'] = net.gnbs.index

        net._gen_connections()

        return net


    def _load_zip(name):
        with zipfile.ZipFile(name, 'r') as zip_file:
            net = NetworkData()
            net.ues = pd.read_csv(zip_file.open('ues.csv'))
            net.gnbs = pd.read_csv(zip_file.open('gnbs.csv'))
            net.conns = pd.read_csv(zip_file.open('conns.csv'))
            parser = configparser.ConfigParser()
            inistr = zip_file.read('channel.ini').decode('utf-8')
            parser.read_string(inistr)
            net.channel = NetworkData._load_channel_info(net, parser['channel'])
            return net


    def _load_channel_info(net, data):
        return Channel(
            float(data['noise']),
            data['pathloss'],
            data['interference'],
            (int(data['area_width']), int(data['area_height'])))


    def _gen_positions(channel, pos):
        if pos['method'] == 'grid':
            return grid(
                *channel.area,
                int(pos['rows']), int(pos['cols']))
        elif pos['method'] == 'scatter':
            return scatter(
                *channel.area,
                float(pos['density']))
        

    def _gen_connections(self):
        self.conns = self.ues.merge(self.gnbs, 'cross', suffixes=('_ue', '_gnb'))


    def save(self, name):
        zipname = name + '.5gn.zip'
        with zipfile.ZipFile(zipname, 'w', compression=zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('ues.csv', self.ues.to_csv(index=False))
            zip_file.writestr('gnbs.csv', self.gnbs.to_csv(index=False))
            zip_file.writestr('conns.csv', self.conns.to_csv(index=False))
            zip_file.writestr('channel.ini', self.channel.to_ini())


def scatter(width, height, density):
    x = np.random.uniform(0, width, int(density * width * height))
    y = np.random.uniform(0, height, int(density * width * height))
    return x, y


def grid(width, height, rows, cols):
    rad_x = width / (2 * cols)
    rad_y = height / (2 * rows)
    x = np.repeat(np.linspace(rad_x, width - rad_x, cols), rows)
    y = np.tile(np.linspace(rad_y, height - rad_y, rows), cols)
    return x, y
