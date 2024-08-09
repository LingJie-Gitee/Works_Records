import os
import sys
import subprocess
import shutil
import re
import requests
import random
import string
import time
import numpy as np
import matplotlib.pyplot as plt
import logging
import paramiko
import itertools


class Logging:

    def __init__(self, start_single, log_name='test.log'):
        """
        在当前文件同目录下生成log
        :param log_name: 日志文件名称
        """
        # 设置存放日志的文件
        file_name = time.strftime('%y-%m-%d-%H-%M-%S-') + log_name
        log_path = os.path.join(os.path.dirname(__file__), file_name)
        with open(log_path, mode='a', encoding='UTF8'):   # mode='a/w/a+/w+'，自动创建，'r'不行
            pass

        # 生成日志器
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)   # 日志需要通过关卡一，日志器的级别

        # 生成处理器，设置处理器级别、格式
        handler = logging.FileHandler(log_path, encoding='UTF8')   # 区别stream_handler
        handler.setLevel(logging.DEBUG)   # 日志需要通过关卡二，处理器的级别
        handler.setFormatter(logging.Formatter('%(asctime)s-%(levelname)s: %(message)s'))   # 日志生成格式

        # 处理器添加到日志器中
        self.logger.addHandler(handler)
        self.logger.info(start_single)


class InternetPython(Logging):

    @staticmethod
    def douban_top250():
        """
        internet_python: 吃国家饭的开端
        :return: None
        """
        # 准备工作：对象 + 配置 + 容器
        urls_ = ['https://movie.douban.com/top250']   # 任意网址，爬取对象
        header_ = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/118.0.0.0 Safari/537.36"}   # 请求头，跳过反爬，可以长期使用
        content = os.path.join(os.path.dirname(__file__), 'douban_top250.txt')   # 任意地址，存放获取到的内容

        # 工作：请求 + 响应 + 筛选 + 存储
        result = []   # 总的容器
        for item in urls_:
            responsex = requests.get(url=item, headers=header_)   # 请求request的结果即是响应response
            target = re.findall('alt=\"([\u4e00-\u9fa5]+)\"', responsex.text)   # 正则表达式筛选目标字符串
            result.extend(target)   # 将响应体添加到总容器
        with open(content, mode='w', encoding='UTF8') as tp250:   # 仅open一次，写入多次，性能小优化
            sortx = 1   # 排名
            for ele in result:   # 遍历总容器，将其添加到对应文件
                tp250.write(f'第{sortx}名:\t{ele}\n')
                sortx += 1

    @staticmethod
    def roro_kingdom():
        """
        internet_python: touch_fish
        :return: None
        """
        # 准备工作：对象 + 配置 + 容器
        url_ = 'https://www.17roco.qq.com/'  # 对象
        header_ = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/118.0.0.0 Safari/537.36"}  # 请求头，跳过反爬，可以长期使用
        content = os.path.join(os.path.dirname(__file__), 'roco_kingdom.txt')  # 任意地址，存放获取到的内容

        # 工作：请求 + 响应 + 筛选 + 存储
        responsex = requests.get(url=url_, headers=header_)  # 请求request的结果即是响应response
        target = re.findall('[\u4e00-\u9fa5]+', responsex.text)  # 正则表达式筛选汉字
        content_filter = [0, '1']   # 过滤器
        with open(content, mode='w', encoding='UTF8') as roco:  # 仅open一次，写入多次，性能小优化
            for ele in target:
                if len(ele) >= content_filter[0] and ele[-1] not in content_filter[1]:   # 太短不要，部分文字不要
                    roco.write(ele + '\n')


