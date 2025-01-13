import configparser
import os
import shutil
from Cython.Build import cythonize
from setuptools import Extension, setup
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import base64

# AES加密配置
KEY = b"0123456789abcdef0123456789abcdef"  # 32字节密钥（AES-256）
IV = b"abcdef0123456789"  # 16字节IV


def aes_encrypt(text):
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    ct_bytes = cipher.encrypt(pad(text.encode(), AES.block_size))
    return base64.b64encode(ct_bytes).decode()


def build_so():
    # 确保config目录存在
    os.makedirs("config", exist_ok=True)

    # 遍历tools目录下的所有.ini文件
    for ini_file in os.listdir("tools"):
        if not ini_file.endswith(".ini"):
            continue

        # 读取配置文件
        config = configparser.ConfigParser()
        config.read(f"tools/{ini_file}")

        # 获取ACCOUNT部分所有键值对并加密
        encrypted_data = {}
        for key, value in config.items("ACCOUNT"):
            encrypted_data[key] = aes_encrypt(value)

        # 生成cfg.pyx
        pyx_content = """from typing import Dict

encrypted_data: Dict[str, str] = {
"""
        for key, value in encrypted_data.items():
            pyx_content += f'    "{key}": "{value}",\n'
        pyx_content += '''}

def get_encrypted_value(key: str) -> str:
    """获取指定key的加密值"""
    return encrypted_data.get(key, "")

def get_all_encrypted_values() -> Dict[str, str]:
    """获取所有加密值"""
    return encrypted_data
'''

        # 获取ini文件名
        ini_name = os.path.splitext(ini_file)[0]

        # 生成对应ini文件名的pyx文件
        pyx_filename = f"{ini_name}.pyx"
        with open(pyx_filename, "w") as f:
            f.write(pyx_content)

        # 编译为.so
        ext = Extension(ini_name, sources=[pyx_filename])
        setup(name=ini_name, ext_modules=cythonize([ext]), script_args=["build_ext", "--inplace"])

        # 移动.so文件到config目录
        so_file = f"{ini_name}.cpython-39-x86_64-linux-gnu.so"
        if os.path.exists(so_file):
            shutil.move(so_file, f"config/{so_file}")

        # 清理临时文件
        os.remove(pyx_filename)

        # 清理编译生成的文件
        if os.path.exists(f"{ini_name}.c"):
            os.remove(f"{ini_name}.c")

        # 清理临时生成的文件
        if os.path.exists(f"{ini_name}.html"):
            os.remove(f"{ini_name}.html")
        if os.path.exists(f"{ini_name}.cpp"):
            os.remove(f"{ini_name}.cpp")

    if os.path.exists("build"):
        shutil.rmtree("build")


if __name__ == "__main__":
    build_so()
