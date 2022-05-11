import pytest

from kubernetes import client, config
from openshift.dynamic import DynamicClient
from kubernetes.client import Configuration
from kubernetes.client.api import core_v1_api
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream

import datetime
import os
import re
import subprocess
import sys
import time
import yaml

DEBUG = False
NORUN = False
RESULTS_DIR = 'results'

#@pytest.fixture (scope="module")
#def oc_client():
#    k8s_client = config.new_client_from_config()
#    return DynamicClient(k8s_client)

#@pytest.fixture
#def setup()

# TODO: 
# Add pytest_addoption for passing arguments: https://stackoverflow.com/questions/40880259/how-to-pass-arguments-in-pytest-by-command-line

def pytest_addoption(parser):
    parser.addoption('--pod', action='store', type=str, required=True, help='the name of the pod')
    parser.addoption('--dest', action='store', type=str, required=False,  help='the destination directory on the pod')
    parser.addoption('--cfg', action='store', type=str, required=True, help='the configuration file to update threads, define paths, and get tests')
    parser.addoption('--no_sibling', action='store_true', required=False, default=False, help='optional no_sibling flag')
    parser.addoption('--file', action='append', type=str, required=False, help='the file(s) to be copied to the pod')
    parser.addoption('--dir', action='append', type=str, required=False, help='the directory(ies) to be copied to the pod (requires rsync or tar on pod)')
    parser.addoption('--xran', action='store_true', required=False, default=False, help='a flag indicating xran mode')
    parser.addoption('--phystart', action='store_true', required=False, default=False, help='a flag indicating quick phystart in xran mode (phystart 4 0 100007)')
    parser.addoption('--namespace', action='store', type=str, required=False, default='default', help='the namespace of the pod')
    parser.addoption('--timeout', action='store', type=int, required=True, help='the timeout (in seconds) for the test')
    parser.addoption('--norun', action='store_true', required=False, default=False, help='do not run l1 or testmac processes - just update testcases')
    parser.addoption('--verbose_flexran', action='store_true', required=False, default=False, help='verbose output')
    parser.addoption('--test', action='store', required=True, help='the name of the test file to run')

@pytest.fixture(scope='session')
def pod(request):
    return request.config.option.pod
@pytest.fixture(scope='session')
def dest(request):
    return request.config.option.dest
@pytest.fixture(scope='session')
def cfg(request):
    return request.config.option.cfg
@pytest.fixture(scope='session')
def no_sibling(request):
    return request.config.option.no_sibling
@pytest.fixture(scope='session')
def files(request):
    return request.config.option.file
@pytest.fixture(scope='session')
def dirs(request):
    return request.config.option.dir
@pytest.fixture(scope='session')
def xran(request):
    return request.config.option.xran
@pytest.fixture(scope='session')
def phystart(request):
    return request.config.option.phystart
@pytest.fixture(scope='session')
def namespace(request):
    return request.config.option.namespace
@pytest.fixture(scope='session')
def timeout(request):
    return request.config.option.timeout
@pytest.fixture(scope='session')
def norun(request):
    global NORUN
    NORUN = request.config.option.norun
    return request.config.option.norun
@pytest.fixture(scope='session')
def verbose(request):
    global DEBUG
    DEBUG = request.config.option.verbose
    return request.config.option.verbose
@pytest.fixture(scope='session')
def test(request):
    return request.config.option.test

# A method to set up the testing.
@pytest.fixture
def setup(pod, api_instance, namespace, dest, files, dirs, cfg, xran, phystart, no_sibling, norun, verbose, architecture_dir, test_dir_list, l1, testmac, test):
    print(test)
    check_pod(pod, api_instance, namespace)
    if files:
        if dest:
            copy_files(namespace, pod, dest, files)
        else:
            print('--dest flag required if files are specified')
            exit(1)
    if dirs:
        if dest:
            copy_directories(namespace, pod, dest, dirs)
        else:
            print('--dest flag required if dirs are specified')
            exit(1)

    # fixtures? so they can be referenced from other fixtures
    #test_list = get_test_list(cfg)
    #architecture_dir = get_architecture_dir(cfg, xran)
    #test_dir_list = get_test_dir_list(cfg)
    #l1 = get_l1(cfg)
    #testmac = get_testmac(cfg)

    # Update the testfiles and xml configurations on the pod.
    #exec_updates(pod_name, api_instance, destination, testmac, l1, test_list, cfg,
    #             no_sibling, architecture_dir, xran, phystart, pod_namespace,
    #             test_dir_list)
    exec_updates(pod, api_instance, dest, testmac,
                 l1, cfg, no_sibling, architecture_dir, xran,
                 phystart, namespace, test_dir_list, test)

    time.sleep(30)
    
    yield

