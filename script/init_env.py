import os

def load_env_variables():
    with open(os.path.join(os.path.dirname(__file__), '../config/simulation.sh')) as file:
        for line in file:
            if line.startswith('export '):
                key, value = line.replace('export ', '', 1).strip().split('=', 1)
                os.environ[key] = value
    # 覆盖 OKX_PROXY
    os.environ['OKX_PROXY'] = 'http://127.0.0.1:20171'

# 调用函数以加载环境变量
load_env_variables()
