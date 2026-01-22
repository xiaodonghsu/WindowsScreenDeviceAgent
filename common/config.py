import yaml

config_file = 'config.yaml'

def load_config() -> dict[str, any]:
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    return config