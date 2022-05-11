#!/usr/bin/python3

from cpu import CpuResource
import sys

PHYSTART_QUICK_DEFAULT = 'phystart 4 0 100007'

class ProcessTestfile:

    # A function to take the setcore maps in the config file and allocate
    # relevant cpus on the current machine, creating a new map and writing it
    # in place, always allocating siblings.
    #
    # References:
    #   https://stackoverflow.com/questions/38935169/convert-elements-of-a-list-into-binary
    #   https://stackoverflow.com/questions/21409461/binary-list-from-indices-of-ascending-integer-list
    @classmethod
    def update_testfile(cls, rsc, testfile, phystart_quick):
        file_changed = False
        print('Processing testfile: %s' % testfile)
        try:
            f = open(testfile, 'r')
            cfg = list(f)
            f.close()
        except:
            sys.exit("can't open %s" %(cfg))
        line_index = 0
        for line in cfg:
            if 'setcore' in line:
                setcore_index = line.index('setcore')
                # The number of cpus (cores or threads, depening on hyperthreading, needed.)
                # Take the string, convert to hex, convert to binary, count the 1s.
                num_cpus = (bin(int(line[setcore_index + len('setcore'):].strip(), 16))[2:]).count('1')
                # Create the hex representation and replace the old setcore
                new_setcore_hex = ' ' + rsc.get_free_siblings_mask(num_cpus) + '\n'
                cfg[line_index] = line.replace(line[setcore_index + len('setcore'):], new_setcore_hex)
                file_changed = True
            elif phystart_quick and 'phystart' in line:
                phystart_index = line.index('phystart')
                cfg[line_index] = line.replace(line[phystart_index:], PHYSTART_QUICK_DEFAULT)
                file_changed = True

            line_index += 1

        if file_changed:
            # Write the new configuration to the same file.
            try:
                f = open(testfile, 'w')
                f.writelines(cfg)
            except:
                sys.exit("can't write %s" %(cfg))
            print('Updated testfile written.')
            f.close()
