import multiprocessing

# 绑定的IP和端口
bind = "0.0.0.0:8888"

# 工作进程数，通常设置为CPU核心数的2-4倍
workers = multiprocessing.cpu_count() * 2 + 1

# 工作模式
worker_class = "gevent"

# 超时时间
timeout = 30

# 日志设置
accesslog = "access.log"
errorlog = "error.log"
loglevel = "info"
