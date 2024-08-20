# encoding=utf-8
import re
import os, subprocess
import paramiko
import time
import logging
from decimal import Decimal


class OfflineCalib(object):
    """
    相机标定离线压测脚本
    提前准备: 通过跳板机scp上传数据集
    """
    def __init__(self, master_data_path, slave_data_path):
        self.master_host = '172.16.9.21'
        self.slave_host = '172.16.9.23'
        self.user_name = 'calib'
        self.password = 'Hello1234'
        self.slave_scp = None
        self.logger = None
        self.master_data_path = master_data_path  # 主板数据集
        self.slave_data_path = slave_data_path  # 从板数据集
        self.slave = None
        self.success = {'yy': 0, 'nyy': 0}
        self.fail = {'yy': 0, 'nyy': 0}
        self.bad_calib = {'yy': [], 'nyy': []}
        self.params_noyuyan = [
            'onsemi_obstacle_extrinsics.yaml',
            'onsemi_obstacle_intrinsics.yaml',
            'onsemi_narrow_extrinsics.yaml',
            'spherical_backward_extrinsics.yaml',
            'spherical_backward_intrinsics.yaml',
            'spherical_left_backward_extrinsics.yaml',
            'spherical_left_backward_intrinsics.yaml',
            'spherical_left_forward_extrinsics.yaml',
            'spherical_left_forward_intrinsics.yaml',
            'spherical_right_backward_extrinsics.yaml',
            'spherical_right_backward_intrinsics.yaml',
            'spherical_right_forward_extrinsics.yaml',
            'spherical_right_forward_intrinsics.yaml',
        ]
        self.params_yuyan = ['fisheye_front_extrinsics.yaml',
                             'fisheye_front_intrinsics.yaml',
                             'fisheye_left_extrinsics.yaml',
                             'fisheye_left_intrinsics.yaml',
                             'fisheye_rear_extrinsics.yaml',
                             'fisheye_rear_intrinsics.yaml',
                             'fisheye_right_extrinsics.yaml',
                             'fisheye_right_intrinsics.yaml',
                             ]

        # 鱼眼/非鱼眼文件列表
        self.camera_fl = {
            'master': [
                "spherical_right_forward.jpg",
                "spherical_left_forward.jpg",
                "onsemi_obstacle.jpg",
                "spherical_backward.jpg",
                "spherical_right_backward.jpg",
                "spherical_left_backward.jpg",
                "onsemi_obstacle_intrinsics.yaml",
                "spherical_backward_intrinsics.yaml",
                "spherical_right_backward_intrinsics.yaml",
                "spherical_left_backward_intrinsics.yaml",
                "fisheye_right_intrinsics.yaml",
                "fisheye_rear_intrinsics.yaml",
                "fisheye_left_intrinsics.yaml",
                "fisheye_front_intrinsics.yaml",
            ],
            'slave': [
                "fisheye_right.jpg",
                "fisheye_rear.jpg",
                "fisheye_left.jpg",
                "fisheye_front.jpg",
                "onsemi_narrow.jpg",
                "onsemi_spare.jpg",
                "onsemi_narrow_intrinsics.yaml",
                "onsemi_spare_intrinsics.yaml",
                "spherical_right_forward_intrinsics.yaml",
                "spherical_left_forward_intrinsics.yaml",
            ]
        }
        # 打分的文件列表
        self.nyy_score_files = {
            'onsemi_narrow_extrinsics.yaml': [],
            'onsemi_obstacle_extrinsics.yaml': [],
            'spherical_backward_extrinsics.yaml': [],
            'spherical_left_backward_extrinsics.yaml': [],
            'spherical_left_forward_extrinsics.yaml': [],
            'spherical_right_backward_extrinsics.yaml': [],
            'spherical_right_forward_extrinsics.yaml': [],
        }
        self.yy_score_files = {
            'fisheye_front_extrinsics.yaml': [],
            'fisheye_left_extrinsics.yaml': [],
            'fisheye_rear_extrinsics.yaml': [],
            'fisheye_right_extrinsics.yaml': [],
        }

    @staticmethod
    def all_files_abspath(path):
        """
        获取path目录下所有文件的完整路径
        """
        all_files_abspath = []
        for root, dirs, files in os.walk(path):
            all_files_abspath = [os.path.join(root, file) for file in files]  # 拼接 → files_abspath

        # 返回所有文件的绝对路径(算法会挑选指定文件，不用担心混乱，后续可以考虑性能优化，仅筛选目标文件，或者场景集预处理，去除非必须文件)
        return all_files_abspath

    def calib_need_files(self, root_path, board, case_name):
        """
        root_path: 场景集路径, 所有场景均存储在此, 如: ~/root_path/case1/; ~/root_path/case2/ ...
        board: 主从板
        case_name: 场景名/用例名
        return : 本轮标定用作输入的文件(主从板不同)
        """
        # 字典, 存储不同场景的同类文件，如: 'fisheye_front.jpg': ['/case1/fisheye_front.jpg', '/case2/fisheye_front.jpg']
        same_files = {}
        # 列表, 返回本轮测试用作输入的文件集(绝对路径)
        file_to_calib = []
        # 列表, 其元素 = 文件的绝对路径
        all_files = self.all_files_abspath(root_path)
        # 列表, 其元素 = 主板或从板需要的文件的名称, 不含路径(后续作为标定算法的输入)
        input_files = self.camera_fl.get(board)
        # 筛选目标文件:
        for type_x in input_files:
            pattern = '/' + type_x  # 举例: /fisheye_front.jpg
            # 遍历所有文件的绝对路径，找出其中: 含"/fisheye_front.jpg"字符串 & 含"case_name(本轮标定的场景名)"字符串的绝对路径
            for file_x in all_files:
                if pattern in file_x and case_name in file_x:
                    file_to_calib.append(file_x)
                    self.logger.info(file_x)

        return file_to_calib

    def ssh_link(self, host):
        """
        ssh link
        """
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=host, username=self.user_name, password=self.password)

        return ssh

    @staticmethod
    def local_shell(cmd):
        """
        master: local exec shell
        """
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, executable="/bin/bash")
        output, error = process.communicate()

        return output

    def exec_shell(self, cmd, ssh=None):
        """
        master: local exec cmd
        slave: ssh to slave then exec cmd
        """
        if ssh:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            output = stdout.read().decode()
            return output
        else:
            return self.local_shell(cmd)

    def kill_mock_proc(self):
        """
        kill mock process
        """
        sudo = 'echo {} | sudo -S'.format(self.password)
        cmd = "ps -ef | grep 'dag/dyn_client.dag' | grep -v grep | awk '{print $2}' | xargs kill -9"
        sudo_cmd = "{} {}".format(sudo, cmd)
        self.exec_shell(sudo_cmd)
        self.logger.info('kill dag/dyn_client.dag process')
        time.sleep(3)

    def create_logger(self):
        """
        create logger
        """
        self.logger = logging.getLogger('my_logger')
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s-%(levelname)s: %(message)s')

        # 写到控制台
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        # 设置到logger对象中
        self.logger.addHandler(console_handler)

    def cp_data(self, case_name):
        """
        拷贝数据放到对应位置
        """
        self.logger.info('master board use data list')
        master_files = self.calib_need_files(self.master_data_path, 'master', case_name)
        self.logger.info('slave board use data list')
        slave_files = self.calib_need_files(self.slave_data_path, 'slave', case_name)
        self.logger.info('master files & slave files copy success !')
        for master_file in master_files:
            # 主板cp到指定目录
            cmd = 'cp {} /opt/profile/calibration/camera/'.format(master_file)
            self.exec_shell(cmd)
        self.exec_shell("sync")
        for slave_file in slave_files:
            file_name = str(slave_file).split('/')[-1]
            # 从板scp到指定目录
            self.slave_scp.put(slave_file, '/opt/profile/calibration/camera/' + file_name)

    def calc_score(self, t, ytype):
        """
        打分
        """
        t = t.replace(' ', '-').replace(':', '-')
        data = {}  # 所有外参的打分字典
        key = 'score'  # 分数关键字
        pass_score = 60  # 及格分
        base_path = '/opt/profile/params/'
        if 'yy' == ytype:
            data = self.yy_score_files
        elif 'nyy' == ytype:
            data = self.nyy_score_files
        for i in data.keys():
            fpath = base_path + i
            text = self.exec_shell('cat {}'.format(fpath))
            comp = key + r':.*?(\d.*?)\n'
            is_score = re.findall(comp, text, re.S)
            external_path = t + '/params/' + i  # 日志存放的目录
            # 能匹配到分数
            if is_score:
                score = Decimal(is_score[0])
                self.logger.info('{}:{}'.format(i, score))
                if ytype == 'lidar':
                    # 超出及格分范围
                    if score >= pass_score:
                        self.bad_calib[ytype].append((str(score), external_path))
                        self.logger.warning(
                            'Waring: {}: {} score is: {}, high pass_score {}'.format(ytype, i, score, pass_score))
                else:
                    # 超出及格分范围
                    if score <= pass_score:
                        self.bad_calib[ytype].append((str(score), external_path))
                        self.logger.warning(
                            'Waring: {}: {} score is: {}, below pass_score {}'.format(ytype, i, score, pass_score))
            # 匹配分数失败
            else:
                score = 0
                self.bad_calib[ytype].append((score, external_path))
                self.logger.warning('Waring: {}: {} score is: 0'.format(ytype, i))
            data[i].append(score)

        return data

    def get_date(self):
        """
        get system date
        """
        cmd = 'date "+%Y-%m-%d %H:%M:%S"'
        t = self.exec_shell(cmd)
        t = str(t).strip()

        return t

    def mock(self):
        """
        启动mock, 获取时间
        """
        current_time = str(time.time())
        log_path = '/opt/data/mock_log/{}.log'.format(current_time)
        self.logger.info(log_path)
        cmd = 'cd /opt/calib; nohup mainboard -p client -d dag/dyn_client.dag >{} 2>&1 &'.format(log_path)
        self.exec_shell(cmd)
        t = self.get_date()

        return t

    def check_proc(self):
        """
        check process
        """
        # 主板
        cmd = 'ps -ef | grep mainboard'
        text = self.exec_shell(cmd)
        comp = 'calibrate_master.dag'
        master_proc = re.search(comp, text, re.S)
        # 从板
        text = self.exec_shell(cmd, self.slave)
        comp = 'calibrate_slave.dag'
        slave_proc = re.search(comp, text, re.S)
        if master_proc and slave_proc:
            self.logger.info('master and slave calib proc exist')
        else:
            if not master_proc:
                self.logger.error('master calib process not exist')
            if not slave_proc:
                self.logger.error('slave calib process not exist')

    def get_log(self, ssh, t, timeout):
        """
        主从板查询日志
        """
        self.exec_shell("sync", ssh)
        mock_time = time.strptime(t, '%Y-%m-%d %H:%M:%S')
        mt = time.mktime(mock_time)
        start_time = time.time()
        grep_text = 'calib_step_7 ResponseFinishedMsgToMcu'
        cmd = 'cd /opt/log/calib;timeout 5 grep -nr  -a "{}"'.format(grep_text)
        while time.time() - start_time < timeout:
            # self.exec_shell("sync")
            text = self.exec_shell(cmd, ssh)
            # 获取从板日志结果
            pattern = ".*?I(\d{4} \d{2}:\d{2}:\d{2})\..*?(" + grep_text + ")"
            ti = re.findall(pattern, text, re.S)
            if not ti:
                time.sleep(1)
                continue
            for info in ti:
                # info[0] 是日志出现的时间, info[1]代表日志的具体内容
                format_time = '1970' + info[0]  # 1102新增
                log_time_tmp = time.strptime(format_time, '%Y%m%d %H:%M:%S')
                log_time_timestamp = int(time.mktime(log_time_tmp))
                mock_time_timestamp = int(time.mktime(mock_time))
                if log_time_timestamp > mock_time_timestamp and info[1] == grep_text:
                    self.logger.info('current judge log time is:' + str(info[0]))
                    gaps = time.mktime(time.strptime(self.get_date(), '%Y-%m-%d %H:%M:%S')) - mt
                    self.logger.info('use {} second get log success '.format(gaps))
                    return True
                if log_time_timestamp > mock_time_timestamp:
                    self.logger.info(info[1])
                    return False
            time.sleep(3)
        self.logger.warning('calibration timeout {} second'.format(timeout))

        return False

    def external_params(self, ssh, ytype):
        """
        校验外参文件
        """
        base_path = '/opt/profile/params/'
        cmd = 'cd {}; ls'.format(base_path)
        self.exec_shell("sync", ssh)
        file_list = self.exec_shell(cmd, ssh)
        params_files = self.params_yuyan
        if ytype == 'nyy':
            params_files = self.params_noyuyan
        for file in params_files:
            params_abspath = base_path + file
            cmd = 'du -b {}'.format(params_abspath)
            file_size = self.exec_shell(cmd, ssh)
            file_size = re.split('\s+', file_size)[0]
            if re.search(file, file_list) and int(file_size) > 0:
                pass
            else:
                self.logger.error('file error not exist:' + str(file))
                return False

        return True

    def fail_to_something(self, ssh, t):
        """
        标定失败要做的一些事
        """
        t = t.replace(' ', '-').replace(':', '-')
        self.logger.info('current fail folder name is:' + str(t))
        sudo = 'echo {} | sudo -S'.format(self.password)  # 删除1个空格
        # 先创建失败的最外层文件夹
        path = '/opt/data/calib_alldata_back/calib_fail_back/' + t
        cmd = 'mkdir {}'.format(path)
        self.exec_shell(cmd, ssh)
        cmd = 'mkdir {}/log_error;mkdir {}/data_error'.format(path, path)
        self.exec_shell(cmd, ssh)
        # calib
        tar_file = 'calib-{}.tar.gz'.format(t)
        cmd = 'cd /opt/log/;{} tar -zcvf {} calib'.format(sudo, tar_file)
        self.exec_shell(cmd, ssh)
        cmd = '{} mv /opt/log/{}  {}/log_error/'.format(sudo, tar_file, path)
        self.exec_shell(cmd, ssh)
        # params
        tar_file = 'params-{}.tar.gz'.format(t)
        cmd = 'cd /opt/profile/;{} tar -zcvf {} params'.format(sudo, tar_file)
        self.exec_shell(cmd, ssh)
        cmd = '{} mv /opt/profile/{} {}/data_error/'.format(sudo, tar_file, path)
        self.exec_shell(cmd, ssh)

    def success_data_store(self, ssh, t):
        """
        本次执行成功存储/opt/profile/calibration和/opt/profile/params/数据
        """
        t = t.replace(' ', '-').replace(':', '-')
        self.logger.info('current success folder name is:' + str(t))
        sudo = 'echo {} | sudo -S'.format(self.password)  # 删除1个空格
        # 先创建成功的最外层文件夹
        path = '/opt/data/calib_alldata_back/calib_success_back/' + t
        cmd = 'mkdir {}'.format(path)
        self.exec_shell(cmd, ssh)
        # /opt/profile/calibration data
        tar_file = 'camera-{}.tar.gz'.format(t)
        cmd = 'cd /opt/profile/;{} tar -zcvf {} calibration'.format(sudo, tar_file)  # 删除1个空格
        self.exec_shell(cmd, ssh)
        cmd = '{} mv /opt/profile/{} {}'.format(sudo, tar_file, path)
        self.exec_shell(cmd, ssh)
        # params
        tar_file = 'params-{}.tar.gz'.format(t)
        cmd = 'cd /opt/profile/;{} tar -zcvf {} params'.format(sudo, tar_file)
        self.exec_shell(cmd, ssh)
        cmd = '{} mv /opt/profile/{} {}'.format(sudo, tar_file, path)
        self.exec_shell(cmd, ssh)

    def pre_0(self):
        """
        :return:
        """
        self.create_logger()
        self.slave = self.ssh_link(self.slave_host)
        self.slave_scp = self.slave.open_sftp()
        # mountrw
        cmd = 'echo {} | sudo -S mountrw'.format(self.password)
        self.exec_shell(cmd)
        self.exec_shell(cmd, self.slave)
        # 新增加的总的备份目录
        basic_log_cmd = 'cd /opt/data; mkdir calib_alldata_back; mkdir mock_log'
        self.exec_shell(basic_log_cmd)
        self.exec_shell(basic_log_cmd, self.slave)
        # 创建成功的和失败的次目录
        result_directory_cmd = "cd /opt/data/calib_alldata_back; mkdir calib_success_back; mkdir calib_fail_back"
        self.exec_shell(result_directory_cmd)
        self.exec_shell(result_directory_cmd, self.slave)

    def pre_1(self):
        """
        return metric
        """
        # error_code metric, 一般在主板
        yaml_path = '{}/sensor_calib_metric.yml'.format(self.master_data_path)
        scenarios, results, errorcode = [], [], []
        keys_mapping = {
            "Scenario:": scenarios,
            "Result:": results,
            "Errorcode:": errorcode, }
        # yaml_metric transfer to python_dict
        with open(yaml_path, 'r') as f:
            for line in f:
                line = line.strip()
                for key, collection in keys_mapping.items():
                    if line.startswith(key):
                        collection.append(line.split(key)[1].strip())
        scenario_result_errorcode = dict(zip(scenarios, zip(results, errorcode)))

        return scenario_result_errorcode

    def main(self, loops, j, case_name, ytype, metric, timeout=120):
        """
        main
        ytype: 相机类型
        yy: 鱼眼
        nyy: 非鱼眼
        """
        # 开始标定
        self.logger.info('type:{}\tall:{}，current:{}'.format(ytype, loops, j + 1))
        self.logger.info('current_case_name: {}'.format(case_name))
        # 放置随机数据
        self.cp_data(case_name)
        time.sleep(5)
        # 主板mock, 打印mock时间
        t = self.mock()
        self.logger.info(t)
        # 主从板mock进程存在性
        self.check_proc()
        # 获取主从板日志
        slave_log = self.get_log(self.slave, t, timeout)
        master_log = self.get_log(None, t, 20)
        time.sleep(20)
        master_params = self.external_params(None, ytype)
        slave_params = self.external_params(self.slave, ytype)

        # 匹配出标定完成的标志
        cmd_metric = 'cd /opt/log/calib; grep -nar "calib_step_7 ResponseFinishedMsgToMcu"'
        log_string = self.exec_shell(cmd_metric, self.slave)
        match = re.search("error_info (.*)", log_string)
        # 测试结果
        error_info_test = match.group(1).strip()
        self.logger.info('error_info_test is: {}'.format(error_info_test))
        # 期望结果
        error_info_expected = metric[case_name][1]
        self.logger.info('error_info_expected is: {}'.format(error_info_expected))

        # 获取主从板外参文件
        if slave_log and master_log and master_params and slave_params and error_info_test == error_info_expected:
            self.logger.info('current {} calib result pass'.format(j + 1))
            self.success[ytype] += 1
            # 标定成功后计算各外参标定分数
            current_score_data = self.calc_score(t, ytype)
            for k, v in current_score_data.items():
                self.logger.info('{} , Total score: {}'.format(k, sum(v)))
            # 成功后主从板保存params,calibration日志
            self.success_data_store(None, t)
            self.success_data_store(self.slave, t)
        else:
            self.logger.error('current {} calib result fail, reason: test != expected'.format(j + 1))
            if not master_log:
                self.logger.error('master log get fail')
            if not slave_log:
                self.logger.error('slave log get fail')
            if not master_params:
                self.logger.error('master board extrinsic not exist')
            if not slave_params:
                self.logger.error('slave board extrinsic not exist')
            self.fail[ytype] += 1
            # 失败主从板打包日志
            self.fail_to_something(None, t)
            self.fail_to_something(self.slave, t)

        self.logger.info(
            'type: {}, all: {} , pass: {} , fail: {}'.format(ytype, loops, self.success[ytype], self.fail[ytype]))
        self.check_proc()
        self.kill_mock_proc()

    def end_0(self, ytype):
        """
        计算平均分数
        """
        data = {}
        if ytype == 'yy':
            data = self.yy_score_files
        elif ytype == 'nyy':
            data = self.nyy_score_files

        for k, v in data.items():
            total_score = sum(v)
            if self.success[ytype] == 0:
                self.logger.warning('{} success is 0, can`t calc score'.format(ytype))
                break
            average_score = total_score / self.success[ytype]
            self.logger.info('{}\ttotal score: {}\taverage_score: {}'.format(k, total_score, average_score))

    def end_1(self):
        """
        统计bad case
        """
        self.logger.info('Bad calib score info:')
        bad_count = 0
        for k, v in self.bad_calib.items():
            if len(v) > 0:
                self.logger.info(k)
                self.logger.info(v)
                bad_count += len(v)
        self.logger.info('All bad calib count:  {} '.format(bad_count))

    def after_exec(self):
        """
        停止标定服务, 重新启动状态机服务
        """
        calib_stop_cmd = 'cd /opt/calibration; echo -e "Hello1234\n" | sudo -S bash stop_calib.sh'
        delete_log_cmd = 'echo -e "Hello1234\n" | sudo -S rm -rf /opt/log/calib/*'
        # 主从停止标定服务
        self.exec_shell(calib_stop_cmd, self.slave)
        self.exec_shell(calib_stop_cmd, None)
        self.logger.info('stop calib end')
        # 主从清空日志
        self.exec_shell(delete_log_cmd, self.slave)
        self.exec_shell(delete_log_cmd, None)
        self.logger.info('delete calib log')
        time.sleep(5)


if __name__ == '__main__':
    # pre
    current_ytype = 'yy'  # 通过"sed -i"修改这个值, 可以实现不同相机的压测
    master_datas = '/opt/data/cjt/calibration_produce_corner_master'
    slave_datas = '/opt/data/cjt/calibration_produce_corner_slave'
    calib_obj = OfflineCalib(master_datas, slave_datas)
    calib_obj.pre_0()
    metrics = calib_obj.pre_1()
    # main
    start = 'AVM' if current_ytype == 'yy' else '8M'
    cases_name = [case_name for case_name in os.listdir(master_datas) if case_name.startswith(start)]
    loop = len(cases_name)
    for master_folder_name in cases_name:
        slave_folder_name = master_folder_name.replace('master', 'slave')
        if slave_folder_name not in os.listdir(slave_datas):
            calib_obj.logger.error('{} is not in {}'.format(slave_folder_name, slave_datas))
    for seq in range(loop):
        case_name = cases_name[seq].split('_master')[0]
        calib_obj.main(loop, seq, cases_name, current_ytype, metrics)
    # after
    calib_obj.end_0(current_ytype)
    calib_obj.end_1()
    calib_obj.after_exec()
