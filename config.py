import os

APP_NAME = "SQLRunner"
c_dir = "C:/" 

def get_config_path():
    config_dir= os.path.join(c_dir,APP_NAME)
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "profiles.json")

