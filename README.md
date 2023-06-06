# intel-test-harness

This incubation repository is intended to be a collection of ansible scripts to setup a test enviroment for Intel vRAN related technologies. At the time of this README file creation, the only test available is for the wireless FEC operator.

The following ansible roles are available:
- install-repo: install a private repo on the ansible script running host
- perf: install performance operator (obsolete) and setup performance profile
- sriov: install sriov operator and create virtual functions
- ptp: install ptp operator and config ptp4l and phc2sys (obsolete)
- fec: install wireless FEC operator and create virtual functions
- test-timer: deploy a FlexRAN pod and run timer mode test
- test-xran: deploy a FlexRAN pod and run xran test (incomplete)
