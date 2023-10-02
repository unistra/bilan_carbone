#!/usr/bin/env python
import argparse
import csv
from datetime import datetime
import os

from pyrfc import Connection


FIELDS = {
    'FRAMEDATA': {
        'fields': ('DEP_DATE', 'ARR_DATE', 'CUSTOMER', 'LOCATION', 'COUNTRY', 'T_SCHEMA',),
    },
    'STATUS': {
        'fields': ('APPROVED', 'APPR_TXT', 'TRAN_FI', 'ACC_TEXT',),
    },
    'AMOUNTS': {
        'fields': ('TRIPNO', 'CURRENCY', 'SUM_REIMBU', 'SUM_ADVANC', 'SUM_PAYOUT', 'SUM_PAIDCO', 'TRIP_TOTAL',
                   'PD_FOOD', 'PD_HOUSING', 'PD_MILEAGE', 'TXF_FOOD', 'PD_POCKET_MON', 'PD_PUB_TRANS',
                   'PD_LOC_TRANS', 'TAXCOMP',),
    },
    'COSTDIST_TRIP': {
        'fields': ('PERC_SHARE', 'COMP_CODE', 'CO_AREA', 'COSTCENTER', 'WBS_ELEMT', 'FUNDS_CTR',),
    },
    'EMP_INFO': {
        'fields': ('PERNR', 'ENAME', 'PERS_AREA',),
    },
    'MILEAGE': {
        'fields': ('KEY_MILE', 'M_TOTAL', 'LIC_PLAT', 'VEH_TYPE', 'VEH_CLAS', 'LOC_FROM', 'LOC_TO',),
        'times': 10,
    },
    'RECEIPTS': {
        'fields': ('RECEIPTNO', 'EXP_TYPE', 'REC_AMOUNT', 'REC_CURR', 'LOC_AMOUNT', 'LOC_CURR'),
        'times': 10,
    },
    'STOPOVER': {
        'fields': ('KEY_STOP', 'DEP_DATE', 'ARR_DATE', 'CUSTOMER', 'LOCATION', 'COUNTRY'),
        'times': 10,
    },
    'DEPART': {
        'fields' : ('DEPAR', 'ARRVL', 'ZZDEPART',),
    }
}
AUTHORIZED_EXP_TYPES = ('BAT', 'BATP', 'SNCF', 'TCOM', 'TRN', 'TRNP' ,'VADM', 'VOL', 'VOLP', 'LOC', 'LOCP')


def result_to_data(result, fields):
    try:
        return dict(zip(fields, (x.strip() for x in result['DATA'][0]['WA'].split('|'))))
    except Exception:
        return {}


def filter_exp_types(data):
    receipts = data['RECEIPTS']
    data['RECEIPTS'] = [r for r in receipts if r['EXP_TYPE'] in AUTHORIZED_EXP_TYPES]


def write_headers():
    headers1, headers2 = [], []
    for group, info in FIELDS.items():
        times = info.get('times', 1)
        fields = info.get('fields', [])
        for i in range(times):
            headers1.extend([f'{group}{i + 1 if times > 1 else ""}'] * len(fields))
            headers2.extend(fields)
    return headers1, headers2


def write_entry(entry):
    entry_result = []
    for group, info in FIELDS.items():
        times = info.get('times', 1)
        data = entry[group]
        data = data if isinstance(data, list) else [data]
        fields_nb = len(info['fields'])
        for i in range(times):
            try:
                record = data[i]
                entry_result.extend([record[f] for f in info['fields']])
            except IndexError:
                entry_result.extend([''] * fields_nb)
                continue
    return entry_result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--ahost')
    parser.add_argument('-s', '--sysnr', default='00')
    parser.add_argument('-c', '--client')
    parser.add_argument('-u', '--user')
    parser.add_argument('-p', '--password')
    parser.add_argument('input_file')
    args = parser.parse_args()

    filename = f"bilan_carbone_{datetime.strftime(datetime.now(), '%Y%m%d%H%M%S')}.csv"

    with Connection(
            ashost=args.ahost,
            sysnr=args.sysnr,
            client=args.client,
            user=args.user,
            passwd=args.password
        ) as conn, \
         open(args.input_file) as fh_reader, \
         open(filename, 'w') as fh_writer:
        reader = csv.DictReader(fh_reader, delimiter=',')
        writer = csv.writer(fh_writer)
        writer.writerows(write_headers())

        for row in reader:
            employee_number = row['EMPLOYEENUMBER']
            trip_number = row['TRIPNUMBER']

            trip_result = conn.call('BAPI_TRIP_GET_DETAILS', EMPLOYEENUMBER=employee_number, 
                                    TRIPNUMBER=trip_number)
            filter_exp_types(trip_result)

            head_fields = ('DEPAR', 'ARRVL')
            head_result = conn.call('RFC_READ_TABLE', QUERY_TABLE='PTRV_HEAD',
                                    FIELDS=[{'FIELDNAME': f} for f in head_fields], DELIMITER='|',
                                    OPTIONS=[
                                        {'TEXT': f"PERNR LIKE '{employee_number.zfill(8)}'"},
                                        {'TEXT': "AND"},
                                        {'TEXT': f"REINR LIKE '{trip_number.zfill(10)}'"},
                                    ])
            trip_result.setdefault('DEPART', {}).update(result_to_data(head_result, head_fields))

            info_fields = ('ZZDEPART',)
            info_result = conn.call('RFC_READ_TABLE', QUERY_TABLE = 'ZSIFACMIS_PTK99T',
                                    FIELDS=[{'FIELDNAME': f} for f in info_fields], DELIMITER='|',
                                    OPTIONS=[
                                        {'TEXT': f"PERNR_D LIKE '{employee_number.zfill(8)}'"},
                                        {'TEXT': "AND"},
                                        {'TEXT': f"REINR LIKE '{trip_number.zfill(10)}'"},
                                    ])
            trip_result.setdefault('DEPART', {}).update(result_to_data(info_result, info_fields))
            writer.writerow(write_entry(trip_result))

        print(f'Fichier {filename} généré')
