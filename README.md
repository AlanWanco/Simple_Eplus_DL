# Simple_Eplus_DL
一个配合N_m3u8DL-RE简单下载eplus视频的工具
# 快速开始
```
eplus_download --url <eplus url> ...
```
# Release包使用方式
* 首先，运行`EasyCommandRunner.exe`。
* 可以看到我的配置文件里已经填好了所需的范例内容和说明
![Snipaste_2024-02-12_04-28-31](https://github.com/AlanWanco/Simple_Eplus_DL/assets/45628961/94b298bd-7530-475e-bdfd-f471a6362ace)
* 根据需求设置下载即可
* 内封`片段编号与视频时间戳转换.html`，根据可以根据时间戳或片段地址手动互转
* 附赠`eplus_m3u8_maker.exe`手动构造m3u8，如何构造可以`-h`查看说明（和下面的各命令情况类似）。
* 构造结束后发送手动构造内容到剪贴板，可以**同时打开eplus对应页面**和浏览器插件猫抓把m3u8内容粘贴进去之后直接播放m3u8地址以精确定位所需时间戳
![image](https://github.com/AlanWanco/Simple_Eplus_DL/assets/45628961/996eb8fa-a737-4e37-9c20-0e5c264ecacc)

![image](https://github.com/AlanWanco/Simple_Eplus_DL/assets/45628961/934a9248-42af-4971-9352-f03031d89c79)

![image](https://github.com/AlanWanco/Simple_Eplus_DL/assets/45628961/515ad447-3b01-4e22-a119-a1190efa7db8)

![image](https://github.com/AlanWanco/Simple_Eplus_DL/assets/45628961/5b75c794-94d9-45d6-9c85-ce9125f22965)

![image](https://github.com/AlanWanco/Simple_Eplus_DL/assets/45628961/0887eaff-4e0b-4497-9190-af172a75f2ab)

# 各命令解释
* `-h`：获取帮助
* `-u`、`--url`：eplus地址 必填 支持普通地址和vip地址
* `-l`、`--list`：选择码流 可选项 不填默认选择最大分辨率
* `-s`、`--start`：开始分片 可选项 不填默认为起始片段1
* `-e`、`--end`：结束分片 可选项 不填默认为当前最大分片（直播时为当时最新分片）
* `-a`、`--archive`：可选项 当回放上线时可直接下载回放
* `-p`、`--proxy`：可选项 设置代理 

# 特性
* **首先，目前不支持武士道系DRM加密下载**
* 不设定码流、开始时间和结束时间时，默认下载最高画质、全部内容
* 全自动模式：默认下载最高画质全部内容；半自动模式：下载所设定的码流中分片范围内的内容；回放模式：下载官方提供的回放。

