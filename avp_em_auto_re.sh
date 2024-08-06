#! /bin/bash
# description: avp em module regress automatically

ARG_1=${1}
FILE_NAME=$(echo $(realpath ${0}) | awk -F '/' '{print $NF}')
DIRNAME=$(dirname $0)
AVP_FILE=${DIRNAME}/avp_em_set_conf.sh
ANP_PATH=/home/caros/em_anp/
PLAY_CONFIG=${ANP_PATH}conf/base/play_ebag.config
RECORD_CONFIG=${ANP_PATH}conf/base/record_ebag.config
RE_DIR=/home/caros/avp_new_data_$(date +"%m%d%H%M")/

# --- func color ---
function green(){
        echo -e "\033[;32m[INFO\t$(date +"%m/%d %H:%M") ${FILE_NAME}] $1 \033[0m"
}

function red(){
        echo -e "\033[;31m[ERROR\t$(date +"%m/%d %H:%M") ${FILE_NAME}] $1 \033[0m"
}

# --- func pre ---
function set_pre_conf() {
	if [ -f ${AVP_FILE} ]; then
		bash ${AVP_FILE}
	else
		red "No ${AVP_FILE} !\texit 0" && exit 0
	fi
}

function check_case_dir() {
	if [[ -d ${ARG_1} && -n ${ARG_1} ]]; then
		DATA_PATH=$(realpath ${ARG_1})/
		green "Origin_Datas_Dir: ${DATA_PATH}"
	else
		red "Usage: bash ${FILE_NAME} [path_to_em_cases]\nexit 0" && exit 0
	fi
}

function check_re_dir() {
	if [ -d ${RE_DIR} ]; then
		true
	else
		mkdir -p ${RE_DIR}
	fi
	green "Save_Datas_Dir: ${RE_DIR}"
}

function check_hd_conf() {
	case_hd_conf=${DATA_PATH}${case}/hardware_config.prototxt
	if [[ -d /opt/profile/ && -f ${case_hd_conf} ]]; then
		sudo cp ${case_hd_conf} /opt/profile/
		sudo chmod -R 777 /opt/profile
	elif [ ! -f ${case_hd_conf} ]; then
		red "No ${case_hd_conf} !\nexit 0" && exit 0
	else
		sudo mkdir -p /opt/profile
		sudo cp ${case_hd_conf} /opt/profile
		sudo chmod -R 777 /opt/profile
	fi
}

# --- func main ---
function main() {
	source ${ANP_PATH}setup.bash
	for case in $(ls ${DATA_PATH}); do
		# --- line ---
		line=$(printf "%80s" ' ') && printf "%s\n" ${line//' '/'-'}
		# --- pre: set config ---
		#check_hd_conf
		play_bag_name=${DATA_PATH}${case}/$(ls ${DATA_PATH}${case} | grep bag)
		sed -i "/ebag_name /{s/: .*/: \"${play_bag_name//\//\\\/}\"/}" ${PLAY_CONFIG}
		re_path=${RE_DIR}${case} && mkdir -p ${re_path}
		sed -i "/save_path /{s/: .*/: \"${re_path//\//\\\/}\"/}" ${RECORD_CONFIG}
		# --- ignore info: info >/dev/null ---
		green "Regressing: ${play_bag_name}" && green "Wait About 2min ..."
		cd ${ANP_PATH} && source ./setup.bash
		pavaro -c ./dag/em_sim.dag -d JIDU >/dev/null 2>&1
		green "${case} Regressed Success, Save Path: ${re_path}, Regressed Output: "
		ls -lh ${RE_DIR}${case} | grep -v total | awk '{print $5 "\t" $9}'
		green "All Regressed Cases: "
		ls -l ${RE_DIR} | grep -v total | awk '{print $9}'
	done
}

# --- main ---
set_pre_conf
check_case_dir
check_re_dir
main

