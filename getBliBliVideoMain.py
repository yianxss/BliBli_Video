# -*- coding: utf-8 -*-
# Author :Soul
# date   :2019/4/4
__version__ = 'v1.0'
# 2019年4月16日23:13:35 维护，新增已存在文件判断
# 2019年5月3日00:32:59 新增根据空间地址下载视频

import sys
import time

import requests
import json
import os
from you_get import common as you_get
import re


class BliVideo(object):
    # 初始化
    def __init__(self, basePath):
        self.basePath = basePath

    # 根据关键词查找视频的api
    @staticmethod
    def search_video_api(keyWord, page_num=None):
        base_url = 'https://api.bilibili.com/x/web-interface/search/type?jsonp=jsonp&search_type=video'
        if page_num is None:
            return base_url + '&keyword={kw}'.format(kw=keyWord)
        else:
            return base_url + \
                '&keyword={kw}&page={pg_num}'.format(kw=keyWord, pg_num=page_num)

    # 根据aid 获取视频列表信息——json
    @staticmethod
    def video_list_api(aid):
        return 'https://api.bilibili.com/x/web-interface/view?aid={Aid}'.format(
            Aid=aFid)

    # 个人空间api
    @staticmethod
    def space_api(mid, cid):
        return 'https://api.bilibili.com/x/space/channel/video?mid={mid}&cid={cid}'.format(
            mid=mid, cid=cid)

    # 根据aid 翻页
    @staticmethod
    def video_detail_info_api(aid, page_num):
        return 'https://www.bilibili.com/video/av{Aid}/?p={Page_Num}'.format(
            Aid=aid, Page_Num=page_num)

    # 秒转时间
    @staticmethod
    def secondToTime(second):
        m, s = divmod(second, 60)
        h, m = divmod(m, 60)
        return "%d:%02d:%02d" % (h, m, s)

    # 时间戳转日期时间
    @staticmethod
    def timeStampToDatetime(timeStamp):
        localtime = time.localtime(timeStamp)
        return time.strftime('%Y-%m-%d %H:%M:%S', localtime)

    # 创建文件夹,创建失败返回提供的基文件夹
    def mkDirs(self, folderPath):
        folderPath = folderPath.rstrip("\\").strip()
        isExists = os.path.exists(folderPath)
        if not isExists:
            try:
                os.makedirs(folderPath)
                print('[{}]-创建成功'.format(folderPath))
                return folderPath
            except Exception as e:
                print('[{}]-创建失败-{err}'.format(folderPath, err=e))
                return self.basePath
        else:
            print('[{}]-已存在'.format(folderPath))
            return folderPath

    # 获取html源码
    @staticmethod
    def getHtml(strUrl):
        headers = {
            'Host': 'api.bilibili.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/68.0.3440.106 Safari/537.36',
            'Referer': 'https://space.bilibili.com/20291891/channel/detail?cid=29424'}
        try:
            r = requests.get(strUrl, headers=headers)
            r.encoding = 'utf-8'
            r.raise_for_status()
            return r.text
        except Exception as e:
            print('get html failed--->{}'.format(e))
            return None

    # 根据关键词获取查找结果列表
    def getSearchHtml(self, keyWord):
        html = self.getHtml(self.search_video_api(keyWord))
        if html is not None:
            return html

    # 获取结果页数
    def getNumPages(self, keyWord):
        jsonData = json.loads(self.getSearchHtml(keyWord))
        if int(jsonData['data']['numResults']) > 0:
            numPages = jsonData['data']['numPages']
            return numPages
        else:
            print("没有对应关键词的结果")
            return None

    # 按照页码获取aid
    def _getAidsByPageNum(self, keyWord, pageNum):
        VideoAids = []
        r = self.getHtml(self.search_video_api(keyWord, pageNum))
        baseInfo = json.loads(r)
        for Item in baseInfo['data']['result']:
            VideoAids.append(Item['aid'])
        return VideoAids

    # 获取视频标题
    def getTileByAid(self, videoAid):
        videoLink = self.video_list_api(videoAid)
        r = self.getHtml(videoLink)
        if r is not None:
            videoInfo = json.loads(r)
            try:
                title = videoInfo['data']['title']
                subStr = r'[\\/:*?"<>|\r\n]+'
                if title is not None:
                    title = re.sub(subStr, '_', title)
                    return title
            except Exception as e:
                print(e)
        else:
            return None

    # 根据aid 获取视频url列表
    def getVideoList(self, videoAid):
        videoList = []
        videoLink = self.video_list_api(videoAid)
        r = self.getHtml(videoLink)

        videoInfo = json.loads(r)
        if 'data' in videoInfo:
            for Item in videoInfo['data']['pages']:
                page_num = Item['page']
                videoList.append(
                    {'title': 'P{:0>3d} {}'.format(int(page_num), Item['part']),
                     'videoUrl': self.video_detail_info_api(videoAid, page_num)
                     })
            return videoList

    # 根据链接下载视频
    @staticmethod
    def downloadVideo(videoLink, videoPath, videoName):
        fullname = os.path.join(videoPath, videoName + ".flv")
        if not os.path.isfile(fullname):
            sys.argv = ['you-get', '-o', videoPath, '-O', videoName, videoLink]
            you_get.main()
        else:
            print("[已存在-]" + videoName)

    # 按照aid批量下载
    def downVideosByAid(self, Aid, savePath=None):

        # 根据aid获取下载的URL列表
        videoList = self.getVideoList(Aid)
        if videoList is not None:
            title = self.getTileByAid(Aid)
            print('title:' + title)
            if savePath is None:
                foldPath = os.path.join(self.basePath, title)
            else:
                foldPath = os.path.join(savePath, title)

            videoPath = self.mkDirs(foldPath)
            # 写入视频一些从基础信息

            jsonData = json.loads(
                self.getHtml(
                    self.video_list_api(Aid)))['data']
            videoInfo = {
                'aid': jsonData['aid'],
                '课时': jsonData['videos'],
                '时长': self.secondToTime(jsonData['duration']),
                '上传': self.timeStampToDatetime(jsonData['pubdate']),
                '上传人': '{name}-->https://space.bilibili.com/{url}'.format(name=jsonData['owner']['name'],
                                                                          url=jsonData['owner']['mid']),
                '播放次数': jsonData['stat']['view'],
            }
            infoTxtFilename = os.path.join(videoPath, 'videoInfo.txt')
            with open(infoTxtFilename, 'w', encoding='utf-8') as f:
                f.write(json.dumps(videoInfo, ensure_ascii=False))

            for (eve, Item) in enumerate(videoList):
                args = [Item.get('videoUrl'), videoPath, Item.get('title')]
                print([args[0], args[2]])
                self.downloadVideo(*args)
                if eve == (videoInfo['课时'] - 1):
                    try:
                        with open(infoTxtFilename, 'a', encoding='utf-8') as f:
                            f.write(r'\n' + "完结")
                    except IOError as e:
                        print(e)

    # 多个aid批量下载
    def downVideosByAids(self, Aids, savePath=None):
        for eve in Aids:
            self.downVideosByAid(eve, savePath)

    # 按照关键词下载
    def downVideosByKeyWord(self, keyWord, videoPageNum=None):
        # 对应的文件夹
        keyPath = os.path.join(self.basePath, keyWord)
        keyPath = self.mkDirs(keyPath)
        if videoPageNum is not None:
            Aids = self._getAidsByPageNum(keyWord, videoPageNum)
            for Item in Aids:
                self.downVideosByAid(Item, keyPath)
        else:
            # 根据关键词获取所有页
            pageNum = self.getNumPages(keyWord)
            for i in range(1, pageNum + 1):
                Aids = self._getAidsByPageNum(keyWord, i)
                for Item in Aids:
                    self.downVideosByAid(Item)

    # 根据URL下载视频
    def downloadVideoByURL(self, video_url):
        if video_url is None:
            raise NameError
        else:
            aid = re.findall('.*?av(\d+).*?', video_url)[0]
            self.downVideosByAid(aid)

    # 根据个人的空间地址下载
    def downloadVideoBySpaceLink(self, link):
        mid, cid = re.findall(
            r'https://space\.bilibili\.com/([0-9]+?)/channel/detail\?cid=([0-9]+)', link)[0]
        json_url = self.space_api(mid, cid)
        json_data = json.loads(self.getHtml(json_url))
        if json_data.get('data', 0) != 0:
            aids = [eve['aid']
                    for eve in json_data['data']['list']['archives']]
            for aid in aids:
                print(aid)
                self.downVideosByAid(aid)


if __name__ == '__main__':
    bli = BliVideo(r'G:\02 学习\02 编程\02 Python')
    # url = 'https://www.bilibili.com/video/av46693539?from=search&seid=760363038415890996'
    # bli.downloadVideoByURL(url)
    bli.downloadVideoBySpaceLink(
        'https://space.bilibili.com/20291891/channel/detail?cid=29424')
