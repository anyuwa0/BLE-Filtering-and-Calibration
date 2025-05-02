#!/usr/bin/env python3

import asyncio
from bleak import BleakScanner
from datetime import datetime
import struct
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from kalman import KalmanFilter
from statistics import stdev

class RecordRSSI:
    def __init__(self):
        self.rssidict = {}

    def record_data(self, address, rssi):
        if address not in self.rssidict.keys():
            self.rssidict[address] = []

        self.rssidict[address].append(rssi)

    def rssi_values(self):
        return self.rssidict

def parse_ibeacon(manufacturer_data):
    """Parse iBeacon data from manufacturer data"""
    try:
        # iBeacon prefix (Apple's company ID + iBeacon type + reserved)
        prefix = manufacturer_data[:4]
        if prefix != b'\x4c\x00\x02\x15':
            return None
        
        # Extract UUID, major, minor, tx_power
        uuid = manufacturer_data[4:20].hex()
        major, minor, tx_power = struct.unpack('>HHb', manufacturer_data[20:25])
        
        return {
            'type': 'iBeacon',
            'uuid': uuid,
            'major': major,
            'minor': minor,
            'tx_power': tx_power
        }
    except:
        return None

def parse_eddystone(service_data):
    """Parse Eddystone beacon data from service data"""
    try:
        for uuid, data in service_data.items():
            if uuid.startswith('0000feaa-'):
                frame_type = data[0]
                if frame_type == 0x00:  # UID frame
                    return {
                        'type': 'Eddystone-UID',
                        'namespace': data[2:12].hex(),
                        'instance': data[12:18].hex(),
                        'tx_power': data[1]
                    }
                elif frame_type == 0x10:  # URL frame
                    return {
                        'type': 'Eddystone-URL',
                        'url': data[2:].decode('utf-8'),
                        'tx_power': data[1]
                    }
        return None
    except:
        return None

async def scan_for_beacons(recorder, beaconfilter, duration=10.0):
    """Scan for BLE beacons with detailed parsing"""
    print(f"Scanning for BLE beacons for {duration} seconds...")
    start_time = datetime.now()
    
    # Get both devices and advertisement data
    devices = await BleakScanner.discover(
        timeout=duration,
        return_adv=True
    )
    
    print("\nBeacon Detection Results:")
    print("=" * 50)
    print(f"Scan started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Scan duration: {duration} seconds")
    print(f"Total devices found: {len(devices)}")
    print("=" * 50 + "\n")

    for address in beaconfilter:
        device_found = False
        for device, advertisement_data in devices.values():
            if device.address == address:
                print(f"Device: {device.name if device.name else 'Unknown'}")
                print(f"  Address: {device.address}")
                print(f"  RSSI: {advertisement_data.rssi} dBm")
                print("-" * 40)
                device_found = True
                record.record_data(device.address, advertisement_data.rssi)  
                break

        if not device_found:
            print("Cannot find specific beacon")
            print(f"Address : {address}")
            print(f"RSSI: Null")
            print("-" * 40)
            record.record_data(address, None)
    
    '''for device, advertisement_data in devices.values():
        if device.address in beaconfilter:
            continue
        print(f"Device: {device.name if device.name else 'Unknown'}")
        print(f"  Address: {device.address}")
        print(f"  RSSI: {advertisement_data.rssi} dBm")
        record.record_data(device.address, advertisement_data.rssi)
        
        # Check for iBeacon
        if advertisement_data.manufacturer_data:
            for manufacturer_id, data in advertisement_data.manufacturer_data.items():
                ibeacon = parse_ibeacon(data)
                if ibeacon:
                    print("  Beacon Type: iBeacon")
                    print(f"    UUID: {ibeacon['uuid']}")
                    print(f"    Major: {ibeacon['major']}, Minor: {ibeacon['minor']}")
                    print(f"    TX Power: {ibeacon['tx_power']} dBm")
        
        # Check for Eddystone
        if advertisement_data.service_data:
            eddystone = parse_eddystone(advertisement_data.service_data)
            if eddystone:
                print(f"  Beacon Type: {eddystone['type']}")
                if eddystone['type'] == 'Eddystone-UID':
                    print(f"    Namespace: {eddystone['namespace']}")
                    print(f"    Instance: {eddystone['instance']}")
                elif eddystone['type'] == 'Eddystone-URL':
                    print(f"    URL: {eddystone['url']}")
                print(f"    TX Power: {eddystone['tx_power']} dBm")
        
        print("-" * 40)'''

def distanceCalculate(mac_address, mRSSI, txPower):
    test = KalmanFilter(0.008, stdev(rssi_dict[mac_address]))
    raw_distanceArray = []
    filtered_distanceArray = []
    for x in rssi_dict[mac_address]:
        if x is None:
            continue
        filteredValue = test.filter(x)
        print("Data:", x)
        print("Filtered Data: ", filteredValue)
        raw_distance = 10**((mRSSI - x)/(10*txPower))
        filtered_distance = 10**((mRSSI - filteredValue)/(10*txPower))
        raw_distanceArray.append(raw_distance)
        filtered_distanceArray.append(filtered_distance)

    return {
        "raw": raw_distanceArray,
        "filtered": filtered_distanceArray,
    }

def file_naming_convention(trial, scans, duration, distance):
    return f"{trial}-{distance}cm-{int(duration*scans)}secs-{int(duration)}secondIntervals.csv"

if __name__ == "__main__":
    try:
        record = RecordRSSI()
        filter_beacons = ['EC:81:F6:64:F0:86',
                          'E0:35:2F:E6:42:46',
                          'EC:BF:B3:25:D5:6C']
        scans = 60
        duration = 1.0
        distance = 10
        for i in range(scans):
            asyncio.run(scan_for_beacons(record, filter_beacons, duration=duration))
        rssi_dict = record.rssi_values()
        #b1 = distanceCalculate('EC:81:F6:64:F0:86', -59, 2)
        #b2 = distanceCalculate('E0:35:2F:E6:42:46', -65, 2)
        #b3 = distanceCalculate('EC:BF:B3:25:D5:6C', -62, 2)

        df = pd.DataFrame(rssi_dict)

        '''time1 = np.array([i for i in range(len(b1["raw"]))])
        rawvalues1 = np.array(b1["raw"])
        filteredvalues1 = np.array(b1["filtered"])

        time2 = np.array([i for i in range(len(b2["raw"]))])
        rawvalues2 = np.array(b2["raw"])
        filteredvalues2 = np.array(b2["filtered"])

        time3 = np.array([i for i in range(len(b3["raw"]))])
        rawvalues3 = np.array(b3["raw"])
        filteredvalues3 = np.array(b3["filtered"])

        fig, (ax1, ax2, ax3) = plt.subplots(3)
        ax1.plot(time1, rawvalues1)
        ax1.plot(time1, filteredvalues1, '-.')
        ax1.set_title("No.6")
        ax2.plot(time2, rawvalues2)
        ax2.plot(time2, filteredvalues2, '-.')
        ax2.set_title("No.4")
        ax3.plot(time3, rawvalues3)
        ax3.plot(time3, filteredvalues3, '-.')
        ax3.set_title("No. 2")
        plt.show()'''

        print(df)
        trial = 5
        file_name = file_naming_convention(trial, scans, duration, distance)
        df.to_csv(file_name, encoding='utf-8')

    except KeyboardInterrupt:
        print("\nScan interrupted by user")
    except Exception as e:
        print(f"An error occurred: {str(e)}")