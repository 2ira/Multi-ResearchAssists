import os
import yaml
from typing import Dict, Any, Optional
class ConfigLoader:

    # def __init__(self, config_path: Optional[str] = None):
    #     # 动态计算配置路径的逻辑保持不变...
    #     if config_path is None:
    #         current_dir = os.path.dirname(os.path.abspath(__file__))
    #         self.config_path = os.path.abspath(os.path.join(current_dir, '..', '..', 'config'))
    #     else:
    #         self.config_path = config_path
    #
    #     print(f"Config path: {self.config_path}")
    #     self.api_keys = self._load_api_keys()
    #     self.config = self._load_main_config()

    ####### Problem1: solve relative path
    def __init__(self, config_path: str = "/Users/bytedance/Multiagent/pythonProject/RA/multiagents/config"):
        self.config_path = config_path
        self.api_keys = self._load_api_keys()
        self.config = self._load_main_config()

    def _load_api_keys(self) -> Dict[str, Any]:
        api_keys_path = os.path.join(self.config_path, "api_key.yaml")
        print(f"Loading API keys from: {api_keys_path}")

        if not os.path.exists(api_keys_path):
            print(f"API keys file not found: {api_keys_path}")
            return {}

        try:
            with open(api_keys_path, "r") as f:
                keys = yaml.safe_load(f) or {}
                print(f"API keys loaded: {list(keys.keys())}")
                return keys
        except Exception as e:
            print(f"Error loading API keys: {e}")
            return {}

    def _load_main_config(self) -> Dict[str, Any]:
        config_path = os.path.join(self.config_path, "config.yaml")
        print(f"Loading main config from: {config_path}")

        if not os.path.exists(config_path):
           # print(f"Config file not found: {config_path}")
            return {}

        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f) or {}
               # print(f"Config loaded: {list(config.keys())}")
                return config
        except Exception as e:
            print(f"Error loading main config: {e}")
            return {}


    # current we have default model and other models like model_1,model_2,model_3...
    def get_model_config(self, model_name: str = "default_model") -> Dict[str, Any]:
        """get target model config"""
        # print(model_name)
        model_config = self.config.get(model_name, {})
        # print("model config is",model_config)
        # from model type to get specific api_key
        service_type = model_config.get("type") # name match like openai
        if service_type and service_type in self.api_keys:
            model_config.update(self.api_keys[service_type])

        return model_config

    def get_tool_config(self, tool_name: str) -> Optional[Dict[str, Any]]:
        for tool in self.config.get("tools", []):
            if tool["name"] == tool_name:
                return tool
        return None

    # workflow contains the retry times and some special parameters
    def get_workflow_config(self, workflow_name: str = "survey") -> Dict[str, Any]:
        return self.config.get("workflow", {}).get(workflow_name, {})

    # user proxy get the interaction type
    def get_user_proxy_config(self) -> Dict[str, Any]:
        return self.config.get("user_proxy", {})


# 全局配置实例
config_loader = ConfigLoader()