from PyQt6.QtWidgets import (QMainWindow, QToolBar, QMenuBar,
                             QFileDialog, QMessageBox, QVBoxLayout,
                             QWidget, QTabWidget, QLineEdit, QCompleter, QComboBox, QTabBar, QMenu)
from PyQt6.QtCore import Qt, QStringListModel, QTimer, QPoint
from PyQt6.QtGui import QKeySequence, QShortcut, QDragEnterEvent, QDropEvent, QAction
from .editor_widget import YamlEditorWidget
import os
from utils.yaml_handler import YamlHandler


class DraggableTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDocumentMode(True)
        self.setTabsClosable(True)
        self.setMovable(True)  # 启用标签拖动

        # 自定义标签栏
        self.tab_bar = DraggableTabBar(self)
        self.setTabBar(self.tab_bar)

        # 右键菜单
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_tab_context_menu)

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


class DraggableTabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setElideMode(Qt.TextElideMode.ElideRight)
        self.setExpanding(False)  # 标签页不要自动扩展
        self.setMovable(True)

        # 添加快捷键
        self.setup_shortcuts()

    def setup_shortcuts(self):
        """设置标签页快捷键"""
        # Ctrl+Tab 切换到下一个标签页
        next_tab = QShortcut(QKeySequence("Ctrl+Tab"), self)
        next_tab.activated.connect(self.next_tab)

        # Ctrl+Shift+Tab 切换到上一个标签页
        prev_tab = QShortcut(QKeySequence("Ctrl+Shift+Tab"), self)
        prev_tab.activated.connect(self.prev_tab)

        # Alt+Left 向左移动标签页
        move_left = QShortcut(QKeySequence("Alt+Left"), self)
        move_left.activated.connect(self.move_current_tab_left)

        # Alt+Right 向右移动标签页
        move_right = QShortcut(QKeySequence("Alt+Right"), self)
        move_right.activated.connect(self.move_current_tab_right)

    def next_tab(self):
        """切换到下一个标签页"""
        if self.count() > 1:
            current = self.parent().currentIndex()
            next_index = (current + 1) % self.count()
            self.parent().setCurrentIndex(next_index)

    def prev_tab(self):
        """切换到上一个标签页"""
        if self.count() > 1:
            current = self.parent().currentIndex()
            prev_index = (current - 1) % self.count()
            self.parent().setCurrentIndex(prev_index)

    def move_current_tab_left(self):
        """将当前标签页向左移动"""
        current = self.parent().currentIndex()
        self.parent().move_tab_left(current)

    def move_current_tab_right(self):
        """将当前标签页向右移动"""
        current = self.parent().currentIndex()
        self.parent().move_tab_right(current)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EasyYAML Editor")
        self.setGeometry(100, 100, 800, 600)

        # 创建中心部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # 创建搜索栏
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("搜索模板...")
        self.search_bar.textChanged.connect(self.filter_templates)
        self.layout.addWidget(self.search_bar)

        # 创建标签页管理器
        self.tab_widget = DraggableTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.layout.addWidget(self.tab_widget)

        # 创建菜单栏和工具栏
        self.create_menu_bar()
        self.create_toolbar()

        # 设置快捷键
        self.setup_shortcuts()

        # 模板路径和模板列表
        self.template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
        self.template_list = self.get_all_templates()

        # 设置模板补全
        self.setup_template_completer()

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
        """获取所有模板文件路径"""
        templates = []
        for root, dirs, files in os.walk(self.template_dir):
            for file in files:
                if file.endswith(('.yaml', '.yml')):
                    rel_path = os.path.relpath(
                        os.path.join(root, file), self.template_dir)
                    templates.append(rel_path)
        return templates

    def setup_template_completer(self):
        """设置模板搜索自动补全"""
        completer = QCompleter(self.template_list)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.search_bar.setCompleter(completer)

    def filter_templates(self, text):
        """根据搜索文本过滤模板"""
        if not text:
            return

        filtered = [t for t in self.template_list
                    if text.lower() in t.lower()]

        if len(filtered) == 1:
            # 如果只有一个匹配结果，直接打开该模板
            self.create_from_template(filtered[0])
        else:
            # 更新自动补全列表
            model = QStringListModel()
            model.setStringList(filtered)
            self.search_bar.completer().setModel(model)

    def create_menu_bar(self):
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")
        new_action = file_menu.addAction("新建 (Ctrl+N)")
        new_action.triggered.connect(self.new_file)
        open_action = file_menu.addAction("打开 (Ctrl+O)")
        open_action.triggered.connect(self.open_file)
        save_action = file_menu.addAction("保存 (Ctrl+S)")
        save_action.triggered.connect(self.save_file)

        # 模板菜单
        template_menu = menubar.addMenu("模板")

        # K8s模板
        k8s_menu = template_menu.addMenu("Kubernetes")
        k8s_templates = {
            "Deployment": "k8s/deployment.yaml",
            "Service": "k8s/service.yaml",
            "Ingress": "k8s/ingress.yaml",
            "ConfigMap": "k8s/configmap.yaml",
            "Secret": "k8s/secret.yaml"
        }

        for name, path in k8s_templates.items():
            action = k8s_menu.addAction(name)
            action.triggered.connect(
                lambda checked, p=path: self.create_from_template(p))

        # Docker模板
        docker_menu = template_menu.addMenu("Docker")
        docker_templates = {
            "Docker Compose": "docker/docker-compose.yaml",
            "Dockerfile": "docker/dockerfile.yaml"
        }

        for name, path in docker_templates.items():
            action = docker_menu.addAction(name)
            action.triggered.connect(
                lambda checked, p=path: self.create_from_template(p))

        # 服务器配置模板
        server_menu = template_menu.addMenu("服务器配置")
        server_templates = {
            "Nginx": "server/nginx.yaml",
            "MySQL": "server/mysql.yaml",
            "Redis": "server/redis.yaml"
        }

        for name, path in server_templates.items():
            action = server_menu.addAction(name)
            action.triggered.connect(
                lambda checked, p=path: self.create_from_template(p))

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
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开YAML文件", "", "YAML files (*.yaml *.yml)")

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                editor = YamlEditorWidget()
                editor.setPlainText(content)
                editor.file_path = file_path

                file_name = os.path.basename(file_path)
                self.tab_widget.addTab(editor, file_name)
                self.tab_widget.setCurrentWidget(editor)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法打开文件: {str(e)}")

    def save_file(self):
        current_editor = self.tab_widget.currentWidget()
        if not current_editor:
            return

        if hasattr(current_editor, 'file_path'):
            file_path = current_editor.file_path
        else:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存YAML文件", "", "YAML files (*.yaml *.yml)")

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(current_editor.toPlainText())

                current_editor.file_path = file_path
                file_name = os.path.basename(file_path)
                self.tab_widget.setTabText(
                    self.tab_widget.currentIndex(), file_name)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法保存文件: {str(e)}")

    def close_tab(self, index):
        self.tab_widget.removeTab(index)

    def create_from_template(self, template_name):
        try:
            template_path = os.path.join(self.template_dir, template_name)
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()

            editor = YamlEditorWidget()
            editor.setPlainText(content)

            self.tab_widget.addTab(editor, f"新建 {os.path.basename(template_name)}")
            self.tab_widget.setCurrentWidget(editor)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法加载模板: {str(e)}")