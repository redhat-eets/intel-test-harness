#!/bin/sh

set -eu

print_usage() {
    declare -A arr
    arr+=( ["vfio"]="bind VFs to the vfio-pci driver"
           ["iavf"]="bind VFs to the iavf driver"
         )
    echo "Usage:"
    echo ""
    for key in ${!arr[@]}; do
        printf '%-15s: %s\n' "$key" "${arr[$key]}"
    done
    exit 1
}

get_pci_str() {
    pci_str=$(env | sed  -r -n 's/^PCIDEVICE_OPENSHIFT_IO.*=(.*)/\1/p' | sed 's/,/ /g')
    if [ -z "${pci_str}" ]; then
       echo "No VF is set via PCIDEVICE_OPENSHIFT_IO, is this a openshift pod?"
       exit 1
    fi
}

bind_driver () {
    driver=$1

    get_pci_str

    for pci in ${pci_str}; do
        original_path=$(realpath /sys/bus/pci/devices/${pci}/driver)
        new_path=/sys/bus/pci/drivers/${driver}
        if [[ ! -e ${new_path}/${pci} ]]; then
             echo ${pci} > ${original_path}/unbind  || true
             echo ${driver} > /sys/bus/pci/devices/${pci}/driver_override  || true
             echo ${pci} > ${new_path}/bind  || true
             if [[ ! -e ${new_path}/${pci} ]]; then
                 echo "failed to bind ${pci} to ${new_path}"
                 exit 1
             fi
        fi
    done
}

bind_vfio () {
    bind_driver vfio-pci
}


bind_iavf () {
    bind_driver iavf
}

if (( $# != 1 )); then
    print_usage
else
    ACTION=$1
fi

case "${ACTION}" in
    vfio)
        bind_vfio 
    ;;
    iavf)
        bind_iavf
    ;;
    *)
        print_usage
esac

