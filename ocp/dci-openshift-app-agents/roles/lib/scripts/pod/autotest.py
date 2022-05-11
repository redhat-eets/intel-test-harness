#!/usr/bin/python3
# This is based on https://gist.github.com/amadorpahim/3062277

import os,re,copy,sys,getopt,yaml
import xml.etree.ElementTree as ET
from cpu import CpuResource

from read_yaml_write_xml import CfgData
from process_testfile import ProcessTestfile

procstatus = '/proc/self/status'

class Setting:
    @classmethod
    def update_cfg_files(cls, cfg: str, cpursc: CpuResource):
    # use self.cfg info to update the config files: phycfg_timer.xml, testmac_cfg.xml
    # assume these config files exist under the current directory
    # reference https://docs.google.com/document/d/1CLlfh2pt2eOxwus0gnOXuAnGT9yRYVu0Rrr8wTAP_0I/edit?usp=sharing
        CfgData.process_cfg_xml(cfg, cpursc)

    # Call the update_tesfile function of the ProcessTestfile class (in
    # process_testfile.py).
    @classmethod
    def update_testfile(cls, rsc, testfile, phystart_quick=False):
        ProcessTestfile.update_testfile(rsc, testfile, phystart_quick)

def main(name, argv):
    nosibling = False
    phystart = False
    cfg = None
    testfile = None
    testdir = None
    helpstr = name + " --testfile=<testfile path>"\
                     " --cfg=<yaml_cfg>"\
                     " --nosibling"\
                     " --phystart"\
                     " --testdir=<testdir path>" \
                     "\n"
    try:
        opts, args = getopt.getopt(argv,"h",["testfile=", "cfg=", "nosibling", "phystart", "testdir="])
    except getopt.GetoptError:
        print(helpstr)
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print(helpstr)
            sys.exit()
        elif opt in ("--testfile"):
            testfile = arg
        elif opt in ("--cfg"):
            cfg = arg
        elif opt in ("--nosibling"):
            nosibling = True
        elif opt in ("--phystart"):
            phystart = True
        elif opt in ("--testdir"):
            testdir = arg

    if cfg is None:
        print("Please specify a config file with --cfg")
        sys.exit(2)

    status_content = open(procstatus).read().rstrip('\n')
    cpursc = CpuResource(status_content, nosibling)

    # Hack: The flexran code only supports a maximum of 64 cpus.
    # See /opt/flexran/source/auxlib/cline/aux_cline.c
    # (function cline_covert_hex_2_dec)
    # As a workaround, remove any cpus numbered 64 or higher.
    to_remove = []
    for cpu in cpursc.available:
        if cpu >= 64:
           to_remove.append(cpu)
    for cpu in to_remove:
        cpursc.remove(cpu)
    if to_remove:
        print("Removed cpus %s from available list due to flexran limitation." % to_remove)

    # Note: update_cfg_files must always be called in order to remove any common cpus
    # from cpursc before cpursc is used by update_testfile below.
    Setting.update_cfg_files(cfg, cpursc)
    print('Test config updated from: %s' % cfg)

    if testfile is not None:
        # NOTE: QUICK PHYSTART NOTED BY TRUE, CHANGE FOR REAL TESTS.
        Setting.update_testfile(cpursc, testfile, phystart)
        print('Test file updated: %s' % testfile)

    if testdir is not None:
        for root, dirs, files in os.walk(testdir):
            for file in files:
                if file.endswith(".cfg"):
                    testfile = os.path.join(root, file)
                    Setting.update_testfile(cpursc, testfile)
        print('Test directory updated: %s' % testdir)

if __name__ == "__main__":
     main(sys.argv[0], sys.argv[1:])
