# arxiv-fetch
这是一个按分类（cat）获取 https://arxiv.org 上所有pdf的脚本（Python 3.0+），参考 karpathy/arxiv-sanity-preserver。

## 准备
> 1. 数据库结构文件为pdf_list.sql，仅支持MySQL/MariaDB，如需支持其他数据库请自行修改代码。
> 2. 数据库配置文件为“.env”，请重命名“.env.example”或另存为“.env”并修改连接参数。
> 3. 分类在utils.py文件中的search_cat元组里设置，全部分类请查看 https://arxiv.org/help/api/user-manual#subject_classifications 。
> 4. 最好使用国外代理，不然下载pdf很慢，且容易导致文件不完整，如果仅仅把信息收录数据库并不下载文件，那不用代理也没关系。
## 开始使用
> 1. 执行“python fetch_papers.py”，爬取论文信息，并将未录入的存入数据库。
> 2. 执行“python download_pdfs.py”，根据数据库中的记录下载论文pdf文件，已下载的自动忽略。