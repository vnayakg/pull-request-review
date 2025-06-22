import yaml
from pr_review_agent.config import Config


def test_env_var_substitution(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "testtoken123")
    config = Config()
    assert config.get("github.token") == "testtoken123"


def test_user_config_override(tmp_path):
    user_config = {"ollama": {"model": "codellama:13b", "temperature": 0.5}}
    user_config_path = tmp_path / "user_config.yaml"
    with open(user_config_path, "w") as f:
        yaml.dump(user_config, f)
    config = Config(str(user_config_path))
    assert config.get("ollama.model") == "codellama:13b"
    assert config.get("ollama.temperature") == 0.5
