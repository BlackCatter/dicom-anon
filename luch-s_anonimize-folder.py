# -*- coding: utf-8 -*-

import argparse
import errno
import fnmatch
import os
import re
import tempfile
import shutil
import string
import unicodedata
import zipfile

import dicom
import dicom_anon

src_dir = ''
dst_dir = ''

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def find_files(directory, pattern):
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename

printable = string.printable.decode('utf-8') + u'АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя'
def remove_control_chars(s):
    return ''.join(c for c in s if c in printable)

def anonimize_dicom_folder(dicom_folder, dst_folder, patient_id, patient_name):
    print(patient_id)
    print(patient_name)
    da = dicom_anon.DicomAnon(quarantine='quarantine', audit_file='identity.db',
        modalities = ['us', 'cr', 'ct', 'mr', 'pr'], org_root='1.2.826.0.1.3680043.8.1008',
        whitelist='white_list.json', log_file=None, rename=False, profile='basic', overlay=False,
        force_tag_list={
            str(dicom.tag.Tag(0x10, 0x20)): patient_id,
            str(dicom.tag.Tag(0x10, 0x10)): patient_name
        })

    da.run(dicom_folder, dst_folder)

def anonimize_sub_dir(sub_dir):
    sub_dir_clean = remove_control_chars(sub_dir)

    sub_dir_path = os.path.join(src_dir, sub_dir)
    temp_dir_path = tempfile.mkdtemp()

    # Find all zip files in directory
    zip_files = find_files(sub_dir_path, '*.zip')

    split = sub_dir_clean.split('.', 1)
    nosology = split[0].strip().encode('utf-8')
    diagnosis = split[1].strip().encode('utf-8')

    # Unzip files
    for zip_file in zip_files:
        zip_ref = zipfile.ZipFile(zip_file, 'r')
        zip_file_name = os.path.basename(zip_file).split('.')[0]
        extract_dir = os.path.join(temp_dir_path, zip_file_name)
        zip_ref.extractall(extract_dir)
        anonimize_dicom_folder(extract_dir, os.path.join(dst_dir, sub_dir_clean), nosology, diagnosis)
        zip_ref.close()

    shutil.rmtree(temp_dir_path)

def anonimize_folder():
    # Make sure dst folder exists
    mkdir_p(dst_dir)

    # Get list of all subdirectories
    sub_dirs = [dI for dI in os.listdir(src_dir)]

    for sub_dir in sub_dirs:
        anonimize_sub_dir(sub_dir)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--src', type=str, required=True)
    #parser.add_argument('--dst', type=str, required=True)
    args = parser.parse_args()

    src_dir = unicode(args.src, 'utf-8')

    dst_dir = unicode(os.getenv('LOCALAPPDATA') + '\dicom_viewer\localArchive', 'utf-8')
    print(dst_dir)

    anonimize_folder()

