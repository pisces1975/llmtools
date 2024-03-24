import hashlib

def generate_sha_digest(input_string):
    sha256 = hashlib.sha256()  # 使用SHA-256算法
    sha256.update(input_string.encode('utf-8'))  # 将输入字符串编码并更新摘要对象
    digest = sha256.hexdigest()  # 获取摘要的16进制表示
    return digest