class ListCalcu(Logging):

    listy = []
    dictx = {}

    @classmethod
    def order_asc(cls, list_y) -> list:
        """
        经典冒泡排序, 升序
        """
        for j in range(1, len(list_y)):
            for i in range(0, len(list_y) - 1):
                if list_y[i] >= list_y[i + 1]:
                    list_y[i], list_y[i + 1] = list_y[i + 1], list_y[i]

        return list_y

    @classmethod
    def order_desc(cls, list_x) -> list:
        """
        反向冒泡, 降序
        """
        for j in range(1, len(list_x)):
            for i in range(0, len(list_x) - 1):
                if list_x[i] <= list_x[i + 1]:
                    list_x[i], list_x[i + 1] = list_x[i + 1], list_x[i]

        return list_x

    @classmethod
    def majority(cls, listy: list) -> None:
        """
        求众数，并输出众数出现的次数
        """
        dictx = {i: listy.count(i) for i in listy}
        for i in dictx.items():
            if i[1] == max(dictx.values()):
                print(f'对于{dictx}\n众数: {i[0]}，出现次数: {i[1]}')

    @classmethod
    def switch_kv(cls, dicty: dict) -> None:
        """
        交换字典的keys和values。
        """
        a = {v: k for k, v in dicty.items()}
        print(f'k:v → v:k后：{a}')

    def combinations(self, original_list: list):
        """
        组合
        :return: 不重复的组合的情况
        """
        all_combinations = []
        for length in range(1, len(original_list) + 1):
            # 求组合：C length/5，length取1-5，以[(,), ...]形式存放
            all_combinations_of_length = itertools.combinations(original_list, length)
            # 将上述变量内的元素挨个添加到容器内，并记录在log中
            for item in all_combinations_of_length:
                if item not in all_combinations:
                    all_combinations.append(item)
                    self.logger.info(item)

        return all_combinations

    def permutations(self, original_list: list):
        """
        排列
        可以用来求数组的所有子集
        :param original_list:
        :return:
        """
        all_permutations = []
        for length in range(1, len(original_list) + 1):
            # 求排列：A length/5，length取1-5，以[(,), ...]形式存放
            all_permutations_of_length = itertools.permutations(original_list, length)
            # 将上述变量内的元素挨个添加到容器内，并记录在log中
            for item in all_permutations_of_length:
                if item not in all_permutations:
                    all_permutations.append(item)
                    self.logger.info(item)

        return all_permutations


class NumCalcu(Logging):

    num = random.randrange(-10, 10)

    def nine_x_nine(self):
        """
        xx乘法表
        """
        for i in range(1, abs(self.num) + 1):
            for j in range(1, i + 1):
                print(f'{j} × {i} = {i * j}\t', end='')
            print()

    @classmethod
    def factorial_cal(cls, x):
        """
        计算x的阶乘
        :return :返回阶乘
        """
        start = 1
        num_factorial = 1
        if x == 0:
            return 1
        else:
            if x > 0:
                while start <= x:
                    num_factorial = num_factorial * start
                    start += 1
                return num_factorial
            else:
                character = 1 if -x % 2 == 0 else -1
                while start <= -x:
                    num_factorial = num_factorial * start
                    start += 1
                return num_factorial * character

    @classmethod
    def pai_lie_zu_he(cls, low_, high_, model_='C'):
        """
        计算排列A-MN，组合C-MN
        :return:返回计算结果
        """
        while True:
            # 判断数据
            if low_ < high_:
                print('不满足：下标 >= 上标')
                continue
            elif low_ <= 0 or high_ <= 0:
                print('不满足：正整数 > 0')
                continue
            elif '.' in str(low_) or '.' in str(high_):
                print('不满足：正整数不含小数点')
                continue
            # 计算并返回结果
            if model_ in 'Aa':
                result_a = int(cls.factorial_cal(low_) / cls.factorial_cal(low_ - high_))
                print(f'排列为：{result_a}')
                return result_a
            elif model_ in 'Cc':
                result_c = int(cls.factorial_cal(low_) / cls.factorial_cal(low_ - high_) / cls.factorial_cal(high_))
                print(f'组合为：{result_c}')
                return result_c
            else:
                print('请输入A、a、C、C中任意字母')
                continue

    @staticmethod
    def time_delta():
        """
        计算时间差。
        """
        # 也可以使用datetime.seconds，输出秒属性！
        start_t = input('输入开始时间，格式如：2023/09/30 23:59\n')
        end_t = input('输入结束时间，格式如：2023/10/21 16:31\n')
        nian = int(start_t[0:4:1]) - int(end_t[0:4:1])
        yue = int(start_t[5:7:1]) - int(end_t[5:7:1])
        ri = int(start_t[8:10:1]) - int(end_t[8:10:1])
        shi = int(start_t[11:13:1]) - int(end_t[11:13:1])
        fen = int(start_t[14:16:1]) - int(end_t[14:16:1])
        print(f'相差：{nian}年，{yue}月，{ri}日，{shi}时，{fen}分')

    @staticmethod
    def ltime_to_stime(l_time: str = '2023/11/10 14:13'):
        """
        标准时间转时间戳，格式如：1689263999，单位s，类型<class 'float'>
        :param l_time:标准时间
        :return:返回seconds
        """
        # 把传入的标准时间转换为<class 'time.struc_time'>
        a = time.strptime(l_time, '%Y/%m/%d %H:%M')
        # 把<class 'time.struc_time'>转换为seconds
        b = time.mktime(a)
        return b

    @staticmethod
    def stime_to_ltime(g_time: float = 1689263999.0):
        """
        时间戳转标准时间，输出格式如：2023/09/20 08:00，类型<class 'str'>
        :param g_time:seconds
        :return:返回标准时间
        """
        # 将seconds转化为<class 'time.struct_time'>
        c = time.localtime(g_time)
        # 将<class 'time.struc_time'>转化为标准时间
        d = time.strftime('%Y/%m/%d %H:%M', c)
        return d

    @staticmethod
    def even_sum():
        """
        求1-100以内的偶数和，和大于1000时停止，并输出最后一次相加的偶数。
        """
        even_sum = 0
        for i in range(1, 101):
            if i % 2 == 0:
                if even_sum < 1000:
                    even_sum = even_sum + i
                else:
                    print(even_sum, i - 2)
                    break


