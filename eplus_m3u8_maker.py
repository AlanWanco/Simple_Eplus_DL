import argparse
from datetime import datetime
import os
import re 
import pyperclip
import requests

formatted_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
path = os.getcwd()
head = '''#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:7
#EXT-X-MEDIA-SEQUENCE:413
'''
ending = '''#EXT-X-ENDLIST
'''

parser = argparse.ArgumentParser(description='m3u8一键生成')
parser.add_argument('--url', '-u',help = 'eplus地址', required=False, type=str)
parser.add_argument('--base', '-b', help='base 地址名构成→https://stream.live.eplus.jp/out/v1/<base>/index_<list>_<num>.ts', required=False, type=str)
parser.add_argument('--list', '-l', help='选择m3u8流', required=True, type=str)
parser.add_argument('--start', '-s', help='开始片段', required=True, type=int)
parser.add_argument('--end', '-e', help='结束片段', required=True, type=int)
args = parser.parse_args()

file = fr'{path}/eplus_{args.start}-{args.end}_{formatted_datetime}.m3u8'
MATCH_URL = r'https:.*?index\.m3u8'
MATCH_STREAM = 'https://stream.live.eplus.jp/out/v1/(?P<base>.*)/index'
MATCH_ARCHIVE ='https://vod.live.eplus.jp/out/v1/(?P<base>.*?)/'

def get_text(url):
    fresh_response = requests.get(url)
    text = fresh_response.text
    return text

def match_expre(expre, main_response):
    match = re.search(expre, main_response)
    if match is None:
        return "None"  
    else:
        matched_string = match.group()
        return matched_string

def find_base(match, text):
    result = re.search(match, text)
    print('获得base值：', result.group("base"))
    if result:
        return result.group("base")
    else:
        return None

def makeFile(file):
    with open(file, 'w', encoding='utf-8') as f:
        f.write(head)

    i = args.start
    while i <= args.end:
        repeat = f'''#EXTINF:6.006
https://stream.live.eplus.jp/out/v1/{base}/index_{args.list}_{i}.ts
'''
        
        with open(file, 'a', encoding='utf-8') as f:
            f.write(repeat)
            i += 1

    with open(file, 'a', encoding='utf-8') as f:
            f.write(ending)
    with open(file, 'r', encoding='utf-8') as f:
        pyperclip.copy(f.read())

if __name__ == "__main__":
    try:
        base = False
        if args.url:
            res = requests.get(args.url)
            if res.status_code == 200:
                text = get_text(args.url)
                m3u8_url = match_expre(MATCH_URL, text).replace("\/", "/")
                print(m3u8_url)
                if m3u8_url.startswith('https://stream.live.eplus.jp/out/v1/'):
                    print('已从网页中获取推流地址')
                    base = find_base(MATCH_STREAM, m3u8_url)

                if m3u8_url.startswith('https://vod.live.eplus.jp/out/v1/'):
                    print('回放已上线')
                    base = find_base(MATCH_ARCHIVE, m3u8_url)
                    m3u8_url = f'https://stream.live.eplus.jp/out/v1/{base}/index.m3u8'

        if base == False:
            base = args.base
            print("使用输入的base")
        if not base:
            print('未检测到输入的base！')
            
        if base:
            makeFile(file)
            print("m3u8文件已生成！")
    except Exception as e:
        print(e)
