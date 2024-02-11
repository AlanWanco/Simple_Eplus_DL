import argparse
from datetime import datetime
import os
import re
import shutil
import subprocess
import requests 

parser = argparse.ArgumentParser(description='eplus一键下载')
parser.add_argument('--url', '-u',help = 'eplus地址 支持普通地址和vip', required=True, type=str)
parser.add_argument('--list', '-l', help='选择码流 可选项 不填默认选择最大分辨率', required=False, type=str)
parser.add_argument('--start', '-s', help='开始分片 可选项 不填默认为起始片段1', required=False, type=int)
parser.add_argument('--end', '-e', help='结束分片 可选项 不填默认为最大分片', required=False, type=int)
parser.add_argument('--archive', '-a', help='当回放上线时 输入这个选项下载回放',nargs='?', const='1', required=False, type=str)
parser.add_argument('--proxy', '-p', help='设置下载代理 格式http://127.0.0.1:7890(当前只支持设置http代理)', required=False, type=str)
parser.add_argument('--range', '-r', help = '''选择视频范围 <0-10> <05:00-20:00>
例如:# 下载[0,10]共11个分片 --range 0-10
# 下载从序号10开始的后续分片 --range 10-
# 下载前100个分片 --custom-range -99
# 下载第5分钟到20分钟的内容 --range "05:00-20:00" 路径中有英文冒号时，前后一定要加""
# 带小时的格式："01:05:00-01:10:00"''', required=False, type=str)
args = parser.parse_args()

if args.proxy:
    os.environ['HTTP_PROXY'] = args.proxy

formatted_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
path = os.getcwd()
temp_path = os.path.join(path, 'temp_elus')
file = f'eplus_{formatted_datetime}'
file_path =os.path.join(temp_path,file + '.m3u8')
proxy = '--custom-proxy'

head = '''#EXTM3U
#EXT-X-VERSION:3
#EXT-X-MEDIA-SEQUENCE:3288
#EXT-X-DISCONTINUITY-SEQUENCE:4
'''
ending = '''#EXT-X-ENDLIST
'''

MATCH_VIP = r"var vipToken = '(.*?)'"
MATCH_URL = r'https:.*?.m3u8'
MATCH_STREAM = 'https://stream.live.eplus.jp/out/v1/(?P<base>.*)/index'
MATCH_ARCHIVE ='https://vod.live.eplus.jp/out/v1/(?P<base>.*?)/'

def match_expre(expre, main_response):
    match = re.search(expre, main_response)
    if match is None:
        return "None"  
    else:
        matched_string = match.group()
        return matched_string

def get_cookie(url):
    fresh_response = requests.get(url)
    cookie_jar=fresh_response.cookies
    cookie_fin = 'Cookie:'
    for cookie in cookie_jar:
        if cookie.name == 'CloudFront-Key-Pair-Id' or cookie.name == 'CloudFront-Policy' or cookie.name == 'CloudFront-Signature':
            cookie_value = f'{cookie.name}={cookie.value}; '
            cookie_fin += cookie_value
    return cookie_fin

# 处理回放上线后多cookie的情况
def multi_cookie(cookie_jar, url):
    cookies_list = list(cookie_jar.items())
    cookies_dict = {}

    for k, v in cookies_list:
        if k in cookies_dict:
            cookies_dict[k].append(v)
        else:
            cookies_dict[k] = [v]

    new_cookies = [
        {'CloudFront-Policy': policy, 'CloudFront-Signature': signature, 'CloudFront-Key-Pair-Id': key_id}
        for policy, signature, key_id in zip(cookies_dict['CloudFront-Policy'], cookies_dict['CloudFront-Signature'], cookies_dict['CloudFront-Key-Pair-Id'])
    ]

    for cookie in new_cookies:
        res = requests.get(url, cookies=cookie)
        if res.status_code == 200:
            cookie_fin = 'Cookie:'
            output = "; ".join(f"{k}={v}" for k, v in cookie.items()) + ";"
            cookie_fin = cookie_fin + output
            # print(cookie_fin)
            return cookie_fin

def get_text(url):
    fresh_response = requests.get(url)
    text = fresh_response.text
    print(text)
    return text

def find_vip():
    if args.url.startswith("https://live.eplus.jp/ex/player"):
        response = requests.get(args.url)
        m = re.search(MATCH_VIP, response.text)
        print("VIP地址：https://live.eplus.jp/vp/" + m.group(1))

def find_m3u8(text):
    res = requests.get(text)
    m3u8_url = match_expre(MATCH_URL, res.text).replace("\/", "/")
    print('获得主m3u8值：', m3u8_url)
    return m3u8_url

def find_base(match, text):
    result = re.search(match, text)
    print('获得base值：', result.group("base"))
    return result.group("base")

def find_num(text):
    result = re.findall(r'index_\d+_(\d+)\.ts', text)
    numbers = map(int,result)
    max_num = max(numbers)
    print('当前最大片段：', max_num)
    return max_num

