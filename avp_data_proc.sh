#! /bin/bash
# description: avp data process, set params_dir + hardware_config.prototxt + *_mode_avp.record

mode=${1}
path=${2}
clean_or_not=${3}
tool_path=/home/caros/x86_perception_log2recordtool/tlmdecode-linux-amd64
script_path=/home/caros/x86_perception_log2recordtool/auto_mock.sh

# --- func pre ---
function Usage() {
	echo -e "Usage:\tbash avp_data_proc.sh [1 or 2] [path to data_dir] [clean or null]"
	echo -e "\t1 = mock_mode, mock_mode need files:"
	echo -e "\t\t1. params.tar.gz\n\t\t2. cyberecord*.record\n\t\t3. *.tar.zst\n\t\t4. *.bag\n\t\t5. *.v4.pb.zst"
	echo -e "\t2 = ebag_mode, ebag_mode need files:"
	echo -e "\t\t1. params.tar.gz\n\t\t2. cyberecord*.record\n\t\t3. *.tar.zst\n\t\t4. *.bag"
	echo -e "\tif [clean] then rm -rf useless datas, else not\n"
	exit 0
}

function check_dir() {
	if [[ -d ${path} && -n ${path} ]]; then
		dir=$(realpath ${path})/
		echo -e "Cases Directory: ${dir}" && sleep 3
	else
		Usage
	fi
}

function set_params(){
	mkdir -p ${dir}${case}/params
	tar -zxvf ${dir}${case}/params*.gz -C ${dir}${case}/params
}

function set_conf(){
	tar -I zstd -xvf ${dir}${case}/*.tar.zst -C ${dir}${case}
	cp ${dir}${case}/opt/profile/hardware_config.prototxt ${dir}${case}/
}

function set_json(){
	zstd -d ${dir}${case}/*.v4.pb.zst
	${tool_path} logslice ${dir}${case}/*.v4.pb > ${dir}${case}/${case}.json
}

function mk_record() {
	bash ${script_path} ${mode} ${dir}${case}/cyberecord*.record
}

function clean_data() {
	if [ ${1} == 'clean' ]; then
		rm -rf ${dir}${case}/params*.gz
		rm -rf ${dir}${case}/opt/
		rm -rf ${dir}${case}/*.tar.zst
		rm -rf ${dir}${case}/*.v4.pb*
		rm -rf ${dir}${case}/*.bag
		rm -rf ${dir}${case}/cyberecord*.record
		rm -rf ${dir}${case}/output.record
		rm -rf ${dir}${case}/*.json
	else
		true
	fi
}

# --- func main ---
function main() {
	if [ ${mode} == 1 ]; then
		echo "mock mode, data dir: ${dir}"
		for case in `ls ${dir}`; do
			set_params
			set_conf
			set_json
			mk_record
			clean_data ${clean_or_not}
		done
	elif [ ${mode} == 2 ]; then
		echo "ebag mode, data dir: ${dir}"
		for case in `ls ${dir}`; do
			set_params
			set_conf
			mk_record
			clean_data ${clean_or_not}
		done
	else
		Usage
	fi
}

# --- main ---
check_dir
main

