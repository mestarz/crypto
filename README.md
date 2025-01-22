# crypto 工具为辅，主观为主

加密策略执行工具

> 编辑`config`文件夹下的`*.ini`配置文件
```
# config.ini
[DEFAULT]
simulate = True
api_debug = False

[TRADE]
coin = ARB-USDT-SWAP
period = 1m
lever = 10
ccy = USDT
reserved = 100
order_wait = 20
max_buy_chance = 8
trade_timeperiod = 1

[FACTOR]
rsi_timeperiod = 14
ma_fast_timeperiod = 6
ma_slow_timeperiod = 14
rsi_down = 30
rsi_up = 70

[LOG]
filename = rsigrid.log
level = DEBUG
```
> 导入环境变量
```
# 环境变量
export OKX_PROX`=http://192.168.3.17:20171
export OKX_APIKEY=xxx
export OKX_SECRETKEY=xxx
export OKX_PASSPHRASE=xxx
```