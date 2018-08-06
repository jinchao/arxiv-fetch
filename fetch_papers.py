# 查询arxiv API 并下载论文pdf

import os
import time
import random
import argparse
import urllib.request
import feedparser
import configparser
import pymysql
import json


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


if __name__ == "__main__":
    # 引入数据库配置文件并连接数据库
    config = configparser.ConfigParser()
    config.read(".env")
    db_config = config['db']
    # 打开数据库连接
    db = pymysql.connect(db_config['host'], db_config['user'], db_config['password'], db_config['database'])
    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()

    # 关闭数据库连接
    # db.close()

    # 解析输入参数
    parser = argparse.ArgumentParser()
    parser.add_argument('--search-query', type=str,
                        default='cat:cs.AI+OR+cat:cs.AR+OR+cat:cs.CC+OR+cat:cs.CE+OR+cat:cs.CG+OR+cat:cs.CL+OR+cat:cs.CR+OR+cat:cs.CV+OR+cat:cs.CY+OR+cat:cs.DB+OR+cat:cs.DC+OR+cat:cs.DL+OR+cat:cs.DM+OR+cat:cs.DS+OR+cat:cs.ET+OR+cat:cs.FL+OR+cat:cs.GL+OR+cat:cs.GR+OR+cat:cs.GT+OR+cat:cs.HC+OR+cat:cs.IR+OR+cat:cs.IT+OR+cat:cs.LG+OR+cat:cs.LO+OR+cat:cs.MA+OR+cat:cs.MM+OR+cat:cs.MS+OR+cat:cs.NA+OR+cat:cs.NE+OR+cat:cs.NI+OR+cat:cs.OH+OR+cat:cs.OS+OR+cat:cs.PF+OR+cat:cs.PL+OR+cat:cs.RO+OR+cat:cs.SC+OR+cat:cs.SD+OR+cat:cs.SE+OR+cat:cs.SI+OR+cat:cs.SY',
                        help='query used for arxiv API. See http://arxiv.org/help/api/user-manual#detailed_examples')
    parser.add_argument('--start-index', type=int, default=0, help='0 = most recent API result')
    parser.add_argument('--max-index', type=int, default=100, help='upper bound on paper index we will fetch')
    parser.add_argument('--results-per-iteration', type=int, default=100, help='passed to arxiv API')
    parser.add_argument('--wait-time', type=float, default=5.0,
                        help='lets be gentle to arxiv API (in number of seconds)')
    parser.add_argument('--break-on-no-added', type=int, default=1,
                        help='break out early if all returned query papers are already in db? 1=yes, 0=no')
    args = parser.parse_args()

    base_url = 'http://export.arxiv.org/api/query?'  # base api query url
    print('抓取arXiv的参数为：%s' % (args.search_query,))

    # -----------------------------------------------------------------------------
    # fetch主程序
    sql = 'select count(*) from pdf_list;'
    cursor.execute(sql)
    data = cursor.fetchone()
    print('数据库在本次录入前已存在%s条记录' % (data[0],))
    num_added_total = 0
    for i in range(args.start_index, args.max_index, args.results_per_iteration):
        print("当前阶段：%i - %i" % (i, i + args.results_per_iteration))
        query = 'search_query=%s&sortBy=lastUpdatedDate&sortOrder=ascending&start=%i&max_results=%i' % (
            args.search_query,
            i, args.results_per_iteration)
        with urllib.request.urlopen(base_url + query) as url:
            response = url.read()
        parse = feedparser.parse(response)
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
                sql = 'insert into pdf_list(raw_id,version, res_json) values (%s,%s,%s);'
                cursor.execute(sql, (raw_id, version, j_json,))
                db.commit()
                num_added += 1
                num_added_total += 1
            # exit()

        print('本阶段新增 %d 条记录, 已存在（跳过） %d 条记录' % (num_added, num_skipped))

        if len(parse.entries) == 0:
            print('arxiv无响应')
            print(response)
            break

        if num_added == 0 and args.break_on_no_added == 1:
            print('没有新的文件被添加，程序退出')
            break

        print('休息%i秒' % (args.wait_time,))
        time.sleep(args.wait_time + random.uniform(0, 3))

    # 保存pdf
    os.system("download_pdfs.py")
