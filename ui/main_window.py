from PyQt6.QtWidgets import (QMainWindow, QToolBar, QMenuBar,
                             QFileDialog, QMessageBox, QVBoxLayout,
                             QWidget, QTabWidget, QComboBox, QTabBar, QMenu,
                             QDialog, QLabel, QLineEdit, QDialogButtonBox,
                             QPushButton, QHBoxLayout, QCompleter, QTreeWidget, QTreeWidgetItem,
                             QPlainTextEdit, QSplitter, QStackedWidget)
from PyQt6.QtCore import Qt, QStringListModel, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut, QAction
import os
import json
import shutil
from .editor_widget import YamlEditorWidget
from .yaml_editor_widget import YamlEditorWidget

class SearchComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.setMaxVisibleItems(10)
        self.setMaxCount(50)
        self.setMinimumWidth(200)
        
        # 设置占位符文本
        self.lineEdit().setPlaceholderText("搜索模板...")
        
        # 使用定时器延迟搜索
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300)  # 300ms 延迟
        
        # 当文本改变时触发搜索
        self.lineEdit().textChanged.connect(self.on_text_changed)
        
        # 初始状态
        self.setCurrentText("")
    
    def on_text_changed(self, text):
        """当输入文本改变时"""
        self.search_timer.stop()
        if text:
            self.search_timer.start()
    
    def focusInEvent(self, event):
        """当获得焦点时"""
        super().focusInEvent(event)
    
    def mousePressEvent(self, event):
        """点击时才显示下拉列表"""
        super().mousePressEvent(event)
        if self.currentText():
            self.showPopup()

class DraggableTabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setElideMode(Qt.TextElideMode.ElideRight)
        self.setExpanding(False)
        self.setMovable(True)
        
        self.setup_shortcuts()
    
    def setup_shortcuts(self):
        next_tab = QShortcut(QKeySequence("Ctrl+Tab"), self)
        next_tab.activated.connect(self.next_tab)
        
        prev_tab = QShortcut(QKeySequence("Ctrl+Shift+Tab"), self)
        prev_tab.activated.connect(self.prev_tab)
        
        move_left = QShortcut(QKeySequence("Alt+Left"), self)
        move_left.activated.connect(self.move_current_tab_left)
        
        move_right = QShortcut(QKeySequence("Alt+Right"), self)
        move_right.activated.connect(self.move_current_tab_right)
    
    def next_tab(self):
        if self.count() > 1:
            current = self.parent().currentIndex()
            next_index = (current + 1) % self.count()
            self.parent().setCurrentIndex(next_index)
    
    def prev_tab(self):
        if self.count() > 1:
            current = self.parent().currentIndex()
            prev_index = (current - 1) % self.count()
            self.parent().setCurrentIndex(prev_index)
    
    def move_current_tab_left(self):
        current = self.parent().currentIndex()
        self.parent().move_tab_left(current)
    
    def move_current_tab_right(self):
        current = self.parent().currentIndex()
        self.parent().move_tab_right(current)

class DraggableTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 确保这些属性按正确顺序设置
        self.setMovable(True)
        self.setTabsClosable(True)  # 启用关闭按钮
        self.setDocumentMode(True)
        self.setAcceptDrops(True)
        
        # 设置标签栏样式
        self.setStyleSheet("""
            QTabBar::close-button {
                image: url(close.png);
                subcontrol-position: right;
                margin: 2px;
            }
            QTabBar::close-button:hover {
                background: rgba(255, 0, 0, 0.1);
            }
        """)
        
        # 自定义标签栏
        self.tab_bar = DraggableTabBar(self)
        self.setTabBar(self.tab_bar)
        
        # 连接关闭信号
        self.tabCloseRequested.connect(self.close_tab)
    
    def show_tab_context_menu(self, position):
        """显示标签页右键菜单"""
        tab_index = self.tabBar().tabAt(position)
        if tab_index < 0:
            return
            
        menu = QMenu(self)
        
        # 移动到左边
        if tab_index > 0:
            move_left = QAction("移到左边", self)
            move_left.triggered.connect(lambda: self.move_tab_left(tab_index))
            menu.addAction(move_left)
        
        # 移动到右边
        if tab_index < self.count() - 1:
            move_right = QAction("移到右边", self)
            move_right.triggered.connect(lambda: self.move_tab_right(tab_index))
            menu.addAction(move_right)
        
        # 移动到开头
        if tab_index > 0:
            move_first = QAction("移到开头", self)
            move_first.triggered.connect(lambda: self.move_tab_to(tab_index, 0))
            menu.addAction(move_first)
        
        # 移动到末尾
        if tab_index < self.count() - 1:
            move_last = QAction("移到末尾", self)
            move_last.triggered.connect(lambda: self.move_tab_to(tab_index, self.count() - 1))
            menu.addAction(move_last)
        
        menu.addSeparator()
        
        # 关闭标签页
        close_tab = QAction("关闭", self)
        close_tab.triggered.connect(lambda: self.tabCloseRequested.emit(tab_index))
        menu.addAction(close_tab)
        
        # 关闭其他标签页
        if self.count() > 1:
            close_others = QAction("关闭其他", self)
            close_others.triggered.connect(lambda: self.close_other_tabs(tab_index))
            menu.addAction(close_others)
        
        menu.exec(self.mapToGlobal(position))
    
    def move_tab_left(self, index):
        """将标签页向左移动一位"""
        if index > 0:
            self.move_tab_to(index, index - 1)
    
    def move_tab_right(self, index):
        """将标签页向右移动一位"""
        if index < self.count() - 1:
            self.move_tab_to(index, index + 1)
    
    def move_tab_to(self, from_index, to_index):
        """将标签页移动到指定位置"""
        # 保存当前标签页信息
        widget = self.widget(from_index)
        text = self.tabText(from_index)
        icon = self.tabIcon(from_index)
        whats_this = self.tabWhatsThis(from_index)
        tool_tip = self.tabToolTip(from_index)
        
        # 移除原标签页
        self.removeTab(from_index)
        
        # 在新位置插入标签页
        self.insertTab(to_index, widget, icon, text)
        
        # 恢复标签页信息
        self.setTabWhatsThis(to_index, whats_this)
        self.setTabToolTip(to_index, tool_tip)
        
        # 选中移动后的标签页
        self.setCurrentIndex(to_index)
    
    def close_other_tabs(self, keep_index):
        """关闭除指定索引外的所有标签页"""
        for i in range(self.count() - 1, -1, -1):
            if i != keep_index:
                self.tabCloseRequested.emit(i)
    
    def close_tab(self, index):
        """关闭标签页"""
        # 获取要关闭的编辑器
        editor = self.widget(index)
        
        # 如果文件已修改，提示保存
        if hasattr(editor, 'document') and editor.document().isModified():
            reply = QMessageBox.question(self, '保存确认',
                "文件已修改，是否保存？",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel)
            
            if reply == QMessageBox.StandardButton.Save:
                # 触发保存操作
                self.parent().save_file()
            elif reply == QMessageBox.StandardButton.Cancel:
                return
        
        # 关闭标签页
        self.removeTab(index)
        
        # 清理编辑器
        if editor:
            editor.deleteLater()

class AddTemplateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加自定义模板")
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        name_layout = QHBoxLayout()
        name_label = QLabel("模板名称:", self)
        self.name_edit = QLineEdit(self)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        category_layout = QHBoxLayout()
        category_label = QLabel("模板分类:", self)
        self.category_edit = QLineEdit(self)
        self.category_edit.setPlaceholderText("例如: k8s, docker, server")
        category_layout.addWidget(category_label)
        category_layout.addWidget(self.category_edit)
        layout.addLayout(category_layout)
        
        self.file_path = None
        file_layout = QHBoxLayout()
        self.file_label = QLabel("未选择文件", self)
        select_button = QPushButton("选择文件", self)
        select_button.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(select_button)
        layout.addLayout(file_layout)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择模板文件", "", "YAML files (*.yaml *.yml)")
        if file_path:
            self.file_path = file_path
            self.file_label.setText(os.path.basename(file_path))

