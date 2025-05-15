#!/usr/bin/env python3
"""
将vim文档转换为简单的HTML格式
原作者: Sirtaj Singh Kang (taj@kde.org)
Python版本: Restorer
"""

import sys
import os
from datetime import datetime
import re
from typing import Dict, List, Tuple

class VimHtml:
    def __init__(self):
        self.url: Dict[str, str] = {}
        now = datetime.now()
        self.date = f"{now.day}.{now.month}.{now.year}"

    def map_link(self, tag: str) -> str:
        """将标签映射到HTML链接"""
        if tag in self.url:
            return self.url[tag]
        # 未知的超链接目标
        tag = tag.replace('.txt', '')
        tag = tag.replace('<', '&lt;').replace('>', '&gt;')
        return f'<code class="badlink">{tag}</code>'

    def read_tag_file(self, tagfile: str) -> None:
        """读取标签文件"""
        try:
            with open(tagfile, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip() or line.startswith('!'):
                        continue
                    
                    parts = line.split(None, 2)
                    if len(parts) < 2:
                        continue

                    tag, filename = parts[0:2]
                    label = tag.replace('.txt', '')
                    filename = filename.replace('.txt', '.html')
                    
                    self.url[tag] = f'<a href="{filename}#{self.esc_url(tag)}">{self.esc_text(label)}</a>'
        except IOError as e:
            print(f"无法读取标签文件: {e}", file=sys.stderr)
            sys.exit(1)

    @staticmethod
    def esc_text(text: str) -> str:
        """转义HTML文本"""
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    @staticmethod
    def esc_url(url: str) -> str:
        """转义URL中的特殊字符"""
        replacements = {
            '"': '%22', '~': '%7E', '<': '%3C', '>': '%3E',
            '=': '%20', '#': '%23', '/': '%2F'
        }
        for char, repl in replacements.items():
            url = url.replace(char, repl)
        return url

    def process_line(self, line: str, original_line: str) -> str:
        """处理单行文本"""
        parts = []
        pos = 0
        
        pattern = r'(\|[^|]+\||\*[^*]+\*)'
        
        for match in re.finditer(pattern, line):
            if match.start() > pos:
                parts.append(self._format_text(line[pos:match.start()], original_line))
            
            token = match.group(1)
            if token.startswith('|'):
                tag = token[1:-1]
                parts.append(f"|{self.map_link(tag)}|")
            else:
                tag = token[1:-1]
                parts.append(
                    f'<b class="vimtag">*<a name="{self.esc_url(tag)}">'
                    f'{self.esc_text(tag)}</a>*</b>'
                )
            
            pos = match.end()
            
        if pos < len(line):
            parts.append(self._format_text(line[pos:], original_line))
            
        return ''.join(parts)

    def _format_text(self, text: str, original_line: str) -> str:
        """格式化普通文本，处理各种vim高亮"""
        text = self.esc_text(text)
        
        text = re.sub(r'CTRL-(\w+)', r'<code class="keystroke">CTRL-\1</code>', text)
        text = re.sub(r'&lt;(.*?)&gt;', r'<code class="special">&lt;\1&gt;</code>', text)
        text = re.sub(r'\{([^}]*)\}', r'<code class="special">{\1}</code>', text)
        text = re.sub(r'\[(range|line|count|offset|cmd|[-+]?num)\]',
                     r'<code class="special">[\1]</code>', text)
        text = re.sub(r'(Note:?)', r'<code class="note">\1</code>', text, flags=re.IGNORECASE)
        
        # 处理以~结尾的行
        if original_line.rstrip().endswith('~'):
            stripped = text.rstrip().rstrip('~')
            if stripped:  # 只有当文本非空时才添加section样式
                # 保留表格行的格式
                if 'WHAT' in original_line and 'PREPEND' in original_line and 'EXAMPLE' in original_line:
                    # 处理表格标题行，保留原始对齐
                    return f'<code class="section">{stripped}</code>~'
                return f'<code class="section">{stripped}</code>'
            
        return text

    def get_indent(self, line: str) -> str:
        """获取行的缩进"""
        if not line:
            return ''
        match = re.match(r'^(\s+)', line)
        if match:
            indent = match.group(1)
            if '\t' in indent:
                indent = ' ' * (len(indent) * 8)
            return indent
        return ''

    def vim2html(self, infile: str) -> None:
        """将vim文档转换为HTML"""
        try:
            outfile = os.path.basename(infile).replace('.txt', '')
            head = outfile.upper()
            
            with open(infile, 'r', encoding='utf-8') as fin, \
                 open(f"{outfile}.html", 'w', encoding='utf-8') as fout:
                
                # 写入HTML头部
                fout.write(f'''<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
<title>VIM: {head}</title>
<link rel="stylesheet" href="vim-stylesheet.css" type="text/css">
</head>
<body>
<h2>{head}</h2>
<pre>
''')
                
                in_example = 0
                prev_line_empty = False
                
                for line in fin:
                    original_line = line
                    line = line.rstrip()
                    
                    # 处理分隔线
                    if re.match(r'^\s*[-=]+\s*$', line):
                        if prev_line_empty:
                            fout.write('</pre><hr><pre>')
                        else:
                            fout.write('\n</pre><hr><pre>')
                        prev_line_empty = False
                        continue
                    
                    # 处理示例
                    if line.endswith('>'):
                        if line == '>' or line.endswith(' >'):
                            in_example = 1
                            line = line[:-1]
                    elif in_example and line and not line[0].isspace():
                        in_example = 0
                        if line.startswith('<'):
                            line = line[1:]
                    
                    # 获取原始缩进
                    indent = self.get_indent(original_line)
                    processed_line = self.process_line(line, original_line)
                    
                    # # 添加波浪号
                    # if self.should_add_tilde(processed_line, original_line):
                    #     processed_line += '~'
                    
                    # 保持原始缩进
                    if processed_line.strip():
                        processed_line = indent + processed_line.lstrip()
                    
                    # 处理空行
                    if not processed_line.strip():
                        if not prev_line_empty:
                            fout.write('\n')
                            prev_line_empty = True
                        continue
                    
                    # 输出行
                    if in_example == 2:
                        fout.write(f'<code class="example">{processed_line}</code>\n')
                    else:
                        fout.write(f'{processed_line}\n')
                    
                    prev_line_empty = False
                    
                    if in_example == 1:
                        in_example = 2
                
                # 写入HTML尾部
                fout.write(f'''</pre>
<p><i>Generated by vim2html on {self.date}</i></p>
</body>
</html>
''')

        except IOError as e:
            print(f"处理文件 {infile} 时出错: {e}", file=sys.stderr)

    def write_css(self) -> None:
        """生成CSS样式表"""
        try:
            with open('vim-stylesheet.css', 'w', encoding='utf-8') as f:
                f.write("""body { background-color: white; color: black;}
:link { color: rgb(0,137,139); }
:visited { color: rgb(0,100,100);
           background-color: white; /* should be inherit */ }
:active { color: rgb(0,200,200);
          background-color: white; /* should be inherit */ }

B.vimtag { color : rgb(250,0,250); }

h1, h2 { color: rgb(82,80,82); text-align: center; }
h3, h4, h5, h6 { color: rgb(82,80,82); }
.headline { color: rgb(0,137,139); }
.header { color: rgb(164, 32, 246); }
.section { color: rgb(164, 32, 246); }
.keystroke { color: rgb(106, 89, 205); }
.vim { }
.example { color: rgb(0, 0, 255); }
.option { }
.notvi { }
.special { color: rgb(106, 89, 205); }
.note { color: blue; background-color: yellow; }
.sub {}
.badlink { color: rgb(0,37,39); }""")
        except IOError as e:
            print(f"无法写入样式表: {e}", file=sys.stderr)

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("""vim2html.py: 将vim文档转换为HTML格式。
用法：
    vim2html.py <标签文件> <文本文件...>""", file=sys.stderr)
        sys.exit(1)

    converter = VimHtml()
    
    print("处理标签...")
    converter.read_tag_file(sys.argv[1])

    for filename in sys.argv[2:]:
        print(f"处理 {filename}...")
        converter.vim2html(filename)

    print("写入样式表...")
    converter.write_css()
    print("完成。")

if __name__ == "__main__":
    main() 