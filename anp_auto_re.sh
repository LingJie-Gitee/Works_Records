#! /bin/bash
# description: perception simulation regression test and evaluation 

FILE_NAME=$(echo $(realpath ${0}) | awk -F '/' '{print $NF}')
RATIO=0.2
FILE_DIRNAME=$(dirname ${0})
DATA_DIR=$(realpath ${1})
ROOT_DIR=$(dirname ${DATA_DIR})
REG_DIR=${ROOT_DIR}/anp_reged_data_$(date +"%m%d%H%M%S")
WORK_SCRIPT=/home/caros/cybertron/scripts/offline_x86_test.sh
total_case=0

# --- func color ---
function green(){
	echo -e "\033[;32m[INFO $(date +"%m/%d %H:%M") ${FILE_NAME}] $1 \033[0m"
}

function red(){
	echo -e "\033[;31m[ERROR $(date +"%m/%d %H:%M") ${FILE_NAME}] $1 \033[0m"
}

# --- func work ---
function pre_work() {
	# check case directory 
	if [[ -d ${DATA_DIR} && -n ${DATA_DIR} ]]; then
		green "Original Datas Dir: ${DATA_DIR}"
	else
		red "Usage:\n\tbash anp_auto_re.sh [DATA_PATH]\nexit 0" && exit 0
	fi
	# set params
	params=$(find ${DATA_DIR} -type d -name "params" | wc -l)
	if [ ${params} -eq 0 ]; then
		for case in $(ls ${DATA_DIR}); do
			mkdir -p ${DATA_DIR}/${case}/params
			tar -zxvf ${DATA_DIR}/${case}/*.tar.gz -C ${DATA_DIR}/${case}/params >/dev/null 2>&1
			rm -rf ${DATA_DIR}/${case}/*.tar.gz
		done
	else
		true
	fi
	green "Set Params Success !"
	# set scripts
	if [ -f ${WORK_SCRIPT} ]; then true; else bash ${FILE_DIRNAME}/anp_pre_re.sh; fi
	green "Scripts Copy Success !"
	# set regressed directory
	if [ -d ${REG_DIR} ]; then true; else mkdir -p ${REG_DIR}; fi
	green "Save Data Path: ${REG_DIR}"
}

function regress() {
	cd /home/caros && source ./cybertron/setup.bash >/dev/null 2>&1
	for case in $(ls ${DATA_DIR}); do
		green "Start Regressing Case: ${case} ..."
		bash ${WORK_SCRIPT} -p ${DATA_DIR}/${case}/params -d ${DATA_DIR}/${case}/*.record -r ${RATIO} -t ${REG_DIR}
		regressed_record=$(ls ${REG_DIR} | grep -v ADD | grep -v JFS | grep -v JBS | grep -v '_')
		mv ${REG_DIR}/${regressed_record} ${REG_DIR}/${case}.record
		green "All Regressed Case: "
		ls -lh ${REG_DIR} | grep -v total | awk -v n=0 '{n++; printf("No.%s\tSize: %s\tName: %s"n,$5,$9)}'
	done
}

function decode() {
	source /home/caros/venv/bin/activate >/dev/null 2>&1
	cd /home/caros/cybertron_parse-master && source ./cybertron/setup.bash
	for record_name in $(ls ${REG_DIR} | grep "\.record"); do
 		((total_case++))
		green "Start Decoding Record: ${record_name} ..."
		input_path=${REG_DIR}/${record_name}
		output_path=${REG_DIR}/${record_name/\.record/''} && mkdir -p ${output_path}
		python decode_record/decode_record_mp.py ${input_path} ${output_path} 2>/dev/null
		green "No.${total_case} ${record_name} Decode Finish !"
	done
}

function evaluate() {
	eval_tools_dir=/home/caros/whole_functional_test_evaluation_tool
	sed -i "/root_dir/{s/: .*/: \"${ROOT_DIR//\//\\\/}\/\"/}" ${eval_tools_dir}/configs/cfg_tool.yaml
	for case in $(ls ${REG_DIR} | grep -v "\.record"); do
		# set /gt dir & /res_record dir
		case_gt_dir=${ROOT_DIR}/gt/${case} && mkdir -p ${case_gt_dir}
		case_js_dir=${ROOT_DIR}/res_record/${case} && mkdir -p ${case_js_dir}
		# set .yaml file
		yaml_file=${DATA_DIR}/${case}/FT_ground_truth_file.yaml
		cp ${yaml_file} ${case_gt_dir}
		# set .json file
		file=$(cat ${yaml_file} | grep file | awk '{print $2}')
		keyword=$(printf "%s" ${file//\.json*/''})
		json_file=${REG_DIR}/${case}/bag_json/${keyword}.json
		cp ${json_file} ${case_js_dir}
		# total info
		module=$(cat ${yaml_file} | grep module | awk '{print $2}')
	done
	cd ${eval_tools_dir} && sudo python3 ./run_evaluation.py
}

function statis() {
	pass_cases=$(cat ${ROOT_DIR}/*.csv | grep Pass | wc -l)
	fail_cases=$(cat ${ROOT_DIR}/*.csv | grep Fail | wc -l)
	green "Pass Cases:" && cat -n ${ROOT_DIR}/*.csv | grep Pass
	green "Fail Cases:" && cat -n ${ROOT_DIR}/*.csv | grep Fail
	green "Total: ${total_case} Pass: ${pass_cases} Fail: ${fail_cases}"
}

# --- main ---
pre_work
regress
decode
evaluate
statis

# --- after ---
green "-------------------- Perception Whole_Function Regression & Evaluation Finish ! --------------------"