# A method to get the Kube configuration and return the API instance.
@pytest.fixture(scope='session')
def api_instance():
    config.load_kube_config()
    try:
        c = Configuration().get_default_copy()
    except AttributeError:
        c = Configuration()
        c.assert_hostname = False
    Configuration.set_default(c)
    core_v1 = core_v1_api.CoreV1Api()

    #return core_v1
    yield core_v1

# A method to check if the pod is running. Exit if it does not exist, as the
# assumption is that the pod will be running and configured for test before
# this script is called.
#@pytest.fixture
def check_pod(name, api_instance, namespace):
    resp = None
    try:
        resp = api_instance.read_namespaced_pod(name=name,
                                                namespace=namespace)
    except ApiException as e:
        if e.status != 404:
            print("Unknown error: %s" % e)
            exit(1)
    if not resp or resp.status.phase != 'Running':
        print("Pod %s does not exist. Exiting..." % name)
        exit(1)

    return

# A method to copy a list of files from the host to the pod at the passed
# destination. This is used to move the scripts, configuration files, etc. to
# the pod.
#@pytest.fixture
def copy_files(pod_namespace, pod_name, destination, files):
    print('\nCopying files to pod \'' + pod_namespace + "/" +  pod_name + '\':')
    for file in files:
        output = subprocess.check_output(
                ['oc', 'cp', file, pod_namespace + '/' + pod_name + ':' + destination])
        print(file)
    return

# A method to copy a list of directories from the host to the pod at the passed
# destination. This is used to move the scripts, configuration files, etc. to
# the pod.
# NOTE: Need to enable rsync on pod.
#@pytest.fixture
def copy_directories(pod_name, destination, directories):
    print('Copying directories to pod \'' + pod_namespace + "/" + pod_name + '\':')
    for directory in directories:
        output = subprocess.check_output(
                ['oc', 'rsync', directory, pod_namespace + '/' + pod_name + ':' + destination])
        print(directory)
    return

# A method to get the tests from the YAML file, taking in the path to the YAML
# config file and returning the list of tests.
@pytest.fixture
def test_list(cfg): #get_tests_from_yaml(cfg):
    try:
        f = open(cfg, 'r')
        config_yaml = yaml.safe_load(f)
        f.close()
    except:
        sys.exit("Can't open or parse %s" %(cfg))

    if 'Tests' in config_yaml and config_yaml['Tests'] is not None:
        return config_yaml['Tests']
    else:
        print('No tests in config...')
        return []

# A method to get the cpu architecture directory from the YAML file, taking in
# the path to the YAML config file and returning the directory. The xran flag
# is also passed in, as this does not apply to xran tests.
@pytest.fixture
def architecture_dir(cfg, xran): #get_architecture_from_yaml(cfg, xran):
    try:
        f = open(cfg, 'r')
        config_yaml = yaml.safe_load(f)
        f.close()
    except:
        sys.exit("Can't open or parse %s" %(cfg))

    if xran:
        print("No architecture directory required for xran tests")
        return
    else:
        if 'Arch_dir' in config_yaml:
            return config_yaml['Arch_dir']
        else:
            print('No architecture directory in config...')
            exit(1)

# A method to get the test directory from the YAML file, taking in
# the path to the YAML config file and returning the directory.
@pytest.fixture
def test_dir_list(cfg): #get_test_dir_list_from_yaml(cfg):
    try:
        f = open(cfg, 'r')
        config_yaml = yaml.safe_load(f)
        f.close()
    except:
        sys.exit("Can't open or parse %s" %(cfg))

    if 'Test_dirs' in config_yaml and config_yaml['Test_dirs'] is not None:
        return config_yaml['Test_dirs']
    else:
        print('No Test_dirs in config...')
        return []

