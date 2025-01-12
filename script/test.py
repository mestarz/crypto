import core.trader as trader
import numpy as np
from core.cfg import Config


def main():
    cfg = Config("simulation.ini")
    long, short = cfg.api.get_position_size_long_and_short("ARB-USDT-SWAP")
    print(long, short)


if __name__ == "__main__":
    main()
