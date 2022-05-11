import pytest

def test_function(setup, pod, api_instance, testmac, l1, xran, namespace, timeout, norun, architecture_dir, test_helper, test):
    if norun:
        print("Exiting before starting l1 and testmac processes")
        return

    print('--------------------------------------------------------------' +
          '------------------\nRunning test: ' + test + '\n----------' +
          '--------------------------------------------------------------' +
          '--------')
        
    if xran:
        testfile = l1 + '/' + test
    else:
        testfile = testmac + '/' + architecture_dir + '/' + test
    # Run the test on the pod.
    success = test_helper.exec_tests(pod, api_instance, testmac, l1, testfile, xran, namespace, timeout, pod)
    assert success is True
