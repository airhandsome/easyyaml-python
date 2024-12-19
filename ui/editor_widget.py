from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit
from PyQt6.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat
import re

class YamlHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        
        # YAML语法高亮规则
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(Qt.GlobalColor.blue)
        keywords = ['true', 'false', 'null']
        
        for word in keywords:
            pattern = f'\\b{word}\\b'
            self.highlighting_rules.append((re.compile(pattern), keyword_format))

class YamlEditorWidget(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.setup_editor()
        
    def setup_editor(self):
        # 设置等宽字体
        font = QFont("Courier New", 10)
        self.setFont(font)
        
        # 启用语法高亮
        self.highlighter = YamlHighlighter(self.document())
        
        # 设置制表符宽度
        self.setTabStopDistance(40) 