class ManageTemplatesDialog(QDialog):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setWindowTitle("模板管理")
        self.setModal(True)
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # 创建树形视图显示模板
        self.tree = QTreeWidget(self)
        self.tree.setHeaderLabels(["模板名称", "路径"])
        self.tree.setColumnWidth(0, 250)
        layout.addWidget(self.tree)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("添加模板", self)
        self.add_btn.clicked.connect(self.add_template)
        
        self.delete_btn = QPushButton("删除模板", self)
        self.delete_btn.clicked.connect(self.delete_template)
        
        self.rename_btn = QPushButton("重命名", self)
        self.rename_btn.clicked.connect(self.rename_template)
        
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.rename_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # 加载模板
        self.load_templates()
    
    def load_templates(self):
        """加载模板到树形视图"""
        self.tree.clear()
        
        # 创建分类节点
        categories = {}
        
        # 加载内置模板
        for template in self.main_window.template_list:
            if not template.startswith('user/'):
                category = os.path.dirname(template)
                if not category:
                    category = "未分类"
                
                if category not in categories:
                    categories[category] = QTreeWidgetItem(self.tree, [category])
                
                template_name = os.path.basename(template).replace('.yaml', '')
                QTreeWidgetItem(categories[category], [template_name, template])
        
        # 加载用户模板
        if hasattr(self.main_window, 'user_templates'):
            for category, templates in self.main_window.user_templates.items():
                if category not in categories:
                    categories[category] = QTreeWidgetItem(self.tree, [category])
                
                for name, info in templates.items():
                    QTreeWidgetItem(categories[category], [name, f"user/{info['path']}"])
        
        self.tree.expandAll()
    
    def add_template(self):
        """添加新模板"""
        dialog = AddTemplateDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.main_window.add_template_from_dialog(dialog)
            self.load_templates()
    
    def delete_template(self):
        """删除选中的模板"""
        current_item = self.tree.currentItem()
        if not current_item or not current_item.parent():
            QMessageBox.warning(self, "警告", "请选择要删除的模板")
            return
        
        template_path = current_item.text(1)
        if not template_path.startswith('user/'):
            QMessageBox.warning(self, "警告", "只能删除用户自定义模板")
            return
        
        reply = QMessageBox.question(self, '确认删除',
            "确定要删除这个模板吗？此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 从文件系统删除
                full_path = os.path.join(self.main_window.user_template_dir,
                                       template_path[5:])  # 移除 'user/' 前缀
                if os.path.exists(full_path):
                    os.remove(full_path)
                
                # 从配置中删除
                category = current_item.parent().text(0)
                template_name = current_item.text(0)
                if category in self.main_window.user_templates:
                    if template_name in self.main_window.user_templates[category]:
                        del self.main_window.user_templates[category][template_name]
                        if not self.main_window.user_templates[category]:
                            del self.main_window.user_templates[category]
                
                # 保存配置
                self.main_window.save_user_template_config()
                
                # 重新加载模板
                self.main_window.load_templates()
                self.load_templates()
                
                QMessageBox.information(self, "成功", "模板已删除")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除模板失败: {str(e)}")
    
    def rename_template(self):
        """重命名模板"""
        current_item = self.tree.currentItem()
        if not current_item or not current_item.parent():
            QMessageBox.warning(self, "警告", "请选择要重命名的模板")
            return
        
        template_path = current_item.text(1)
        if not template_path.startswith('user/'):
            QMessageBox.warning(self, "警告", "只能重命名用户自定义模板")
            return
        
        new_name, ok = QLineEdit.getText(self, '重命名模板',
                                       '输入新名称:', text=current_item.text(0))
        
        if ok and new_name:
            try:
                category = current_item.parent().text(0)
                old_name = current_item.text(0)
                
                # 重命名文件
                old_path = os.path.join(self.main_window.user_template_dir,
                                      template_path[5:])
                new_path = os.path.join(os.path.dirname(old_path),
                                      f"{new_name}.yaml")
                
                if os.path.exists(new_path):
                    raise Exception("该名称已存在")
                
                os.rename(old_path, new_path)
                
                # 更新配置
                template_info = self.main_window.user_templates[category][old_name]
                del self.main_window.user_templates[category][old_name]
                self.main_window.user_templates[category][new_name] = {
                    'path': os.path.relpath(new_path, self.main_window.user_template_dir),
                    'description': template_info.get('description', '')
                }
                
                # 保存配置
                self.main_window.save_user_template_config()
                
                # 重新加载模板
                self.main_window.load_templates()
                self.load_templates()
                
                QMessageBox.information(self, "成功", "模板已重命名")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重命名模板失败: {str(e)}")

class SwitchableEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建工具栏
        toolbar = QHBoxLayout()
        self.view_combo = QComboBox()
        self.view_combo.addItems(["文本视图", "树形视图"])  # 改变默认顺序
        self.view_combo.currentTextChanged.connect(self.switch_view)
        toolbar.addWidget(QLabel("编辑器视图:"))
        toolbar.addWidget(self.view_combo)
        toolbar.addStretch()
        self.layout.addLayout(toolbar)
        
        # 创建堆叠部件来容纳两种编辑器
        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)
        
        # 创建两种编辑器
        self.text_editor = QPlainTextEdit()  # 文本编辑器放在前面
        self.tree_editor = YamlEditorWidget()
        
        # 添加到堆叠部件
        self.stack.addWidget(self.text_editor)  # 文本编辑器作为默认视图
        self.stack.addWidget(self.tree_editor)
        
        # 连接编辑器的修改信号
        self.tree_editor.tree.contentChanged.connect(self.on_tree_changed)
        self.text_editor.textChanged.connect(self.on_text_changed)
        
        # 用于防止循环更新
        self._updating = False
    
    def switch_view(self, view_name):
        """切换编辑器视图"""
        if view_name == "树形视图":
            if self.stack.currentWidget() != self.tree_editor:
                self.update_tree_from_text()
                self.stack.setCurrentWidget(self.tree_editor)
        else:
            if self.stack.currentWidget() != self.text_editor:
                self.update_text_from_tree()
                self.stack.setCurrentWidget(self.text_editor)
    
    def on_tree_changed(self):
        """树形编辑器内容改变时更新文本编辑器"""
        if not self._updating:
            self._updating = True
            self.update_text_from_tree()
            self._updating = False
    
    def on_text_changed(self):
        """文本编辑器内容改变时更新树形编辑器"""
        if not self._updating and self.stack.currentWidget() == self.text_editor:
            self._updating = True
            self.update_tree_from_text()
            self._updating = False
    
    def update_tree_from_text(self):
        """从文本更新树形视图"""
        try:
            text = self.text_editor.toPlainText()
            self.tree_editor.setPlainText(text)
        except Exception as e:
            print(f"更新树形视图失败: {str(e)}")
    
    def update_text_from_tree(self):
        """从树形视图更新文本"""
        try:
            text = self.tree_editor.toPlainText()
            self.text_editor.setPlainText(text)
        except Exception as e:
            print(f"更新文本视图失败: {str(e)}")
    
    def setPlainText(self, text):
        """设置编辑器内容"""
        self._updating = True
        self.text_editor.setPlainText(text)
        self.tree_editor.setPlainText(text)
        self._updating = False
    
    def toPlainText(self):
        """获取编辑器内容"""
        if self.stack.currentWidget() == self.tree_editor:
            return self.tree_editor.toPlainText()
        return self.text_editor.toPlainText()
    
    def document(self):
        """返回当前活动编辑器的文档"""
        if self.stack.currentWidget() == self.tree_editor:
            return self.tree_editor.document()
        return self.text_editor.document()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EasyYAML Editor")
        self.setGeometry(100, 100, 800, 600)
        
        # 初始化模板目录
        self.template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
        self.user_template_dir = os.path.join(
            os.path.expanduser('~'), 
            '.easyyaml', 
            'templates'
        )
        self.user_template_config = os.path.join(
            os.path.expanduser('~'), 
            '.easyyaml', 
            'template_config.json'
        )
        
        # 确保用户模板目录存在
        os.makedirs(self.user_template_dir, exist_ok=True)
        
        # 加载用户模板配置
        self.load_user_template_config()
        
        # 初始化中心部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # 创建搜索组合框
        self.search_box = SearchComboBox()
        self.layout.addWidget(self.search_box)
        
        # 创建标签页管理器
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)  # 启用关闭按钮
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)  # 连接关闭信号
        
        # 标签页右键菜单
        self.tab_widget.tabBar().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tab_widget.tabBar().customContextMenuRequested.connect(self.show_tab_context_menu)
        
        self.layout.addWidget(self.tab_widget)
        
        # 创建菜单栏和工具栏
        self.create_menu_bar()
        self.create_toolbar()
        
        # 设置快捷键
        self.setup_shortcuts()
        
        # 使用定时器延迟加载模板
        self.template_list = []
        QTimer.singleShot(0, self.load_templates)
        
        # 初始化搜索框
        self.search_box.search_timer.timeout.connect(self.filter_templates)
    
    def setup_shortcuts(self):
        # Ctrl+S 保存
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save_file)
        
        # Ctrl+O 打开
        open_shortcut = QShortcut(QKeySequence("Ctrl+O"), self)
        open_shortcut.activated.connect(self.open_file)
        
        # Ctrl+N 新建
        new_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        new_shortcut.activated.connect(self.new_file)
    
    def get_all_templates(self):
        """获取所有模板，包括内置和用户自定义的"""
        templates = []
        try:
            # 获取内置模板
            if os.path.exists(self.template_dir):
                for root, dirs, files in os.walk(self.template_dir):
                    for file in files:
                        if file.endswith(('.yaml', '.yml')):
                            rel_path = os.path.relpath(
                                os.path.join(root, file), 
                                self.template_dir
                            )
                            templates.append(rel_path)
            else:
                print(f"内置模板目录不存在: {self.template_dir}")  # 调试信息
            
            # 获取用户模板
            if os.path.exists(self.user_template_dir):
                for root, dirs, files in os.walk(self.user_template_dir):
                    for file in files:
                        if file.endswith(('.yaml', '.yml')):
                            rel_path = os.path.relpath(
                                os.path.join(root, file), 
                                self.user_template_dir
                            )
                            templates.append(f"user/{rel_path}")
            else:
                print(f"用户模板目录不存在: {self.user_template_dir}")  # 调试信息
                
            print(f"找到的所有模板: {templates}")  # 调试信息
            return templates
            
        except Exception as e:
            print(f"获取模板列表失败: {str(e)}")  # 调试信息
            return []
    
    def setup_template_completer(self):
        """设置模板搜索自动补全"""
        completer = QCompleter(self.template_list)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.search_bar.setCompleter(completer)
    
    def filter_templates(self):
        """根据搜索文本过滤模板"""
        try:
            text = self.search_box.currentText().lower()
            self.search_box.blockSignals(True)
            self.search_box.clear()
            
            if not text:
                # 如果没有搜索文本，显示所有模板但不显示下拉列表
                self.setup_search_box()
                self.search_box.blockSignals(False)
                return
            
            # 过滤匹配的模板
            filtered = []
            for template in self.template_list:
                display_name = template.replace('\\', ' > ').replace('.yaml', '').title()
                if (text in display_name.lower() or 
                    text in template.lower()):
                    filtered.append((display_name, template))
            
            # 排序结果
            filtered.sort(key=lambda x: x[0])
            
            # 添加过滤后的结果
            for display_name, template_path in filtered:
                self.search_box.addItem(display_name, template_path)
            
            self.search_box.blockSignals(False)
                
        except Exception as e:
            print(f"过滤模板失败: {str(e)}")
            self.search_box.blockSignals(False)
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        
        new_action = QAction('新建', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction('打开', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction('保存', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_current_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction('另存为...', self)
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        close_action = QAction('关闭', self)
        close_action.setShortcut('Ctrl+W')
        close_action.triggered.connect(lambda: self.close_tab(self.tab_widget.currentIndex()))
        file_menu.addAction(close_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu('编辑')
        
        # 视图菜单
        view_menu = menubar.addMenu('视图')
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助')
    
    def create_toolbar(self):
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        new_action = toolbar.addAction("新建")
        new_action.triggered.connect(self.new_file)
        open_action = toolbar.addAction("打开")
        open_action.triggered.connect(self.open_file)
        save_action = toolbar.addAction("保存")
        save_action.triggered.connect(self.save_file)
    
    def new_file(self):
        editor = YamlEditorWidget()
        self.tab_widget.addTab(editor, "未命名")
        self.tab_widget.setCurrentWidget(editor)
    
    def open_file(self):
        """打开文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开文件", "", "YAML files (*.yaml *.yml)")
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 使用可切换的编辑器
                editor = SwitchableEditor()
                editor.setPlainText(content)
                
                file_name = os.path.basename(file_path)
                index = self.tab_widget.addTab(editor, file_name)
                self.tab_widget.setCurrentIndex(index)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法打开文件: {str(e)}")
    
    def save_file(self):
        """保存当前文件"""
        current_editor = self.tab_widget.currentWidget()
        if not current_editor:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存文件", "", "YAML files (*.yaml *.yml)")
        
        if file_path:
            try:
                # 获取 YAML 内容
                content = current_editor.toPlainText()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # 更新标签页标题
                file_name = os.path.basename(file_path)
                self.tab_widget.setTabText(
                    self.tab_widget.currentIndex(), 
                    file_name
                )
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法保存文件: {str(e)}")
    
    def close_tab(self, index):
        self.tab_widget.removeTab(index)
    
    def create_from_template(self, template_name):
        """从模板创建新文件"""
        try:
            if template_name.startswith('user/'):
                template_path = os.path.join(
                    self.user_template_dir,
                    template_name[5:]
                )
            else:
                template_path = os.path.join(self.template_dir, template_name)
            
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 使用可切换的编辑器
            editor = SwitchableEditor()
            editor.setPlainText(content)
            
            display_name = os.path.basename(template_name).replace('.yaml', '').title()
            index = self.tab_widget.addTab(editor, f"新建 {display_name}")
            self.tab_widget.setCurrentIndex(index)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法加载模板: {str(e)}")
    
    def load_user_template_config(self):
        """加载用户模板配置"""
        try:
            if os.path.exists(self.user_template_config):
                with open(self.user_template_config, 'r', encoding='utf-8') as f:
                    self.user_templates = json.load(f)
            else:
                self.user_templates = {}
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载用户模板配置失败: {str(e)}")
            self.user_templates = {}
    
    def save_user_template_config(self):
        """保存用户模板配置"""
        try:
            with open(self.user_template_config, 'w', encoding='utf-8') as f:
                json.dump(self.user_templates, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"保存用户模板配置失败: {str(e)}")
    
    def add_template(self):
        """添加自定义模板"""
        dialog = AddTemplateDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                name = dialog.name_edit.text().strip()
                category = dialog.category_edit.text().strip()
                file_path = dialog.file_path
                
                if not all([name, category, file_path]):
                    QMessageBox.warning(self, "警告", "请填写所有必要信息")
                    return
                
                # 创建分类目录
                category_dir = os.path.join(self.user_template_dir, category)
                os.makedirs(category_dir, exist_ok=True)
                
                # 复制模板文件
                dest_path = os.path.join(category_dir, f"{name}.yaml")
                shutil.copy2(file_path, dest_path)
                
                # 更新配置
                if category not in self.user_templates:
                    self.user_templates[category] = {}
                self.user_templates[category][name] = {
                    'path': os.path.relpath(dest_path, self.user_template_dir),
                    'description': ''
                }
                
                # 保存配置
                self.save_user_template_config()
                
                # 重新加载模板列表
                self.load_templates()
                
                QMessageBox.information(self, "成功", "模板添加成功！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加模板失败: {str(e)}")
    
    def manage_templates(self):
        """打开模板管理对话框"""
        dialog = ManageTemplatesDialog(self)
        dialog.exec()
    
    def load_templates(self):
        """异步加载所有模板"""
        try:
            print("开始加载模板...")  # 调试信息
            self.template_list = self.get_all_templates()
            print(f"找到模板: {self.template_list}")  # 调试信息
            self.setup_search_box()
        except Exception as e:
            print(f"加载模板错误: {str(e)}")  # 调试信息
            QMessageBox.warning(self, "警告", f"加载模板失败: {str(e)}")
            self.template_list = []
    
    def setup_search_box(self):
        """设置搜索框的内容"""
        try:
            print("开始设置搜索框...")
            templates_with_names = []
            for template in self.template_list:
                display_name = template.replace('\\', ' > ').replace('.yaml', '').title()
                templates_with_names.append((display_name, template))
            
            print(f"处理后的模板: {templates_with_names}")
            
            templates_with_names.sort(key=lambda x: x[0])
            
            try:
                self.search_box.activated.disconnect()
            except:
                pass
            
            self.search_box.blockSignals(True)
            self.search_box.clear()
            for display_name, template_path in templates_with_names:
                try:
                    self.search_box.addItem(display_name, template_path)
                except Exception as e:
                    print(f"添加项目失败: {display_name}, 错误: {str(e)}")
            
            self.search_box.setCurrentText("")
            self.search_box.blockSignals(False)
            
            # 重新连接信号
            self.search_box.activated.connect(self.on_template_selected)
                
        except Exception as e:
            print(f"设置搜索框失败: {str(e)}")
            QMessageBox.warning(self, "警告", f"设置搜索框失败: {str(e)}")
    
    def on_template_selected(self, index):
        """当用户从下拉列表中选择模板时"""
        try:
            template_path = self.search_box.itemData(index)
            if template_path:
                # 只有当用户实际选择了一个项目时才创建新文件
                if self.search_box.currentIndex() >= 0:
                    self.create_from_template(template_path)
                    # 清空搜索框并重新显示所有模板
                    self.search_box.setCurrentText("")
                    self.setup_search_box()
        except Exception as e:
            print(f"选择模板失败: {str(e)}")
            QMessageBox.warning(self, "警告", f"选择模板失败: {str(e)}")
    
    def show_tab_context_menu(self, position):
        """显示标签页右键菜单"""
        tab_bar = self.tab_widget.tabBar()
        tab_index = tab_bar.tabAt(tab_bar.mapFrom(self.tab_widget, position))
        
        if tab_index != -1:
            menu = QMenu(self)
            
            # 添加菜单项
            close_action = menu.addAction("关闭")
            close_others_action = menu.addAction("关闭其他")
            close_all_action = menu.addAction("关闭所有")
            menu.addSeparator()
            save_action = menu.addAction("保存")
            save_as_action = menu.addAction("另存为...")
            
            # 显示菜单并获取选择的动作
            action = menu.exec(self.tab_widget.tabBar().mapToGlobal(position))
            
            if action == close_action:
                self.close_tab(tab_index)
            elif action == close_others_action:
                self.close_other_tabs(tab_index)
            elif action == close_all_action:
                self.close_all_tabs()
            elif action == save_action:
                self.save_current_file()
            elif action == save_as_action:
                self.save_file_as()
    
    def close_tab(self, index):
        """关闭指定的标签页"""
        editor = self.tab_widget.widget(index)
        if editor and editor.document().isModified():
            reply = QMessageBox.question(self, '保存确认',
                "文件已修改，是否保存？",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel)
            
            if reply == QMessageBox.StandardButton.Save:
                self.save_current_file()
            elif reply == QMessageBox.StandardButton.Cancel:
                return
        
        self.tab_widget.removeTab(index)
    
    def close_other_tabs(self, keep_index):
        """关闭除指定标签页外的所有标签页"""
        for i in range(self.tab_widget.count() - 1, -1, -1):
            if i != keep_index:
                self.close_tab(i)
    
    def close_all_tabs(self):
        """关闭所有标签页"""
        for i in range(self.tab_widget.count() - 1, -1, -1):
            self.close_tab(i)
    
    def save_current_file(self):
        """保存当前文件"""
        current_editor = self.tab_widget.currentWidget()
        if not current_editor:
            return
            
        # 如果是新文件，调用另存为
        if self.tab_widget.tabText(self.tab_widget.currentIndex()).startswith("新建"):
            self.save_file_as()
        else:
            # TODO: 保存到原文件
            self.save_file_as()  # 临时使用另存为
    
    def save_file_as(self):
        """文件另存为"""
        current_editor = self.tab_widget.currentWidget()
        if not current_editor:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存文件", "", "YAML files (*.yaml *.yml)")
        
        if file_path:
            try:
                content = current_editor.toPlainText()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # 更新标签页标题
                file_name = os.path.basename(file_path)
                self.tab_widget.setTabText(
                    self.tab_widget.currentIndex(), 
                    file_name
                )
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法保存文件: {str(e)}")