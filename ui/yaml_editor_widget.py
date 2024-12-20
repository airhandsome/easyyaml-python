from PyQt6.QtWidgets import (QWidget, QTreeWidget, QTreeWidgetItem, 
                           QVBoxLayout, QHBoxLayout, QPushButton, 
                           QMenu, QInputDialog, QMessageBox, QComboBox,
                           QLineEdit, QLabel, QDialog, QDialogButtonBox,
                           QPlainTextEdit, QStackedWidget)
from PyQt6.QtCore import Qt, pyqtSignal
import yaml
import copy

class AddNodeDialog(QDialog):
    def __init__(self, parent=None, is_list_item=False):
        super().__init__(parent)
        self.setWindowTitle("添加节点")
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # 键名输入（如果不是列表项）
        if not is_list_item:
            key_layout = QHBoxLayout()
            key_layout.addWidget(QLabel("键名:"))
            self.key_edit = QLineEdit()
            key_layout.addWidget(self.key_edit)
            layout.addLayout(key_layout)
        
        # 类型选择
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("类型:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "字符串(string)", 
            "整数(int)", 
            "浮点数(float)", 
            "布尔值(bool)", 
            "列表(list)", 
            "字典(dict)",
            "空值(null)"
        ])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)
        
        # 值输入
        self.value_layout = QHBoxLayout()
        self.value_layout.addWidget(QLabel("值:"))
        self.value_edit = QLineEdit()
        self.value_layout.addWidget(self.value_edit)
        layout.addLayout(self.value_layout)
        
        # 布尔值选择
        self.bool_combo = QComboBox()
        self.bool_combo.addItems(["True", "False"])
        self.bool_combo.hide()
        self.value_layout.addWidget(self.bool_combo)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def on_type_changed(self, type_text):
        """当类型改变时更新值输入控件"""
        if "布尔值" in type_text:
            self.value_edit.hide()
            self.bool_combo.show()
        elif "列表" in type_text or "字典" in type_text:
            self.value_edit.hide()
            self.bool_combo.hide()
        else:
            self.value_edit.show()
            self.bool_combo.hide()
            if "整数" in type_text:
                self.value_edit.setPlaceholderText("请输入整数")
            elif "浮点数" in type_text:
                self.value_edit.setPlaceholderText("请输入数字")
            elif "空值" in type_text:
                self.value_edit.setEnabled(False)
            else:
                self.value_edit.setPlaceholderText("")
                self.value_edit.setEnabled(True)
    
    def get_data(self):
        """获取输入的数据"""
        # 获取键（如果有）
        key = self.key_edit.text() if hasattr(self, 'key_edit') else None
        
        # 获取类型和值
        type_text = self.type_combo.currentText()
        
        # 根据类型处理值
        if "布尔值" in type_text:
            value = self.bool_combo.currentText() == "True"
        elif "列表" in type_text:
            value = []
        elif "字典" in type_text:
            value = {}
        elif "空值" in type_text:
            value = None
        else:
            value = self.value_edit.text()
            # 类型转换
            try:
                if "整数" in type_text:
                    value = int(value)
                elif "浮点数" in type_text:
                    value = float(value)
            except ValueError:
                QMessageBox.warning(self, "警告", "输入的值格式不正确")
                return None, None
        
        return key, value

