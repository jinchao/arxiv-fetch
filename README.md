# arxiv-fetch
这是一个获取 https://arxiv.org 上所有pdf的脚本，参考 karpathy/arxiv-sanity-preserver。

## 开始使用
1、执行“python fetch_papers.py”，爬取论文信息存入数据库，数据库配置文件为“.env”，运行前需重命名“.env.example”或另存为“.env”并修改数据库连接参数；
2、执行“python download_pdfs.py”，根据数据库中的记录下载论文PDF文件。