# A method to get the l1 directory from the YAML file, taking in the path to
# the YAML config file and returning the path.
@pytest.fixture
def l1(cfg): #get_l1_from_yaml(cfg):
    try:
        f = open(cfg, 'r')
        config_yaml = yaml.safe_load(f)
        f.close()
    except:
        sys.exit("Can't open or parse %s" %(cfg))

    if 'Cfg_file_paths' in config_yaml:
        for index in config_yaml['Cfg_file_paths']:
            for config_name in config_yaml['Cfg_file_paths'][index]:
                if config_name[0:6] == 'phycfg':
                    if config_yaml['Cfg_file_paths'][index][config_name][-1] == '/':
                        return config_yaml['Cfg_file_paths'][index][config_name][:-1]
                    else:
                        return config_yaml['Cfg_file_paths'][index][config_name]
    else:
        print('No config files in config...')
        exit(1)

# A method to get the testmac directory from the YAML file, taking in the path
# to the YAML config file and returning the path.
@pytest.fixture
def testmac(cfg): #get_testmac_from_yaml(cfg):
    try:
        f = open(cfg, 'r')
        config_yaml = yaml.safe_load(f)
        f.close()
    except:
        sys.exit("Can't open or parse %s" %(cfg))

    if 'Cfg_file_paths' in config_yaml:
        for index in config_yaml['Cfg_file_paths']:
            for config_name in config_yaml['Cfg_file_paths'][index]:
                if config_name[0:7] == 'testmac':
                    if config_yaml['Cfg_file_paths'][index][config_name][-1] == '/':
                        return config_yaml['Cfg_file_paths'][index][config_name][:-1]
                    else:
                        return config_yaml['Cfg_file_paths'][index][config_name]
    else:
        print('No config files in config...')
        exit(1)

# A method which can run a list of commands on the pod.
#@pytest.fixture
def run_commands_on_pod(name, api_instance, commands, pod_namespace):
    exec_command = ['/bin/sh']
    resp = stream(api_instance.connect_get_namespaced_pod_exec,
                  name,
                  pod_namespace,
                  command=exec_command,
                  stderr=True, stdin=True,
                  stdout=True, tty=True,
                  _preload_content=False)

    while resp.is_open():
        if commands:
            c = commands.pop(0)
            print("Running command... %s\n" % c)
            resp.write_stdin(c + "\n")
            time.sleep(1)
            resp.write_stdin("\n")
        else:
            break

    resp.run_forever(5)
    output = resp.read_stdout(5)
    return output

# A method to execute updates to the testfiles and xml configurations on the
# pod.
#@pytest.fixture
def exec_updates(name, api_instance, destination, testmac,
                 l1, cfg, no_sibling, architecture_dir, xran,
                 phystart, pod_namespace, test_dir_list, test):

    # Install python modules in pod
    #commands = [
    #    'pip3 install lxml',
    #    'pip3 install dataclasses',
    #    "cd " + destination,
    #]

    # Is there a generic way to install these dependencies? VENV? pip3 freeze
    # NOTE: Moved to creation of container image
    #run_commands_on_pod(name, api_instance, commands, pod_namespace)
    
    # Update configuration and test config files in pod
    updated = []
    #for testfile in test_list:
    if test not in updated:
        if xran:
            full_testfile = l1 + '/' + test
        else:
            full_testfile = testmac + '/' + architecture_dir + '/' + test
        update_command = "./autotest.py" + " --testfile " + full_testfile + " --cfg " + cfg.split('/')[-1]

        if xran and phystart:
            update_command = update_command + ' --phystart'

        if no_sibling:
            update_command = update_command + ' --nosibling'

        commands = [
            update_command,
        ]

        output = run_commands_on_pod(name, api_instance, commands, pod_namespace)
        if "Test file updated" in output:
            if DEBUG:
                print(output)
            print("Finished updating test file %s on pod.\n" % full_testfile)
            updated.append(test)
        else:
            print(output)
            sys.exit(1)

    # Update configuration and test config files in a specified test directory in pod
    for test_dir in test_dir_list:
        update_command = "./autotest.py" + " --testdir " + test_dir + " --cfg " + cfg.split('/')[-1]

        if no_sibling:
            update_command = update_command + ' --nosibling'

        commands = [
            update_command,
        ]
        
        output = run_commands_on_pod(name, api_instance, commands, pod_namespace)
        if "Test directory updated" in output:
            if DEBUG:
                print(output)
            print("Finished updating test files in directory %s on pod.\n" % test_dir)
        else:
            print(output)
            sys.exit(1)