class YamlTreeWidget(QTreeWidget):
    contentChanged = pyqtSignal()  # 内容变化信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(["键", "值", "类型"])
        self.setColumnWidth(0, 200)
        self.setColumnWidth(1, 300)
        
        # 启用编辑
        self.setEditTriggers(QTreeWidget.EditTrigger.DoubleClicked | 
                           QTreeWidget.EditTrigger.EditKeyPressed)
        
        # 右键菜单
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # 连接编辑完成信号
        self.itemChanged.connect(self.on_item_edited)
        
        # 添加工具栏
        self.toolbar = QHBoxLayout()
        self.add_root_btn = QPushButton("添加根节点")
        self.add_root_btn.clicked.connect(self.add_root_item)
        self.toolbar.addWidget(self.add_root_btn)
        
        # 展开所有项
        self.expandAll()
        
        # 防止循环更新
        self._updating = False
    
    def on_item_edited(self, item, column):
        """处理项目编辑完成事件"""
        if self._updating:
            return
            
        self._updating = True
        try:
            if column == 0:  # 编辑键
                # 对于列表项，不允许编辑键（索引）
                parent = item.parent()
                if parent and isinstance(parent.data(0, Qt.ItemDataRole.UserRole), list):
                    # 恢复原始索引值，不显示警告
                    item.setText(0, str(self._get_list_index(item)))
                    return
            
            elif column == 1:  # 编辑值
                value = item.data(0, Qt.ItemDataRole.UserRole)
                new_text = item.text(1)
                
                # 根据原始类型转换新值
                try:
                    if isinstance(value, bool):
                        new_value = new_text.lower() in ['true', '1', 'yes', 'y']
                    elif isinstance(value, int):
                        new_value = int(new_text)
                    elif isinstance(value, float):
                        new_value = float(new_text)
                    else:
                        new_value = new_text
                    
                    item.setData(0, Qt.ItemDataRole.UserRole, new_value)
                    item.setText(1, str(new_value))
                    item.setText(2, type(new_value).__name__)
                except ValueError:
                    item.setText(1, str(value))
                    QMessageBox.warning(self, "警告", "输入的值格式不正确")
            
            self.contentChanged.emit()
            
        finally:
            self._updating = False
    
    def _get_list_index(self, item):
        """获取列表项的实际索引"""
        parent = item.parent()
        if parent:
            return parent.indexOfChild(item)
        return 0
    
    def keyPressEvent(self, event):
        """处理键盘事件"""
        if event.key() == Qt.Key.Key_Delete:
            current = self.currentItem()
            if current:
                self.delete_item(current)
        elif event.key() == Qt.Key.Key_Insert:
            current = self.currentItem()
            if current:
                self.add_child_item(current)
            else:
                self.add_root_item()
        else:
            super().keyPressEvent(event)
    
    def _add_item(self, parent, key, value):
        """递归添加节点"""
        item = QTreeWidgetItem(parent)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)  # 使项目可编辑
        item.setText(0, str(key))
        item.setText(1, str(value))
        item.setText(2, type(value).__name__)
        item.setData(0, Qt.ItemDataRole.UserRole, value)
        
        if isinstance(value, dict):
            for k, v in value.items():
                self._add_item(item, k, v)
        elif isinstance(value, list):
            for i, v in enumerate(value):
                self._add_item(item, str(i), v)
    
    def add_root_item(self):
        """添加根节点"""
        dialog = AddNodeDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            key, value = dialog.get_data()
            if key is not None:  # 确保输入有效
                item = QTreeWidgetItem(self)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                item.setText(0, str(key))
                item.setText(1, str(value))
                item.setText(2, type(value).__name__)
                item.setData(0, Qt.ItemDataRole.UserRole, value)
                self.contentChanged.emit()
    
    def add_child_item(self, parent_item):
        """添加子节点"""
        parent_value = parent_item.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(parent_value, (dict, list)):
            QMessageBox.warning(self, "警告", "只能向字典或列表添加子项")
            return
        
        # 如果是列表，则不需要输入键名
        is_list_item = isinstance(parent_value, list)
        dialog = AddNodeDialog(self, is_list_item=is_list_item)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            key, value = dialog.get_data()
            if value is not None:  # 确保输入有效
                item = QTreeWidgetItem(parent_item)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                
                # 如果是列表项，使用当前索引作为键
                if is_list_item:
                    key = str(self._get_list_index(item))
                
                item.setText(0, str(key))
                item.setText(1, str(value))
                item.setText(2, type(value).__name__)
                item.setData(0, Qt.ItemDataRole.UserRole, value)
                parent_item.setExpanded(True)
                self.contentChanged.emit()
    
    def _update_list_indices(self, parent_item):
        """更新列表项的索引"""
        if isinstance(parent_item.data(0, Qt.ItemDataRole.UserRole), list):
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                child.setText(0, str(i))
    
    def show_context_menu(self, position):
        """显示右键菜单"""
        item = self.itemAt(position)
        menu = QMenu()
        
        if item:
            add_action = menu.addAction("添加子项")
            edit_action = menu.addAction("编辑")
            delete_action = menu.addAction("删除")
            
            action = menu.exec(self.mapToGlobal(position))
            
            if action == add_action:
                self.add_child_item(item)
            elif action == edit_action:
                self.edit_item(item)
            elif action == delete_action:
                self.delete_item(item)
        else:
            add_action = menu.addAction("添加根节点")
            action = menu.exec(self.mapToGlobal(position))
            if action == add_action:
                self.add_root_item()
    
    def edit_item(self, item):
        """编辑节点"""
        if not item:
            return
            
        value = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(value, (dict, list)):
            QMessageBox.warning(self, "警告", "不能直接编辑字典或列表的值")
            return
            
        new_value, ok = QInputDialog.getText(
            self, "编辑值", "输入新值:",
            text=str(value)
        )
        
        if ok:
            try:
                # 尝试保持原来的类型
                if isinstance(value, bool):
                    new_value = new_value.lower() in ['true', '1', 'yes', 'y']
                elif isinstance(value, int):
                    new_value = int(new_value)
                elif isinstance(value, float):
                    new_value = float(new_value)
                
                item.setText(1, str(new_value))
                item.setData(0, Qt.ItemDataRole.UserRole, new_value)
                self.contentChanged.emit()
            except ValueError:
                QMessageBox.warning(self, "警告", "输入的值格式不正确")
    
    def delete_item(self, item):
        """删除节点"""
        if not item:
            return
            
        reply = QMessageBox.question(
            self, '确认删除',
            "确定要删除这个节点吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            parent = item.parent()
            if parent:
                parent.removeChild(item)
                # 如果是列表，更新其他项的索引
                if isinstance(parent.data(0, Qt.ItemDataRole.UserRole), list):
                    self._update_list_indices(parent)
            else:
                self.invisibleRootItem().removeChild(item)
            self.contentChanged.emit()
    
    def dropEvent(self, event):
        """处理拖放事件"""
        super().dropEvent(event)
        # 更新所有列表的索引
        root = self.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            if isinstance(item.data(0, Qt.ItemDataRole.UserRole), list):
                self._update_list_indices(item)
        self.contentChanged.emit()
    
    def to_yaml_data(self):
        """将树形结构转换为YAML数据"""
        data = {}
        root = self.invisibleRootItem()
        
        for i in range(root.childCount()):
            item = root.child(i)
            key = item.text(0)
            value = self._get_item_data(item)
            data[key] = value
        
        return data
    
    def _get_item_data(self, item):
        """递归获取节点数据"""
        value = item.data(0, Qt.ItemDataRole.UserRole)
        
        if isinstance(value, dict):
            result = {}
            for i in range(item.childCount()):
                child = item.child(i)
                result[child.text(0)] = self._get_item_data(child)
            return result
        elif isinstance(value, list):
            result = []
            for i in range(item.childCount()):
                child = item.child(i)
                result.append(self._get_item_data(child))
            return result
        else:
            return value
    
    def from_yaml_data(self, data):
        """从YAML数据加载树形结构"""
        self.clear()
        if isinstance(data, dict):
            for key, value in data.items():
                self._add_item(self.invisibleRootItem(), key, value)
        self.expandAll()

class YamlEditorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        # 创建树形编辑器
        self.tree = YamlTreeWidget(self)
        layout.addLayout(self.tree.toolbar)
        layout.addWidget(self.tree)
        
        # 连接信号
        self.tree.contentChanged.connect(self.on_content_changed)
        
        # 用于跟踪修改状态
        self._modified = False
        self._can_convert_tree = True
    def setPlainText(self, text):
        """从文本加载YAML"""
        try:
            data = yaml.safe_load(text) or {}
            self.tree.from_yaml_data(data)
            self._modified = False
        except Exception as e:
            self._can_convert_tree = False
            print("警告", f"加载YAML失败: {str(e)}")

    def canConvertTree(self):
        return self._can_convert_tree

    def toPlainText(self):
        """将树形结构转换为YAML文本"""
        try:
            data = self.tree.to_yaml_data()
            return yaml.dump(data, allow_unicode=True, sort_keys=False)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"生成YAML失败: {str(e)}")
            return ""
    
    def on_content_changed(self):
        """内容变化时的处理"""
        self._modified = True
    
    def document(self):
        """模拟 QTextEdit 的 document() 方法"""
        class Document:
            def __init__(self, modified):
                self._modified = modified
            def isModified(self):
                return self._modified
        return Document(self._modified) 

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

    def is_tree_view(self):
        """检查当前是否为树形视图"""
        return self.stack.currentWidget() == self.tree_editor

    def load_yaml_file(self, file_path):
        """加载 YAML 文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if self.is_tree_view():  # 仅在树形视图下加载
                    self.tree_editor.load_yaml(content)
                else:
                    # 在文本视图下直接显示内容
                    self.text_editor.setPlainText(content)
        except Exception as e:
            if self.is_tree_view():  # 仅在树形视图下显示错误
                QMessageBox.critical(self, "加载失败", f"该文件不支持使用树形视图: {str(e)}")
                self.view_combo.setCurrentText("文本视图")  # 切换回文本视图
                self.text_editor.setPlainText(content)  # 显示内容
            else:
                # 在文本视图下不显示错误
                pass

    def switch_view(self):
        """切换视图"""
        if self.is_tree_view():
            # 检查当前文本是否有效
            if not self.text_editor.toPlainText().strip():
                QMessageBox.warning(self, "警告", "当前文本无效，无法切换到树形视图")
                self.view_combo.setCurrentText("文本视图")  # 切换回文本视图
                return
        # 其他切换逻辑...