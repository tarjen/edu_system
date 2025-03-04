import os
import ast
from typing import List, Dict
import re

def generate_api_docs(source_dir: str, output_md: str = "API_DOCUMENTATION.md"):
    """
    生成 API 文档生成器
    
    Args:
        source_dir (str): 要扫描的源代码目录路径
        output_md (str): 生成的 Markdown 文件路径
    """
    
    # 存储所有 API 信息的列表
    api_collection: List[Dict] = []
    
    # 遍历目录树
    for root, _, files in os.walk(source_dir):
        for filename in files:
            if not filename.endswith('.py'):
                continue
                
            filepath = os.path.join(root, filename)

            rel_path = os.path.relpath(filepath, start=source_dir)
            rel_path = rel_path.replace('\\', '/')  # 统一使用斜杠
            
            # 解析每个 Python 文件
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
                
            # 查找路由函数
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    api_info = extract_route_info(node, rel_path)
                    if api_info:
                        api_collection.append(api_info)
    
    # 生成 Markdown 文档
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write(build_markdown_content(api_collection))

def extract_route_info(func_node: ast.FunctionDef, filename: str) -> Dict:
    """
    提取路由函数信息
    
    Args:
        func_node (ast.FunctionDef): AST 函数节点
        filename (str): 所属文件名
    
    Returns:
        Dict: 包含路由信息的字典
    """
    route_info = {
        'file': filename,
        'path': None,
        'methods': ['GET'],
        'description': '',
        'args': [],
        'returns': ''
    }
    
    # 检查路由装饰器
    for decorator in func_node.decorator_list:
        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
            if decorator.func.attr == 'route' and isinstance(decorator.func.value, ast.Name) and decorator.func.value.id == 'app':
                # 提取路径
                route_info['path'] = decorator.args[0].s
                
                # 提取 HTTP 方法
                for keyword in decorator.keywords:
                    if keyword.arg == 'methods':
                        route_info['methods'] = [elt.s for elt in keyword.value.elts]
    
    if not route_info['path']:
        return None
    
    # 解析文档字符串
    docstring = ast.get_docstring(func_node) or ''
    route_info.update(parse_google_docstring(docstring))
    
    return route_info

def parse_google_docstring(docstring: str) -> Dict:
    """
    解析 Google 风格文档字符串
    
    Returns:
        Dict: 包含解析后的文档结构
    """
    parsed = {
        'description': '',
        'args': [],
        'returns': ''
    }
    
    sections = re.split(r'\n\s*(Args|Returns):\s*\n', docstring)
    parsed['description'] = sections[0].strip()
    
    # 解析参数
    if 'Args' in sections:
        args_index = sections.index('Args') + 1
        args_text = sections[args_index].strip()
        parsed['args'] = [
            parse_param_line(line) 
            for line in args_text.split('\n') 
            if line.strip()
        ]
    
    # 解析返回说明
    if 'Returns' in sections:
        returns_index = sections.index('Returns') + 1
        parsed['returns'] = sections[returns_index].strip()
    
    return parsed

def parse_param_line(line: str) -> Dict:
    """
    解析单个参数行
    
    Example:
        "title (str, 可选): 比赛标题模糊搜索关键词"
    """
    match = re.match(r"(\w+)\s*(\(.*?\))?\s*:\s*(.+)", line.strip())
    if not match:
        return {'name': '', 'type': '', 'desc': line.strip()}
    
    name, type_info, desc = match.groups()
    return {
        'name': name.strip(),
        'type': (type_info or '').strip('() ') or 'Any',
        'desc': desc.strip()
    }

def build_markdown_content(api_collection: List[Dict]) -> str:
    """
    构建符合示例格式的Markdown内容
    """
    md = ["# API 文档\n"]
    
    for api in api_collection:
        # 路由标题（带HTTP方法）
        md.append(f"## `{api['path']}` ({', '.join(api['methods'])})")
        
        # 文件位置
        md.append(f"*文件位置*: `{api['file']}`\n")
        
        # 描述部分
        if api['description']:
            md.append(f"**描述**: {api['description']}\n")
        
        # 参数说明
        if api['args']:
            md.append("### 参数说明")
            for arg in api['args']:
                # 过滤空参数名（如通过JWT获取的情况）
                if arg['name']:
                    type_info = f"({arg['type']})" if arg['type'] else ""
                    md.append(f"- `{arg['name']}` {type_info}: {arg['desc']}")
                else:
                    md.append(f"- {arg['desc']}")  # 处理无参数名的说明
        
        # 返回结构
        if api['returns']:
            md.append("### 返回结构")
            md.append(f"```\n{api['returns']}\n```")
        
        md.append("\n---\n")
    
    return '\n'.join(md)

# 其余函数保持不变，只需替换原来的build_markdown_content函数


if __name__ == '__main__':
    # 使用示例：扫描当前目录，生成到当前目录的 API.md
    generate_api_docs(source_dir='./')
