from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QCheckBox, QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal

class FindDialog(QDialog):
    findNext = pyqtSignal(str, bool, bool)  # 文本, 是否区分大小写, 是否向上搜索
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("查找")
        self.setModal(False)  # 非模态对话框
        
        # 主布局
        layout = QVBoxLayout(self)
        
        # 查找输入框
        find_layout = QHBoxLayout()
        find_layout.addWidget(QLabel("查找内容:"))
        self.find_edit = QLineEdit()
        self.find_edit.textChanged.connect(self.validate_input)
        find_layout.addWidget(self.find_edit)
        layout.addLayout(find_layout)
        
        # 选项组
        options_group = QGroupBox("选项")
        options_layout = QVBoxLayout(options_group)
        
        self.case_sensitive = QCheckBox("区分大小写")
        options_layout.addWidget(self.case_sensitive)
        
        self.search_up = QCheckBox("向上搜索")
        options_layout.addWidget(self.search_up)
        
        layout.addWidget(options_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.find_button = QPushButton("查找下一个")
        self.find_button.setEnabled(False)
        self.find_button.clicked.connect(self.find_clicked)
        button_layout.addWidget(self.find_button)
        
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def validate_input(self, text):
        """验证输入，启用/禁用查找按钮"""
        self.find_button.setEnabled(bool(text))
    
    def find_clicked(self):
        """发送查找信号"""
        text = self.find_edit.text()
        case_sensitive = self.case_sensitive.isChecked()
        search_up = self.search_up.isChecked()
        self.findNext.emit(text, case_sensitive, search_up)
    
    def set_find_text(self, text):
        """设置查找文本"""
        self.find_edit.setText(text)
        self.find_edit.selectAll()
        self.find_edit.setFocus()

class ReplaceDialog(QDialog):
    findNext = pyqtSignal(str, bool, bool)  # 文本, 是否区分大小写, 是否向上搜索
    replace = pyqtSignal(str)  # 替换文本
    replaceAll = pyqtSignal(str, str, bool)  # 查找文本, 替换文本, 是否区分大小写
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("替换")
        self.setModal(False)
        
        # 主布局
        layout = QVBoxLayout(self)
        
        # 查找输入框
        find_layout = QHBoxLayout()
        find_layout.addWidget(QLabel("查找内容:"))
        self.find_edit = QLineEdit()
        self.find_edit.textChanged.connect(self.validate_input)
        find_layout.addWidget(self.find_edit)
        layout.addLayout(find_layout)
        
        # 替换输入框
        replace_layout = QHBoxLayout()
        replace_layout.addWidget(QLabel("替换为:"))
        self.replace_edit = QLineEdit()
        replace_layout.addWidget(self.replace_edit)
        layout.addLayout(replace_layout)
        
        # 选项组
        options_group = QGroupBox("选项")
        options_layout = QVBoxLayout(options_group)
        
        self.case_sensitive = QCheckBox("区分大小写")
        options_layout.addWidget(self.case_sensitive)
        
        self.search_up = QCheckBox("向上搜索")
        options_layout.addWidget(self.search_up)
        
        layout.addWidget(options_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.find_button = QPushButton("查找下一个")
        self.find_button.setEnabled(False)
        self.find_button.clicked.connect(self.find_clicked)
        button_layout.addWidget(self.find_button)
        
        self.replace_button = QPushButton("替换")
        self.replace_button.setEnabled(False)
        self.replace_button.clicked.connect(self.replace_clicked)
        button_layout.addWidget(self.replace_button)
        
        self.replace_all_button = QPushButton("全部替换")
        self.replace_all_button.setEnabled(False)
        self.replace_all_button.clicked.connect(self.replace_all_clicked)
        button_layout.addWidget(self.replace_all_button)
        
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def validate_input(self, text):
        """验证输入，启用/禁用按钮"""
        enabled = bool(text)
        self.find_button.setEnabled(enabled)
        self.replace_button.setEnabled(enabled)
        self.replace_all_button.setEnabled(enabled)
    
    def find_clicked(self):
        """发送查找信号"""
        text = self.find_edit.text()
        case_sensitive = self.case_sensitive.isChecked()
        search_up = self.search_up.isChecked()
        self.findNext.emit(text, case_sensitive, search_up)
    
    def replace_clicked(self):
        """发送替换信号"""
        self.replace.emit(self.replace_edit.text())
    
    def replace_all_clicked(self):
        """发送全部替换信号"""
        find_text = self.find_edit.text()
        replace_text = self.replace_edit.text()
        case_sensitive = self.case_sensitive.isChecked()
        self.replaceAll.emit(find_text, replace_text, case_sensitive)
    
    def set_find_text(self, text):
        """设置查找文本"""
        self.find_edit.setText(text)
        self.find_edit.selectAll()
        self.find_edit.setFocus() 