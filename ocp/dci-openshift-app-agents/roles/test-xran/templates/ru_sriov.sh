#!/bin/sh
bind_driver () {
    local driver=$1
    local pci=$2
    local original_path=$(realpath /sys/bus/pci/devices/${pci}/driver)
    local new_path=/sys/bus/pci/drivers/${driver}
    if [[ ! -e ${new_path}/${pci} ]]; then
        echo ${pci} > ${original_path}/unbind  || true
        echo ${driver} > /sys/bus/pci/devices/${pci}/driver_override  || true
        echo ${pci} > ${new_path}/bind  || true
        if [[ ! -e ${new_path}/${pci} ]]; then
            echo "failed to bind ${pci} to ${new_path}"
            exit 1
        fi
    fi
}

modprobe vfio-pci
echo 2 > /sys/class/net/{{ru_sriov_int}}/device/sriov_numvfs
ip link set dev {{ru_sriov_int}} vf 0 vlan 10 mac 00:11:22:33:00:01 spoofchk off
ip link set dev {{ru_sriov_int}} vf 1 vlan 20 mac 00:11:22:33:00:11 spoofchk off
vfs_str=""
for v in 0 1; do
    vf_pci=$(realpath /sys/class/net/{{ru_sriov_int}}/device/virtfn${v} | awk -F '/' '{print $NF}')
    bind_driver vfio-pci ${vf_pci}
    if [[ -z "${vfs_str}" ]]; then
        vfs_str=${vf_pci}
    else
        vfs_str="${vfs_str},${vf_pci}"
    fi
done

echo "${vfs_str}"

