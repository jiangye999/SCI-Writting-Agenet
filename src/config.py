"""
配置管理模块
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class Config:
    """配置管理类"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置

        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """加载配置文件"""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}
        else:
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

    def reload(self) -> None:
        """重新加载配置文件"""
        self._load_config()

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持点号分隔的路径，如 'api.model'
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

            if value is None:
                return default

        return value

    @property
    def api_key(self) -> str:
        """获取API密钥"""
        return self.get("api.api_key", "")

    @property
    def model(self) -> str:
        """获取模型名称"""
        return self.get("api.model", "claude-3-opus-20240229")

    @property
    def temperature(self) -> float:
        """获取温度参数"""
        return float(self.get("api.temperature", 0.7))

    @property
    def literature_db_path(self) -> str:
        """获取文献数据库路径"""
        return self.get("database.literature_db", "data/literature.db")

    @property
    def citation_style(self) -> str:
        """获取引用格式"""
        return self.get("citation.style", "author-year")

    @property
    def quality_thresholds(self) -> Dict[str, float]:
        """获取质量阈值"""
        return self.get(
            "quality.thresholds",
            {
                "completeness": 0.80,
                "style_match": 0.75,
                "citation_accuracy": 0.95,
                "overall": 0.85,
            },
        )

    @property
    def paths(self) -> Dict[str, str]:
        """获取路径配置"""
        return {
            "input_dir": self.get("paths.input_dir", "input"),
            "output_dir": self.get("paths.output_dir", "output"),
            "style_dir": self.get("paths.style_dir", "output/style"),
            "sections_dir": self.get("paths.sections_dir", "output/sections"),
            "final_dir": self.get("paths.final_dir", "output/final"),
        }

    def get_agent_target_words(self, agent_type: str) -> tuple:
        """
        获取Agent目标字数范围

        Args:
            agent_type: Agent类型 (introduction, methods, results, discussion, abstract)

        Returns:
            (最小字数, 最大字数)
        """
        key = f"agents.workers.{agent_type}"
        config = self.get(key, {})
        return (
            config.get("target_words_min", 500),
            config.get("target_words_max", 700),
        )

    def update(self, key: str, value: Any) -> None:
        """
        更新配置值

        Args:
            key: 配置键
            value: 新的值
        """
        keys = key.split(".")
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self, path: Optional[str] = None) -> None:
        """
        保存配置到文件

        Args:
            path: 保存路径，如果为None则保存到原路径
        """
        save_path = Path(path) if path else self.config_path
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "w", encoding="utf-8") as f:
            yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)


# 全局配置实例
_config: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """获取全局配置实例"""
    global _config
    if _config is None or config_path is not None:
        _config = Config(config_path)
    return _config


def reset_config() -> None:
    """重置配置"""
    global _config
    _config = None