class Operator(Logging):

    @staticmethod
    def dos_cmd_log(cmd: str):
        """
        dos窗口中执行cmd，获取返回值，并将返回值存入指定文件内。
        :param cmd: dos窗口中执行的命令
        :return: None
        """
        # 获取cmd命令的返回内容，并重命名为a
        a = os.popen(f'{cmd}').read()
        # 获取当前文件直属上级目录地址，并重命名为p
        p = os.path.dirname(__file__)
        # 目录存在则直接创建文件并写入内容，然后break，否则创建目录，再循环一次！
        with open(p + '\\Dos_Result.txt', mode='w', encoding='utf8') as cmd:
            # 写入时间和写入内容
            cmd.write(time.strftime('%Y-%m-%d %H:%M:%S') + ':')
            cmd.write(a)


class StringCh(Logging):

    @staticmethod
    def change_shape(strings: str) -> None:
        """
        字母大写变小写，小写变大写，数字则不做改变。
        """
        # 容器，将处理后（大变小，小变大）的字符串存起来
        container = []
        for i in strings:
            if i in string.ascii_uppercase:
                # 如果是大写字母，就变小写，然后添加到container中，elif同理
                container.append(i.lower())
            elif i in string.ascii_lowercase:
                container.append(i.upper())
            else:
                container.append(i)
        # ''.join(container)将container由列表变字符串
        print('转换前：' + strings + '\n转换后：' + ''.join(container))


class FindFile(Logging):
    file_list = []
    dir_list = []

    @staticmethod
    def file_find1(pathx):
        """
        递归遍历，会反复执行此方法，为了遍历所有目录。
        :param pathx:
        :return:
        """
        # 遍历地址下的所有文件/目录
        for file in os.listdir(pathx):
            file_name = os.path.join(pathx, file)
            # 如果是目录：
            if os.path.isdir(file_name):
                FindFile.dir_list.append(file)
                FindFile.file_find1(file_name)   # 递归此目录
            # 否则：如果是文件
            else:
                FindFile.file_list.append(file)

    @staticmethod
    def file_find2(pathx):
        for i, j, k in os.walk(pathx):
            print(f'遍历地址：{i}\t目录：{j}\t文件：{k}')


