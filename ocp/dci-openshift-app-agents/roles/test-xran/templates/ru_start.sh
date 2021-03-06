#!/bin/sh
set -eu

echo "updating cpu setting in {{orancfg_dir}}/oru/usecase_ru.cfg"

cpu_cache_dir=$(mktemp -d)

isolated_cpus=$(cat /sys/devices/system/cpu/isolated)
if [[ -z "${isolated_cpus}" ]]; then
    echo "no isolated_cpus on kernel cmdline, use default Cpus_allowed_list"
    egrep 'Cpus_allowed_list:' /proc/self/status > ${cpu_cache_dir}/procstatus
else
    echo "found isolated_cpus on kernel cmdline"
    echo "Cpus_allowed_list: ${isolated_cpus}" > ${cpu_cache_dir}/procstatus 
fi

PYTHON=python3
#core=$(${PYTHON} cpu_cmd.py --proc=${cpu_cache_dir}/procstatus --dir ${cpu_cache_dir} allocate-core)
#sed -i -r "s/^(ioCore)=.*/\1=${core}/" {{orancfg_dir}}/oru/usecase_ru.cfg

cpumask=$(${PYTHON} cpu_cmd.py --proc=${cpu_cache_dir}/procstatus --dir ${cpu_cache_dir} allocate-cpu-mask 2)
sed -i -r "s/^(ioWorker)=.*/\1=${cpumask}/" {{orancfg_dir}}/oru/usecase_ru.cfg

echo "cpu setting updated"

/bin/rm -rf ${cpu_cache_dir}

echo "update sriov string in run_o_ru.sh"
sed -i -r "s/(.*vf_addr_o_xu_a).*/\1 \"{{oru_sriov_str}}\"/" {{orancfg_dir}}/oru/run_o_ru.sh

echo "update config_file_o_ru.dat"
sed -i -r "s/^ruMac0=.*/ruMac0=00:11:22:33:00:01/" {{orancfg_dir}}/oru/config_file_o_ru.dat
sed -i -r "s/^ruMac1=.*/ruMac1=00:11:22:33:00:11/" {{orancfg_dir}}/oru/config_file_o_ru.dat
sed -i -r "s/^c_plane_vlan_tag=.*/c_plane_vlan_tag=10/" {{orancfg_dir}}/oru/config_file_o_ru.dat
sed -i -r "s/^u_plane_vlan_tag=.*/u_plane_vlan_tag=20/" {{orancfg_dir}}/oru/config_file_o_ru.dat

echo "starting ru"

ru_cmd="cd {{flexran_dir}}; source ./set_env_var.sh -d; cd {{orancfg_dir}}/oru; ./run_o_ru.sh"

tmux kill-session -t ru 2>/dev/null || true
sleep 1
tmux new-session -s ru -d "${ru_cmd}" 
sleep 1
if ! tmux ls | grep ru; then
    echo "failed to start ru"
    exit 1
else
    echo "ru started"
fi

