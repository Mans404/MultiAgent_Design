import os
class TemplateParser:
    def __init__(self, language: str = None, default_language: str = "en"):
        self.current_path = os.path.dirname(os.path.abspath(__file__))
        self.default_language = default_language
        self.language = None
        self.set_language(language or default_language)

    def set_language(self, language: str):
        language_dir_path = os.path.join(self.current_path, "locales", language)
        if language and os.path.isdir(language_dir_path):  # isdir, not isfile
            self.language = language
    def get(self, group: str, key: str, vars: dict = None):
        if not group or not key:
            return None
        group_path = os.path.join(self.current_path, "locales", self.language, f"{group}.py")
        targeted_language = self.language
        if not os.path.exists(group_path):
            group_path = os.path.join(self.current_path, "locales", self.default_language, f"{group}.py")
            targeted_language = self.default_language

        if not os.path.exists(group_path):
            return None
        
        #import group_module
        module  = __import__(f"stores.LLM.templates.locales.{targeted_language}.{group}", fromlist=[group])

        if not module:
            return None
        
        key_attribute = getattr(module, key, None) # محتاج مراجعة
        if key_attribute is None:
            return None
        return key_attribute.substitute(vars) if vars is not None else key_attribute