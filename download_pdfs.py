import os
import time
import shutil
import random
import configparser
import pymysql
import json
from urllib.request import urlopen
from utils import Config

print('开始下载pdf')
timeout_secs = 10  # 超时后放弃该次下载
if not os.path.exists(Config.pdf_dir): os.makedirs(Config.pdf_dir)
have = set(os.listdir(Config.pdf_dir))  # 获取已下载的pdf列表
print(have)
numok = 0
numtot = 0

# 引入数据库配置文件并连接数据库
config = configparser.ConfigParser()
config.read(".env")
db_config = config['db']
# 打开数据库连接
db = pymysql.connect(db_config['host'], db_config['user'], db_config['password'], db_config['database'])
# 使用 cursor() 方法创建一个游标对象 cursor
cursor = db.cursor()
sql = 'select raw_id,res_json from pdf_list;'
cursor.execute(sql)
data = cursor.fetchall()
# 关闭数据库连接
db.close()

for v in data:
    pid = v[0]
    j = json.loads(v[1])
    pdfs = [x['href'] for x in j['links'] if x['type'] == 'application/pdf']
    assert len(pdfs) == 1
    pdf_url = pdfs[0] + '.pdf'
    basename = pdf_url.split('/')[-1]
    fname = os.path.join(Config.pdf_dir, basename)
    numtot += 1
    try:
        if not basename in have:
            print('下载 %s 另存为 %s' % (pdf_url, fname))
            req = urlopen(pdf_url, None, timeout_secs)
            with open(fname, 'wb') as fp:
                shutil.copyfileobj(req, fp)
            time.sleep(0.05 + random.uniform(0, 0.1))
        else:
            print('%s 已下载，跳过' % (fname,))
        numok += 1
    except Exception as e:
        print('下载出错: ', pdf_url)
        print(e)
    print('%d/%d of %d 下载成功.' % (numok, numtot, len(data)))

print('最终下载的pdf数量: %d/%d' % (numok, len(data)))
