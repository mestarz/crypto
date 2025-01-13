from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64

# AES配置（必须与加密配置一致）
KEY = b'0123456789abcdef0123456789abcdef'  # 32字节密钥（AES-256）
IV = b'abcdef0123456789'   # 16字节IV

def aes_decrypt(encrypted_text):
    """解密AES加密的字符串"""
    try:
        cipher = AES.new(KEY, AES.MODE_CBC, IV)
        decrypted_bytes = cipher.decrypt(base64.b64decode(encrypted_text))
        return unpad(decrypted_bytes, AES.block_size).decode()
    except Exception as e:
        print(f"解密失败: {str(e)}")
        return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("用法: python3 decrypt.py <加密字符串>")
        sys.exit(1)
    
    encrypted_text = sys.argv[1]
    decrypted = aes_decrypt(encrypted_text)
    if decrypted:
        print(f"解密结果: {decrypted}")
