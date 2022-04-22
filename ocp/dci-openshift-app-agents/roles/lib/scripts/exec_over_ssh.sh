nodename=$1
cmd=$2
ssh_options="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
ip_addr=$(oc get node ${nodename} -o json | jq -r '.status.addresses[] | select(.type=="InternalIP") | .address')
ssh_output=$(ssh ${ssh_options} core@${ip_addr} "$cmd")
echo "${ssh_output}"