def find_index_list(text):
    index_list = re.findall(r'\S+\.m3u8', text)
    print(index_list)
    return(index_list)

def resolution_to_int(resolution_string):
    width, height = map(int, resolution_string.split("x"))
    return width * height

def find_max_resolution(text):
    stream_info_lines = filter(lambda x: x.startswith("#EXT-X-STREAM-INF:"), text.split("\n"))
    # print(stream_info_lines)
    sorted_stream_info_lines = sorted(stream_info_lines,
                                    key=lambda x: resolution_to_int(re.search("RESOLUTION=(\d+x\d+)", x).group(1)),
                                    reverse=True
                                    )

    manifest_lines_list = text.split("\n")
    max_resolution_line = sorted_stream_info_lines[0]

    max_resolution_line_index = manifest_lines_list.index(max_resolution_line)  
    corresponding_index_url = manifest_lines_list[max_resolution_line_index + 1]


    max_resolution = re.search("RESOLUTION=(\d+x\d+)", max_resolution_line).group(1)
    print('最大分辨率：', max_resolution)
    print('最大分辨率流：', corresponding_index_url)
    
    return corresponding_index_url

def make_m3u8_file(start, end, base, list):
    with open(file_path, 'w', encoding='utf-8') as f:
            f.write(head)
    i = start
    while i <= end:
        repeat = f'''#EXTINF:6.006
https://stream.live.eplus.jp/out/v1/{base}/{list}_{i}.ts
'''
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(repeat)
            i += 1

    with open(file_path, 'a', encoding='utf-8') as f:
            f.write(ending)
    print('已手动构建m3u8！')

def m3u8_download(m3u8, cookie):
    command = fr'N_m3u8DL-RE "{m3u8}" --save-name "{file}" --save-dir "{path}" --download-retry-count 5 --auto-select --del-after-done --thread-count 16 -H "{cookie}" --check-segments-count'
    if args.range:
        command = fr'N_m3u8DL-RE "{m3u8}" --save-name "{file}" --save-dir "{path}" --download-retry-count 5 --auto-select --del-after-done --thread-count 16 -H "{cookie}" --custom-range "{args.range}" --check-segments-count'
    if args.proxy:
        command = command + ' ' + proxy + ' ' +args.proxy
    # print(command)
    subprocess.call(command)

if __name__ == "__main__":
    try:
        res = requests.get(args.url)
        if res.status_code == 200:
            if not os.path.exists(temp_path):
                os.mkdir(temp_path)
                print('已创建缓存目录')
            os.chdir(temp_path)

            fresh_response = requests.get(args.url)
            cookie_jar = fresh_response.cookies
            cookie = get_cookie(args.url)

            find_vip()
            m3u8_url = find_m3u8(args.url)# 获取主m3u8地址
            
            if m3u8_url.startswith('https://stream.live.eplus.jp/out/v1/'):
                print('已从网页中获取推流地址')
                base = find_base(MATCH_STREAM, m3u8_url)
                code = 1
                if args.archive:
                    print('官方回放未上线，无法下载官方回放')

            if m3u8_url.startswith('https://vod.live.eplus.jp/out/v1/'):
                print('回放已上线')
                base = find_base(MATCH_ARCHIVE, m3u8_url)
                if args.archive is None:
                    m3u8_url = f'https://stream.live.eplus.jp/out/v1/{base}/index.m3u8'
                    code = 1
                else:
                    print('检测到下载回放设定，下载官方回放')
                    code = 2
                cookie = multi_cookie(cookie_jar, m3u8_url)

            if code == 1:
                m3u8_res = requests.get(m3u8_url,cookies=cookie_jar)# 获取主m3u8的内容
                max_index = find_max_resolution(m3u8_res.text)# 获取最佳分辨率的index

                if args.list:
                    print('检测到手动选择码流，码流为：index_' + args.list + '.m3u8')
                    max_index = 'index_' + args.list + '.m3u8'
                max_index_num = max_index.replace(".m3u8", "")

                url = f'https://stream.live.eplus.jp/out/v1/{base}/{max_index}'
                res = requests.get(url,cookies=cookie_jar)
                max_num = find_num(res.text)

                if not args.start:
                    print('没有检测到开始片段输入，默认从片段1开始')
                    min_num = 1
                if args.start:
                    min_num = args.start
                    print('开始片段：', min_num)

                if not args.end:
                    print('没有检测到结束片段输入，默认从最后一个片段开始')
                if args.end:
                    max_num = args.end
                    print('结束片段：', max_num)

                make_m3u8_file(min_num, max_num, base ,max_index_num)
                print('eplus cookie有效期只有一个小时，请尽快下载！')
                m3u8_download(file_path, cookie)

            if code == 2:
                m3u8_download(m3u8_url, cookie)

            os.chdir(path)

            if os.path.exists(temp_path):
                print('删除目录')
                shutil.rmtree(temp_path)

    except Exception as e:
        print(e)