class NumImage(Logging):

    @staticmethod
    def test_():
        """
        just test
        :return:
        """
        x_p = np.array([1, 5, 3, 7, 9, 1])
        y_p = np.array([2, 5, 7, 4, 8, 4])
        x_point = [1, 2, 3, 6]
        y_point = [3, 2, 1, 2]
        color_style_width = {'linestyle': '-', 'linewidth': 1}
        plt.suptitle('ALL_AT_SEA')   # 总图标题
        # 图一
        plt.subplot(2, 2, 1)   # 图像输入位置
        plt.title('test1')   # 子图标题
        plt.xlabel('X-axis', loc='left')   # 子图X轴名称
        plt.ylabel('Y-axis', loc='bottom')   # 子图Y轴名称
        plt.plot(x_point, y_point, 'r-o')   # 子图颜色、形状、坐标点
        plt.grid(visible=1, which='both', axis='both', **color_style_width)   # 子图网格线
        # 图三
        plt.subplot(2, 2, 3)
        plt.title('test2')
        plt.xlabel('XXXX', loc='center')
        plt.ylabel('YYYY', loc='center')
        plt.plot(x_p, y_p, 'r-o')
        plt.grid(visible=1, which='both', axis='both', **color_style_width)

        plt.show()

    @staticmethod
    def random_scatter():
        """
        随机散点图
        :return: None
        """
        plt.suptitle('Random Scatter')
        random_color = random.sample(['r', 'b', 'g', 'k', 'y', 'r', 'b', 'g', 'k', 'b'], 10)
        plt.scatter(random.sample(range(1, 20), 10), random.sample(range(1, 20), 10),
                    s=random.sample(range(1, 999), 10), c=random_color, marker='*')
        plt.grid(visible=None, which='major', color='g', linestyle=':', linewidth='0.5')
        plt.show()


class Painter(Logging):

    @staticmethod
    def christmas_tree(size):
        """
        Christmas Tree: 2023-12-25, have a good day.
        :param size: size of tree
        :return: None
        """
        # 树叶
        for i in range(size):
            print(' ' * (size - i) + ('*' * i) + '*' + ('*' * i))
        # 树干
        main_ = 1 + size//6   # 最少1，合理。
        for i in range(main_):
            print(' ' * size + '|')


class FinishJob(Logging):

    @staticmethod
    def ssh_connect(cmd: str):
        """
        测试通过paramiko实现SSH连接，以及在远程中断执行cmd
        """
        # 实例化SSH客户端，并将实例化的对象添加到主机host_allow中去，相当于键入'yes'保证书
        ssh_client = paramiko.client.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # 调用connect方法，并传入建立SSH的必要信息
        ssh_client.connect(hostname='172.16.9.67', port=22, username='liangzhao', password='123456')

        # 返回3个对象，且无法直接读取，需要调用read()读取 + decode()解码
        stdin, stdout, stderr = ssh_client.exec_command(f'{cmd}')
        result = stdout.read().decode('UTF-8')

        # 检查命令执行情况
        check = stdout.channel.recv_exit_status()

        return result

    @staticmethod
    def runcmd(command):
        # 运行linux_cmd， 注意参数
        run_cmd = subprocess.run(command, shell=True, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, encoding="utf-8")  # 可以增加命令截至时间: timeout=3
        # 获取cmd的输出
        result = run_cmd.stdout

        return result


