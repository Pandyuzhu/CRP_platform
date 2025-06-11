import os
import json
import logging
from typing import Dict, List, Optional
from fastapi import UploadFile, HTTPException
import shutil
from datetime import datetime

# 配置日志
logger = logging.getLogger(__name__)

class ModelManager:
    """建筑模型管理器"""
    
    def __init__(self):
        """初始化模型管理器"""
        # 模型存储目录
        self.models_dir = "data/building_models"
        self.models_metadata_file = "data/building_models/metadata.json"
        
        # 确保目录存在
        os.makedirs(self.models_dir, exist_ok=True)
        
        # 加载模型元数据
        self.models_metadata = self._load_metadata()
        
        # 支持的模型格式
        self.supported_formats = ['.gltf', '.glb', '.obj', '.stl']
        
    def _load_metadata(self) -> Dict:
        """加载模型元数据"""
        if os.path.exists(self.models_metadata_file):
            try:
                with open(self.models_metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载模型元数据失败: {e}")
                return {}
        return {}
    
    def _save_metadata(self):
        """保存模型元数据"""
        try:
            with open(self.models_metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.models_metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存模型元数据失败: {e}")
    
    async def upload_model(self, file: UploadFile, metadata: Dict) -> Dict:
        """上传建筑模型"""
        # 检查文件格式
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in self.supported_formats:
            raise HTTPException(status_code=400, detail=f"不支持的文件格式。支持的格式: {', '.join(self.supported_formats)}")
        
        # 生成唯一的模型ID
        model_id = f"model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 保存文件
        file_path = os.path.join(self.models_dir, f"{model_id}{file_ext}")
        try:
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
        except Exception as e:
            logger.error(f"保存模型文件失败: {e}")
            raise HTTPException(status_code=500, detail="保存模型文件失败")
        
        # 保存元数据
        model_info = {
            "id": model_id,
            "name": metadata.get("name", file.filename),
            "filename": f"{model_id}{file_ext}",
            "format": file_ext,
            "upload_time": datetime.now().isoformat(),
            "position": metadata.get("position", {"x": 0, "y": 0, "z": 0}),
            "rotation": metadata.get("rotation", {"x": 0, "y": 0, "z": 0}),
            "scale": metadata.get("scale", {"x": 1, "y": 1, "z": 1}),
            "opacity": metadata.get("opacity", 0.7),
            "visible": metadata.get("visible", True),
            "description": metadata.get("description", ""),
            "reference_point": metadata.get("reference_point", {
                "latitude": 0,
                "longitude": 0,
                "altitude": 0
            })
        }
        
        self.models_metadata[model_id] = model_info
        self._save_metadata()
        
        return {
            "success": True,
            "model_id": model_id,
            "message": "模型上传成功",
            "model_info": model_info
        }
    
    def get_models(self) -> List[Dict]:
        """获取所有模型列表"""
        return list(self.models_metadata.values())
    
    def get_model(self, model_id: str) -> Optional[Dict]:
        """获取指定模型信息"""
        return self.models_metadata.get(model_id)
    
    def update_model(self, model_id: str, updates: Dict) -> Dict:
        """更新模型信息"""
        if model_id not in self.models_metadata:
            raise HTTPException(status_code=404, detail="模型不存在")
        
        # 更新允许的字段
        allowed_fields = ["name", "position", "rotation", "scale", "opacity", "visible", "description", "reference_point"]
        for field in allowed_fields:
            if field in updates:
                self.models_metadata[model_id][field] = updates[field]
        
        self._save_metadata()
        
        return {
            "success": True,
            "message": "模型更新成功",
            "model_info": self.models_metadata[model_id]
        }
    
    def delete_model(self, model_id: str) -> Dict:
        """删除模型"""
        if model_id not in self.models_metadata:
            raise HTTPException(status_code=404, detail="模型不存在")
        
        # 删除文件
        model_info = self.models_metadata[model_id]
        file_path = os.path.join(self.models_dir, model_info["filename"])
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.error(f"删除模型文件失败: {e}")
        
        # 删除元数据
        del self.models_metadata[model_id]
        self._save_metadata()
        
        return {
            "success": True,
            "message": "模型删除成功"
        }
    
    def get_model_file_path(self, model_id: str) -> str:
        """获取模型文件路径"""
        if model_id not in self.models_metadata:
            raise HTTPException(status_code=404, detail="模型不存在")
        
        model_info = self.models_metadata[model_id]
        file_path = os.path.join(self.models_dir, model_info["filename"])
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="模型文件不存在")
        
        return file_path

# 创建全局模型管理器实例
model_manager = ModelManager() 