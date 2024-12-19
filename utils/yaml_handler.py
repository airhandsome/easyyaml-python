import yaml
import os

class YamlHandler:
    @staticmethod
    def load_yaml(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise Exception(f"加载YAML文件失败: {str(e)}")
    
    @staticmethod
    def save_yaml(data, file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True)
        except Exception as e:
            raise Exception(f"保存YAML文件失败: {str(e)}")
    
    @staticmethod
    def load_template(template_name):
        template_path = os.path.join('templates', template_name)
        return YamlHandler.load_yaml(template_path) 