class ModelSelector:
    def __init__(self, config_file="model_config.json"):
        self.config_file = config_file
        self.default_model = "llama3"
    
    def get_selected_model(self):
        """Returns the currently selected model"""
        try:
            import json
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                return config.get('selected_model', self.default_model)
        except (FileNotFoundError, json.JSONDecodeError):
            return self.default_model
    
    def set_selected_model(self, model_name):
        """Sets the selected model"""
        import json
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            config = {}
        
        config['selected_model'] = model_name
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)