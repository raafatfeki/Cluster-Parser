#!/bin/bash
#

declare -A checked_ssh=()
declare -a reachable_nodes=()
declare -a unreachable_nodes=()
SSH_TIMEOUT=1
set_ssh_passwordless=true
RESULTS_FILE="/tmp/ssh_results.$$"
LOCK_FILE="/tmp/ssh_check.lock"

check_ssh_and_share_key() {
	local node=$1
	local l_root_password=$2
	local l_ssh_timout=$3
	if [[ -z $l_ssh_timout ]]; then
		l_ssh_timout=2
	fi
	# Initialize to Unreacheable
	local status=1

	sshpass -p $l_root_password ssh -o ConnectTimeout=$l_ssh_timout -o StrictHostKeyChecking=no $node "exit" 2>/dev/null
	ret=$?
	if [[ $ret == 0 ]]; then
		# Check if public key already shared
		ssh -o BatchMode=yes -o ConnectTimeout=$l_ssh_timout -o StrictHostKeyChecking=no $node "exit" 2>/dev/null
		if [[ $? != 0 ]]; then
			echo "sshpass -p ****** ssh-copy-id -i ~/.ssh/id_rsa.pub $node"
			sshpass -p $l_root_password ssh-copy-id -i ~/.ssh/id_rsa.pub $node >/dev/null 2>&1
			# we need to ssh with the password one final time
			sshpass -p $l_root_password ssh -o ConnectTimeout=$l_ssh_timout -o StrictHostKeyChecking=no $node exit >/dev/null 2>&1
			echo "ssh-copy-id from $(hostname -s) to $node ..... Done"
		fi
		# Reacheable
		status=0
	elif [[ $ret == 5 ]]; then
		# Wrong Password
		status=2
	fi

	# Safely update the global array using file locking
	(
		flock -x 200
		echo "$node:$status" >> "$RESULTS_FILE"
	) 200>"$LOCK_FILE"
}

get_node_info()
{
	. /etc/os-release
	OS_VERSION=$ID$VERSION_ID

	if [[ -z `command -v opaconfig` ]]; then
		OPXSVERSION="0"
	else
		OPXSVERSION=$(opaconfig -V)
	fi

	CPU_Model=$(lscpu | grep ^"Model name" | awk -F":" '{print $2}' | xargs)
	Socket=$(lscpu | grep ^"Socket" | awk -F":" '{print $2}' | xargs)
	# CPU_Model=$(lscpu | grep ^"Frequency boost" | awk -F":" '{print $2}' | xargs)
	CorePerSocket=$(lscpu | grep ^"Core(s) per socket" | awk -F":" '{print $2}' | xargs)
	Threads=$(lscpu | grep ^"Thread(s) per" | awk -F":" '{print $2}' | xargs)

	orderedKeys=("OPA100" "CN-5000" "NV-MLX" "NV-GPUs" "AMD-GPUs")

	declare -A hardw=(["CN-5000"]="corn" ["OPA100"]="omni" ["NV-GPUs"]="nvidia" ["NV-MLX"]="infini" ["AMD-GPUs"]="Instinct")
	declare -A info=(["CN-5000"]="" ["OPA100"]="" ["NV-GPUs"]="" ["NV-MLX"]="" ["AMD-GPUs"]="")

	allInfoStr=""
	for hw in ${orderedKeys[@]}; do
		output=$(lspci | grep -i "${hardw[$hw]}" | cut -d " " -f1)
		nbDevice=$(echo $output | wc -w)
		info[$hw]+="$nbDevice-"
		if [[ ! -z $output ]]; then
			i=0
			for device in $output; do
				i=$((i+1))
				info[$hw]+="$i:NUMA"$(lspci -vvv -s $device | grep NUMA | awk '{print $3}')"/"
			done
		fi
		# allInfoStr+="${hw}:${info[$hw]}#"
		allInfoStr+="${hw}=$nbDevice#"
	done

	echo "OS=${OS_VERSION}#OPXS=$OPXSVERSION#CPU=$CPU_Model#CPUINFO=${Socket}x${CorePerSocket}x${Threads}#${allInfoStr}"
}


# read -s -p "Please enter your root password: " root_password < /dev/tty >&2
read -s -p "Please enter your root password: " root_password
echo
if [[ -z $root_password ]]; then
	echo "-- Error: Cannot proceed without root password -- Abort"
	exit
fi

# sinfo -N | awk '{print $1}' | sed /NODELIST/d | uniq > hostfile
# readarray -t nodesList < hostfile
# or
echo "Create Map of nodes"
mapfile -t nodesList < <(sinfo -N | awk '{print $1}' | sed /NODELIST/d | uniq)
# printf "%s\n" "${nodesList[@]}" > hostfile

echo "Set Passwordless ssh"
if $set_ssh_passwordless; then
	for node in ${nodesList[@]}; do
		if [[ -v checked_ssh[$node] ]]; then
			continue
		fi
		check_ssh_and_share_key $node $root_password $SSH_TIMEOUT &
	done
	wait

	while IFS=':' read -r node status; do
		checked_ssh["$node"]="$status"
	done < "$RESULTS_FILE"

	for node in "${!checked_ssh[@]}"; do
		if [[ ${checked_ssh[$node]} == 0 ]]; then
			reachable_nodes+=($node)
		elif [[ ${checked_ssh[$node]} == 1 ]]; then
			unreachable_nodes+=($node)
		elif [[ ${checked_ssh[$node]} == 2 ]]; then
			wrong_password_nodes+=($node)
		fi
	done

	if [[ ${#unreachable_nodes[@]} != 0 ]]; then
			echo "---------------------------" 
			echo "List of ALL unreachable nodes:" 
			echo "---------------------------" 
			echo "${unreachable_nodes[@]}" 
			echo 
	fi

	if [[ ${#wrong_password_nodes[@]} != 0 ]]; then
			echo "---------------------------"
			echo "List of nodes with different password:"
			echo "---------------------------"
			echo "${wrong_password_nodes[@]}"
			echo
	fi
	printf "%s\n" "${reachable_nodes[@]}" > hostfile
else
	printf "%s\n" "${nodesList[@]}" > hostfile
fi

echo "Collect Nodes Info"
mkdir -p cluster_parser/data 2> /dev/null

if [[ $1 != "append" ]]; then
	rm -rf cluster_parser/data/nodesInfo.txt &> /dev/null
fi
pdsh -t 2 -w ^hostfile  "$(typeset -f get_node_info ); get_node_info;" &>> "cluster_parser/data/nodesInfo.txt"

