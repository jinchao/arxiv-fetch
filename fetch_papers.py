# 按分类（cat）查询arxiv API并下载论文pdf

import os
import time
import random
import urllib.request
import feedparser
import configparser
import pymysql
import json
from utils import Config


def encode_feedparser_dict(d):
    if isinstance(d, feedparser.FeedParserDict) or isinstance(d, dict):
        j = {}
        for k in d.keys():
            j[k] = encode_feedparser_dict(d[k])
        return j
    elif isinstance(d, list):
        l = []
        for k in d:
            l.append(encode_feedparser_dict(k))
        return l
    else:
        return d


# 通过url提取原始id和版本号
def parse_arxiv_url(url):
    ix = url.rfind('/')
    idversion = j['id'][ix + 1:]  # extract just the id (and the version)
    parts = idversion.split('v')
    assert len(parts) == 2, 'error parsing url ' + url
    return parts[0], int(parts[1])


# 获取查询结果，返回dict
def query_result(search_cat, start, max_results):
    base_url = 'http://export.arxiv.org/api/query?'
    query = 'search_query=cat:%s&sortBy=lastUpdatedDate&sortOrder=ascending&start=%i&max_results=%i' % (
        search_cat, start, max_results)
    current_url = base_url + query
    print('当前请求url：%s' % current_url)
    with urllib.request.urlopen(current_url) as url:
        response = url.read()
    res = feedparser.parse(response)
    return res


# 引入数据库配置文件并连接数据库
config = configparser.ConfigParser()
config.read(".env")
db_config = config['db']
# 打开数据库连接
db = pymysql.connect(db_config['host'], db_config['user'], db_config['password'], db_config['database'])
# 使用 cursor() 方法创建一个游标对象 cursor
cursor = db.cursor()

for c in Config.search_cat:
    # 查询参数
    search_cat = c
    # 先查询下当前条件下的结果总数，作为max_index的默认值
    res = query_result(search_cat, 0, 1)
    total_results = res.feed.opensearch_totalresults
    print('当前分类下的结果总数：%s' % total_results)
    # 查询当前分类下已录入的条数
    sql = 'select count(*) from pdf_list where cat=%s;'
    cursor.execute(sql, (search_cat,))
    data = cursor.fetchone()
    have_num = data[0]
    print('本次录入前该分类在数据库中已存在%s条记录' % (have_num,))
    # 查询起始
    start_index = int(have_num)
    # 查询结束
    max_index = int(total_results)
    # 分页参数
    per_iteration = 500
    # 等待时间
    wait_time = 5
    print('当前抓取arXiv的参数为：%s' % (search_cat,))

    # -----------------------------------------------------------------------------
    # fetch主程序
    num_added_total = 0
    for i in range(start_index, max_index, per_iteration):
        # 当arxiv无响应时强制重试
        parse_entries_len = 0
        while parse_entries_len == 0:
            print("当前阶段：%i - %i" % (i, i + per_iteration))
            parse = query_result(search_cat, i, per_iteration)
            total_results = parse.feed.opensearch_totalresults
            print('当前分类下的结果总数：%s' % total_results)
            parse_entries_len = len(parse.entries)
            if parse_entries_len == 0:
                print('arxiv无响应，程序%s秒后重试' % (wait_time,))
                time.sleep(wait_time)
        num_added = 0
        num_skipped = 0
        for e in parse.entries:
            j = encode_feedparser_dict(e)
            # 只提取原始id和版本号
            raw_id, version = parse_arxiv_url(j['id'])
            j['_raw_id'] = raw_id
            j['_version'] = version
            # 查询是否重复录入
            # 1.如果重复，再检查版本是否更新，如果相同版本，略过，如果不同版本，更新
            # 2.如果不重复，新增
            sql = 'select id,version from pdf_list where raw_id=%s;'
            # 在每次运行sql之前，ping一次，如果连接断开就重连
            db.ping(reconnect=True)
            # 使用 execute()  方法执行 SQL 查询
            cursor.execute(sql, (raw_id,))
            # 使用 fetchone() 方法获取单条数据.
            data = cursor.fetchone()
            j_json = json.dumps(j)
            if data:
                # 存在数据
                id = data[0]
                if version > data[1]:
                    print('获取一条旧数据的新版本 raw_id:%s version:%s' % (raw_id, version,))
                    sql = 'update pdf_list set version=%s, res_json=%s where id=%s;'
                    cursor.execute(sql, (version, j_json, id))
                    db.commit()
                    num_added += 1
                    num_added_total += 1
                else:
                    print('跳过一条旧数据 raw_id:%s version:%s' % (raw_id, version,))
                    num_skipped += 1
            else:
                print('获取一条新数据 raw_id:%s version:%s' % (raw_id, version,))
                # 新数据
                sql = 'insert into pdf_list(cat,raw_id,version,res_json) values (%s,%s,%s,%s);'
                cursor.execute(sql, (search_cat, raw_id, version, j_json,))
                db.commit()
                num_added += 1
                num_added_total += 1

        print('本阶段新增 %d 条记录, 已存在（跳过） %d 条记录' % (num_added, num_skipped))
        if num_added == 0:
            print('本阶段没有新的记录被添加')

        print('休息%i秒' % (wait_time,))
        time.sleep(wait_time + random.uniform(0, 3))

# 关闭数据库连接
db.close()
# 保存pdf
os.system("python download_pdfs.py")