class LeetCode(NumCalcu, ListCalcu, Logging):

    @staticmethod
    def find_longest_of_():
        """
        找出string中最长且连续的()字串，输出它的索引位，并计算长度
        :return: None
        """
        # 随机生成规定字符串
        string_ = ''
        length_ = random.randrange(30, 80)
        i = 0
        while i < length_:
            i = i + 1
            son = random.sample('()', 1)
            string_ = string_ + son[0]
        print(f"随机生成长度为：{len(string_)} 的字符串：{string_}")

        # 关键符号转化
        exec_ = string_.replace('()', 'T')
        tar_ = re.findall('T+', exec_)

        # 结果输出
        longest_ = len(max(tar_))*2
        index_ = string_.index(str(max(tar_)).replace('T', '()'))
        print(f'最长且连续的"()"的长度为：{longest_}，他的起始位置为：{index_}')

        return 0

    @staticmethod
    def compress_string(string_):
        """
        压缩字符串，'aaabbcc'压缩后：'a3b2c2'
        :param string_: 原始字符串
        :return:
        """
        # 字符串转列表，利用列表的可变性，记录元素重叠的个数
        container_1 = []
        container_1.extend(string_)
        for ele_0 in range(len(container_1)):
            length = 1
            for ele_1 in range(ele_0+1, len(container_1)):
                if container_1[ele_0] == container_1[ele_1]:
                    length = length + 1
                    container_1[ele_1] = ''
                else:
                    break
            container_1[ele_0] = container_1[ele_0] * length

        # 统计列表元素
        for i in range(len(container_1)):
            if container_1[i] and len(container_1[i]) > 1:
                container_1[i] = container_1[i][0] + str(len(container_1[i]))
        container_2 = [i for i in container_1 if i]

        return ''.join(container_2)

    @staticmethod
    def balance_string(original_s: str):
        """
        求最长平衡子字符串
        平衡: 0都在1的左边，O的数量等于1的数量
        子字符串: 连续字符串，长度肯定小于original_s
        :param original_s: 原始字符串
        :return: longest_son_s
        """
        container = {}
        for i in range(len(original_s)):
            for j in range(i+1, len(original_s)):
                son_s = original_s[i:j:1]
                if len(son_s) % 2 == 0:
                    if '1' not in son_s[0:int(len(son_s) / 2):1]:
                        if '0' not in son_s[-1:int(len(son_s) / 2) - 1:-1]:
                            container[son_s] = len(son_s)
        result = int(max(container.values()) / 2)

        return result * '0' + result * '1'

    @classmethod
    def son_set(cls, father_list: list):
        """
        求列表的所有子集
        思路：
        百度可知，一个列表拥有的子集数 = 2^元素数-1，即2的【元素数】次方-1
        首先命名一个空的二进制代码容器container = []
        循环【2^元素数】次，每次都会生成一个二进制代码，将其添加到container中
        再命名一个空的子集容器son_list = []
        遍历container内的二进制代码，根据0 or 1产生子集的元素，0则空，1则有
        :param father_list:
        :return: son_list
        """
        container = []
        for i in range(2 ** len(father_list)):
            int_to_str = bin(i).replace('0b', '')   # 关键步骤：将循环次数转换为二进制，后续会根据0 or 1产生子集的元素
            son_str = ''
            if len(int_to_str) < len(father_list):
                metric = (len(father_list) - len(int_to_str)) * '0' + int_to_str   # 长度不足的会补齐0
                for ele in range(len(metric)):
                    if metric[ele] == '1':
                        son_str = son_str + str(father_list[ele])   # 是"1"就"上"
                if son_str:
                    container.append(son_str)
            else:
                for ele in range(len(int_to_str)):
                    if int_to_str[ele] == '1':
                        son_str = son_str + str(father_list[ele])
                if son_str:
                    container.append(son_str)

        print(len(container), container)

    @staticmethod
    def string_like_z(original_string: string):
        """
        将【原始字符串】按【从上到下，从左往右】画出一个"Z"字
        :param original_string:
        :return: z_string
        """
        
        pass

    @staticmethod
    def orin_string_0(string_: str):
        """
        字符串预处理_fun1
        :param string_: 待处理字符串
        :return: 处理好的列表
        """
        contain_ = []
        for index in range(len(string_)):
            target = int(string_[index]) * 'A' if string_[index] in string.digits else string_[index]
            contain_.extend(target)

        return contain_

    @staticmethod
    def orin_string_1(string_: str):
        """
        字符串预处理_fun2
        part_0: 0
        part_1: 1 ~ -3
        part_2: -2
        part_3: -1
        :param string_: 待处理字符串
        :return: 处理好的列表
        """
        contain_ = []
        for index in range(len(string_)):
            if index == 0:   # 第1位
                if string_[index] in string.digits and string_[index + 1] in string.digits:
                    target_0 = int(string_[index] + string_[index + 1]) * 'A'
                    contain_.extend(target_0)
                else:
                    target_1 = int(string_[index]) * 'A' if string_[index] in string.digits else string_[index]
                    contain_.extend(target_1)
            elif index < len(string_) - 2:   # 第二位 - 倒数第三位
                if string_[index - 1] in string.digits:
                    continue
                elif string_[index] in string.digits and string_[index + 1] in string.digits:
                    target_0 = int(string_[index] + string_[index + 1]) * 'A'
                    contain_.extend(target_0)
                else:
                    target_1 = int(string_[index]) * 'A' if string_[index] in string.digits else string_[index]
                    contain_.extend(target_1)
            elif index == len(string_) - 2:   # 倒数第二位
                if string_[index - 1] in string.digits:
                    continue
                elif string_[index] in string.digits and string_[index + 1] in string.digits:
                    target_0 = int(string_[index] + string_[index + 1]) * 'A'
                    contain_.extend(target_0)
                    break
                else:
                    target_1 = int(string_[index]) * 'A' if string_[index] in string.digits else string_[index]
                    contain_.extend(target_1)
            else:   # 最后一位
                if string_[index] in string.digits and string_[index - 1] in string.digits:
                    break
                target_0 = int(string_[index]) * 'A' if string_[index] in string.digits else string_[index]
                contain_.extend(target_0)

        return contain_

    @staticmethod
    def orin_string_metric(list_s1: list, list_s2: list):
        """
        判断处理好的列表是否满足同源字符串条件
        :return: Error or Nothing
        """
        metric_list = list_s1 if len(list_s1) >= len(list_s2) else list_s2
        other_list = list_s2 if metric_list is list_s1 else list_s1
        print(f'{metric_list}{len(metric_list)}\n{other_list}{len(other_list)}')

        if len(metric_list) == len(other_list):
            for index in range(len(metric_list)):
                if metric_list[index] == other_list[index] or metric_list[index] == 'A' or other_list[index] == 'A':
                    continue
                else:
                    raise Exception
        else:
            raise Exception

        return True

    def orin_string_main(self, s1: str, s2: str):
        """
        同源字符串
        """
        print(s1, s2)

        try:
            list_s1 = self.orin_string_0(s1)
            list_s2 = self.orin_string_0(s2)
            self.orin_string_metric(list_s1, list_s2)
            print('第一种方法成功, 是同源字符串')
            return True
        except BaseException:
            print('第一种方法失败')
            try:
                list_s3 = self.orin_string_1(s1)
                list_s4 = self.orin_string_1(s2)
                self.orin_string_metric(list_s3, list_s4)
                print('第二种方法成功, 是同源字符串')
                return True
            except BaseException:
                print('第二种方法失败')
                try:
                    list_s5 = self.orin_string_1(s1)
                    list_s6 = self.orin_string_0(s2)
                    self.orin_string_metric(list_s5, list_s6)
                    print('第三种方法成功, 是同源字符串')
                    return True
                except BaseException:
                    print('第三种方法失败')
                    try:
                        list_s7 = self.orin_string_1(s2)
                        list_s8 = self.orin_string_0(s1)
                        self.orin_string_metric(list_s7, list_s8)
                        print('第四种方法成功, 是同源字符串')
                    except BaseException:
                        print('四种方法都失败, 不是同源字符串')


if __name__ == '__main__':
    start_time = time.time()

    # test1 = ListCalcu('Start Logging ↓↓↓ ', 'test.log')
    # test2 = NumCalcu()
    # test3 = StringCh()
    # test4 = FindFile()
    # test5 = NumImage()
    # test6 = Operator('systeminfo')
    # test7 = Logging()
    # test8 = InternetPython()
    # test9 = Painter()
    # test10 = FinishJob()
    test11 = LeetCode('start LeetCoting')
    test11.find_longest_of_()

    finish_time = time.time()
    print(f'duration: {float(finish_time - start_time)}s')