class Tests:
    # A method to execute the given test on the pod.
    @staticmethod
    def exec_tests(name, api_instance, testmac, l1, testfile, xran, pod_namespace, timeout_seconds, pod):
        # Calling exec interactively
        exec_command = ['/bin/sh']
        resp = stream(api_instance.connect_get_namespaced_pod_exec,
                      name,
                      pod_namespace,
                      command=exec_command,
                      stderr=True, stdin=True,
                      stdout=True, tty=True,
                      _preload_content=False)

        #commands = [
        #    "source /opt/flexran/auto/env.src",
        #    "cd " + l1,
        #]
        commands = [
            "cd " + l1,
        ]

        if xran:
            commands.append("unbuffer ./l1.sh -oru")
        else:
            commands.append("unbuffer ./l1.sh -e")

        while resp.is_open():
            if commands:
                c = commands.pop(0)
                print("Running command... %s\n" % c)
                resp.write_stdin(c + "\n")
                time.sleep(5)
                resp.write_stdin("\n")
            else:
                break
        # NOTE: This time might need adjusting, run_forever(5) ran into some
        #       crashing issues which we think have to do with timing.
        '''resp.run_forever(10)
        output = resp.read_stdout(timeout=timeout_seconds)
        output += resp.read_stdout(timeout=timeout_seconds)
        if "welcome" in output:
            print("l1app ready\n")
        else:
            print("L1 failed to start!\n")
            print(output)
            write_to_files(testfile, '', xran, l1, pod, output, '', pod_namespace)
            sys.exit(1)
        '''
        #resp.run_forever(5)
        output = ''
        last_update = 0
        l1_ready = False
        while resp.is_open():
            resp.run_forever(1)
            l1_update = resp.read_stdout(timeout=timeout_seconds)

            #print(l1_update)
            #print(last_update)
            #print(time.time())
            #print(timeout_seconds)
            #print('----------------')

            if l1_update not in output:
                last_update = time.time()
                output += l1_update
            elif time.time() - last_update >= timeout_seconds:
                print("TIMEOUT")
                timed_out = True
                break

            if "welcome" in output:
                print("l1app ready\n")
                l1_ready = True
                break
            resp.write_stdin('\n')

        if not l1_ready:
            print("L1 failed to start!\n")
            print(output)
            write_to_files(testfile, '', xran, l1, pod, output, '', pod_namespace)
            print("pod: Failed to start L1. Exiting...\n")
            sys.exit(1)

        testmac_resp = stream(api_instance.connect_get_namespaced_pod_exec,
                      name,
                      pod_namespace,
                      command=exec_command,
                      stderr=True, stdin=True,
                      stdout=True, tty=True,
                      _preload_content=False)
        #commands = [
        #    "source /opt/flexran/auto/env.src",
        #    "cd " + testmac,
        #    "./l2.sh --testfile=" + testfile,
        #]
        commands = [
            "cd " + testmac,
            "unbuffer ./l2.sh --testfile=" + testfile,
        ]


        while testmac_resp.is_open():
            if commands:
                c = commands.pop(0)
                print("Running command... %s\n" % c)
                testmac_resp.write_stdin(c + "\n")
                time.sleep(5)
                testmac_resp.write_stdin("\n")
            else:
                break

        l1_output = output
        
        output = ''
        last_update = 0
        testmac_ready = False
        while testmac_resp.is_open():
            testmac_resp.run_forever(1)
            testmac_update = testmac_resp.read_stdout(timeout=timeout_seconds)
            
            if testmac_update not in output:
                last_update = time.time()
                output += testmac_update
            elif time.time() - last_update >= timeout_seconds:
                print("TIMEOUT")
                timed_out = True
                break
            
            if "welcome" in output:
                print("Testmac ready\n")
                testmac_ready = True
                break

        if not testmac_ready:
            print("Testmac failed to start!\n")
            print(output)
            write_to_files(testfile, '', xran, l1, pod, l1_output, output, pod_namespace)
            sys.exit(1)

        print('Running tests...')

        testmac_output = ''

        last_update = time.time()
        timed_out = False
        while testmac_resp.is_open():
            testmac_resp.run_forever(1)
            testmac_output_update = testmac_resp.read_stdout(timeout=timeout_seconds)
            testmac_output = testmac_output + testmac_output_update
            l1_output = l1_output + resp.read_stdout(timeout=timeout_seconds)
            result = re.search(r"All Tests Completed.*\n", testmac_output)
            passed = re.search(r"FAIL 0 Tests.*\n", testmac_output)
            seg_fault = re.search(r"Segmentation Fault!*\n", testmac_output)
            core_os_terminal = re.search(r".*\#", testmac_output)

            if testmac_output_update:
                last_update = time.time()
            elif time.time() - last_update >= timeout_seconds:
                timed_out = True

            if result:
                result_dir = write_to_files(testfile, result, xran, l1, pod, l1_output, testmac_output, pod_namespace)
                break
            elif seg_fault or timed_out or core_os_terminal:
                if seg_fault:
                    print('Segmentation Fault in Testmac!\n')
                elif timed_out:
                    print('Testmac timed out without update!\n')
                elif core_os_terminal:
                    print('Testmac exited without finishing!\n')

                result_dir = write_to_files(testfile, result, xran, l1, pod, l1_output, testmac_output, pod_namespace)
                # The test fails
                return False
                #sys.exit(1)

        resp.write_stdin("exit\r\n")
        testmac_resp.write_stdin("exit\r\n")
        time.sleep(20)
        resp.close()
        testmac_resp.close()
        if not passed:
            print("Not all tests passed")
            return False
        # The test passes
        return True

