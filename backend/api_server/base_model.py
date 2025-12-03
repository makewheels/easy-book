"""
MongoDB 模型基类和索引管理系统
遵循项目规范：不使用数据库唯一约束，仅创建查询性能优化索引
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import OperationFailure
import logging

logger = logging.getLogger(__name__)


class BaseModel(ABC):
    """
    MongoDB 模型基类

    提供统一的索引管理功能：
    - 自动创建查询优化索引
    - 禁止使用唯一约束
    - 支持索引版本管理
    """

    # 子类需要定义的索引配置
    indexes: List[Dict[str, Any]] = []

    @classmethod
    @abstractmethod
    def get_collection_name(cls) -> str:
        """返回MongoDB集合名称"""
        pass

    @classmethod
    def get_indexes(cls) -> List[Dict[str, Any]]:
        """
        获取该模型的所有索引配置

        索引配置格式：
        {
            'fields': [('field1', ASCENDING), ('field2', DESCENDING)],
            'name': 'custom_index_name',  # 可选，默认自动生成
            'background': True,           # 可选，默认True
            'unique': False,             # 强制为False，禁止使用唯一约束
        }
        """
        return cls.indexes

    @classmethod
    def create_indexes(cls, db) -> bool:
        """
        创建模型的所有索引

        Args:
            db: MongoDB 数据库连接

        Returns:
            bool: 是否成功创建所有索引
        """
        collection_name = cls.get_collection_name()
        collection = db[collection_name]

        success = True

        for index_config in cls.get_indexes():
            try:
                # 强制禁止唯一约束
                if index_config.get('unique', False):
                    print(f"[WARNING] {collection_name}: 检测到唯一约束配置，已自动禁用")
                    index_config['unique'] = False

                fields = index_config['fields']
                options = {
                    'background': index_config.get('background', True),
                    'unique': False,  # 强制禁止唯一约束
                }

                # 如果指定了索引名称，添加到选项中
                if 'name' in index_config:
                    options['name'] = index_config['name']

                # 创建索引
                collection.create_index(fields, **options)
                index_name = index_config.get('name', f"index_on_{'_'.join([f[0] for f in fields])}")
                print(f"[OK] {collection_name}: 创建索引 {index_name}")

            except OperationFailure as e:
                if "already exists" in str(e):
                    index_name = index_config.get('name', 'unknown')
                    print(f"[OK] {collection_name}: 索引 {index_name} 已存在")
                else:
                    print(f"[ERROR] {collection_name}: 创建索引失败 - {e}")
                    success = False
            except Exception as e:
                print(f"[ERROR] {collection_name}: 创建索引时发生错误 - {e}")
                success = False

        return success

    @classmethod
    def validate_indexes(cls) -> bool:
        """
        验证索引配置是否符合项目规范

        Returns:
            bool: 配置是否有效
        """
        for index_config in cls.get_indexes():
            # 检查必要字段
            if 'fields' not in index_config:
                print(f"[ERROR] 索引配置缺少 'fields' 字段: {index_config}")
                return False

            # 检查是否意外设置了唯一约束
            if index_config.get('unique', False):
                print(f"[ERROR] 检测到唯一约束配置，违反项目规范: {index_config}")
                return False

        return True


class IndexManager:
    """索引管理器，负责管理所有模型的索引创建"""

    def __init__(self, db):
        self.db = db
        self.models = []

    def register_model(self, model_class: type):
        """注册模型类"""
        if not issubclass(model_class, BaseModel):
            raise ValueError(f"模型类 {model_class} 必须继承自 BaseModel")

        if model_class not in self.models:
            self.models.append(model_class)

    def create_all_indexes(self) -> bool:
        """为所有注册的模型创建索引"""
        print("Starting to create all model indexes...")

        all_success = True

        for model_class in self.models:
            # 验证索引配置
            if not model_class.validate_indexes():
                print(f"[ERROR] Model {model_class.__name__} index validation failed")
                all_success = False
                continue

            # 创建索引
            success = model_class.create_indexes(self.db)
            if not success:
                all_success = False

        if all_success:
            print("All model indexes created successfully")
        else:
            print("Warning: Some indexes failed to create, please check logs")

        return all_success

    def get_model_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有模型的索引状态"""
        status = {}

        for model_class in self.models:
            collection_name = model_class.get_collection_name()
            indexes = model_class.get_indexes()

            status[collection_name] = {
                'model_class': model_class.__name__,
                'index_count': len(indexes),
                'indexes': [
                    {
                        'fields': idx['fields'],
                        'name': idx.get('name', 'auto_generated'),
                        'background': idx.get('background', True)
                    }
                    for idx in indexes
                ]
            }

        return status