from core.cfg import Config
from core.real import OKXExecute
from core.rsigrid import RSIGrid


def main():
    cfg = Config("simulation.ini")
    _exec = OKXExecute(cfg)
    _strategy = RSIGrid(_exec, cfg)
    _strategy.run()


if __name__ == "__main__":
    main()
