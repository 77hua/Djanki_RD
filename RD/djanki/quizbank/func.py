import os
import re
from django.conf import settings
from urllib.parse import urlparse, unquote

# 删除试题时一起图片
def remove_markdown_images(markdown_text):
    # 正则表达式匹配Markdown图片链接，提取完整的URL
    image_patterns = re.findall(r'!\[.*?\]\((.*?)\)', markdown_text)
    for url in image_patterns:
        # 解析URL获取路径部分，并对路径进行URL解码
        parsed_url = urlparse(url)
        # URL解码，防止路径中的特殊字符问题
        relative_path = unquote(parsed_url.path)
        # 移除URL的/media前缀
        if relative_path.startswith(settings.MEDIA_URL):
            relative_path = relative_path[len(settings.MEDIA_URL):]
        # 正确处理路径中可能的多余斜杠
        relative_path = relative_path.lstrip('/')
        # 完整的文件系统路径
        image_path = os.path.join(relative_path)
        # 检查并删除文件
        if os.path.exists(image_path):
            os.remove(image_path)