@pytest.fixture
def test_helper():
    return Tests

# A method to write the stdout of l1 and testmac, as well as the results of the test, to files.
#@pytest.fixture
def write_to_files(testfile, result, xran, l1, pod_name, l1_output, testmac_output, pod_namespace):
    print('Checking directory status...')
    directory_exits = os.path.isdir(RESULTS_DIR)
    if not directory_exits:
        os.makedirs(RESULTS_DIR)
        print('Created results directory')
    else:
        print('Results directory exits')

    test_dir = RESULTS_DIR + '/' + (testfile.split('/')[-1]).split('.')[0]
    directory_exits = os.path.isdir(test_dir)
    if not directory_exits:
        os.makedirs(test_dir)
        print('Created ' + test_dir + ' directory')
    else:
        print(test_dir + ' directory exits')

    time_dir = test_dir + '/' + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    directory_exits = os.path.isdir(time_dir)
    if not directory_exits:
        os.makedirs(time_dir)
        print('Created ' + time_dir + ' directory')
    else:
        print(time_dir + ' directory exits')

    if result:
        print(result.group())
    print("Copying stat file (l1_mlog_stats.txt) to results directory...")

    if xran:
        mlog_path = l1.split('l1')[0] + 'l1' + '/l1_mlog_stats.txt'
    else:
        mlog_path = l1 + '/l1_mlog_stats.txt'
    try:
        copy_output = subprocess.check_output(
                ['oc', 'cp', pod_namespace + '/' + pod_name + ':' + mlog_path, "./" + time_dir + "/l1_mlog_stats.txt"])
    except Exception as e:
        print(e)
        print("Did not copy l1_mlog_stats.txt")
    #print(output)
    print("Writing l1 output (l1.txt) to results directory...")
    l1_out = open('./' + time_dir + '/l1.txt', 'w')
    out = l1_out.write(l1_output)
    l1_out.close()

    print("Writing testfile output (testmac.txt) to results directory...")
    test_output = open('./' + time_dir + '/testmac.txt', 'w')
    out = test_output.write(testmac_output)
    test_output.close()

    print("Pod: Writing Complete.")
    print("Result directory: " + time_dir)
    return time_dir

