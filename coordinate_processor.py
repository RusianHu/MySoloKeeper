# -*- coding: utf-8 -*-
"""
坐标处理和平滑模块
"""

import json
import re
import math
from typing import List, Dict, Optional, Tuple
from config import *


class CoordinateProcessor:
    """坐标处理器，负责解析、验证和平滑人脸坐标"""
    
    def __init__(self, canvas_width: int, canvas_height: int):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.previous_faces = []
        self.no_face_counter = 0
        
    def is_valid_face_coordinate(self, face: Dict) -> bool:
        """验证人脸坐标是否合理"""
        try:
            # 检查坐标是否为数字
            if not all(isinstance(face.get(key), (int, float)) for key in ['x', 'y', 'width', 'height']):
                return False
            
            x, y, width, height = face['x'], face['y'], face['width'], face['height']
            
            # 检查坐标是否在合理范围内
            if x < 0 or y < 0 or width <= 0 or height <= 0:
                return False
            
            # 检查坐标是否在画布范围内
            if x + width > self.canvas_width or y + height > self.canvas_height:
                return False
            
            # 检查人脸框大小是否合理
            if width < MIN_FACE_SIZE or height < MIN_FACE_SIZE:
                return False
            
            if (width > self.canvas_width * MAX_FACE_SIZE_RATIO or 
                height > self.canvas_height * MAX_FACE_SIZE_RATIO):
                return False
            
            # 检查宽高比是否合理
            aspect_ratio = width / height
            if aspect_ratio < FACE_ASPECT_RATIO_MIN or aspect_ratio > FACE_ASPECT_RATIO_MAX:
                return False
            
            return True
            
        except (KeyError, TypeError, ZeroDivisionError):
            return False
    
    def calculate_face_similarity(self, face1: Dict, face2: Dict) -> float:
        """计算两个人脸框的相似度（0-1之间，1表示完全相同）"""
        try:
            # 计算中心点距离
            center1_x = face1['x'] + face1['width'] / 2
            center1_y = face1['y'] + face1['height'] / 2
            center2_x = face2['x'] + face2['width'] / 2
            center2_y = face2['y'] + face2['height'] / 2
            
            # 计算中心点距离与画布对角线的比值（归一化）
            canvas_diagonal = math.sqrt(self.canvas_width**2 + self.canvas_height**2)
            center_distance = math.sqrt((center1_x - center2_x)**2 + (center1_y - center2_y)**2)
            normalized_distance = 1 - (center_distance / canvas_diagonal)
            
            # 计算大小相似度
            area1 = face1['width'] * face1['height']
            area2 = face2['width'] * face2['height']
            area_ratio = min(area1, area2) / max(area1, area2)
            
            # 综合相似度（距离和大小各占权重）
            return normalized_distance * 0.7 + area_ratio * 0.3
            
        except (KeyError, TypeError, ZeroDivisionError):
            return 0.0
    
    def find_most_similar_face(self, face: Dict, face_array: List[Dict]) -> Optional[Dict]:
        """查找最相似的人脸"""
        max_similarity = 0
        most_similar_face = None
        
        for candidate_face in face_array:
            similarity = self.calculate_face_similarity(face, candidate_face)
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_face = candidate_face
        
        # 只有相似度大于阈值才认为是相似的人脸
        return most_similar_face if max_similarity > SIMILARITY_THRESHOLD else None
    
    def smooth_face_coordinates(self, current_faces: List[Dict]) -> List[Dict]:
        """平滑人脸坐标，减少抖动"""
        # 如果没有当前人脸，增加无人脸计数器
        if not current_faces:
            self.no_face_counter += 1
            
            # 如果连续多次没有检测到人脸，才清除之前的人脸框
            if self.no_face_counter >= MAX_NO_FACE_COUNT:
                self.previous_faces = []
                return []
            else:
                # 否则继续使用之前的人脸框
                return self.previous_faces
        
        # 重置无人脸计数器
        self.no_face_counter = 0
        
        # 如果之前没有人脸，直接使用当前人脸
        if not self.previous_faces:
            self.previous_faces = current_faces.copy()
            return current_faces
        
        # 平滑处理：将当前人脸与之前人脸进行匹配和平均
        smoothed_faces = []
        
        # 处理当前检测到的每个人脸
        for current_face in current_faces:
            # 查找之前帧中最相似的人脸
            similar_previous_face = self.find_most_similar_face(current_face, self.previous_faces)
            
            if similar_previous_face:
                # 如果找到相似的人脸，进行平滑处理（加权平均）
                weight = SMOOTHING_WEIGHT  # 当前帧权重
                smoothed_face = {
                    'x': round(current_face['x'] * weight + similar_previous_face['x'] * (1 - weight)),
                    'y': round(current_face['y'] * weight + similar_previous_face['y'] * (1 - weight)),
                    'width': round(current_face['width'] * weight + similar_previous_face['width'] * (1 - weight)),
                    'height': round(current_face['height'] * weight + similar_previous_face['height'] * (1 - weight))
                }
                smoothed_faces.append(smoothed_face)
            else:
                # 如果没有找到相似的人脸，直接使用当前人脸
                smoothed_faces.append(current_face)
        
        # 更新previous_faces用于下一次比较
        self.previous_faces = smoothed_faces.copy()
        
        return smoothed_faces
    
    def parse_face_detection_response(self, response: str) -> List[Dict]:
        """解析SmolVLM返回的JSON响应，提取人脸坐标"""
        try:
            # 检查响应是否明确表示没有人脸
            no_face_indicators = [
                "no face", "no faces", "cannot detect", "didn't detect", 
                "not detect", "no person", "no human"
            ]
            
            if any(indicator in response.lower() for indicator in no_face_indicators):
                return []
            
            # 检查是否有空的faces数组
            if '"faces":[]' in response or '"faces": []' in response:
                return []
            
            # 尝试直接解析完整JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                try:
                    json_str = json_match.group(0)
                    data = json.loads(json_str)
                    
                    if data and 'faces' in data and isinstance(data['faces'], list):
                        if not data['faces']:
                            return []
                        
                        # 过滤出有效的人脸坐标
                        valid_faces = []
                        for face in data['faces']:
                            if (isinstance(face, dict) and 
                                all(key in face for key in ['x', 'y', 'width', 'height'])):
                                valid_faces.append(face)
                        
                        return valid_faces
                        
                except json.JSONDecodeError:
                    pass
            
            # 尝试从文本中提取单个人脸坐标对象
            face_obj_pattern = r'\{\s*"x"\s*:\s*(\d+)\s*,\s*"y"\s*:\s*(\d+)\s*,\s*"width"\s*:\s*(\d+)\s*,\s*"height"\s*:\s*(\d+)\s*\}'
            matches = re.finditer(face_obj_pattern, response)
            
            extracted_faces = []
            for match in matches:
                face = {
                    'x': int(match.group(1)),
                    'y': int(match.group(2)),
                    'width': int(match.group(3)),
                    'height': int(match.group(4))
                }
                extracted_faces.append(face)
            
            if extracted_faces:
                return extracted_faces
            
            # 尝试提取数字坐标
            coord_pattern = r'x\s*[:=]\s*(\d+)[,\s]+y\s*[:=]\s*(\d+)[,\s]+width\s*[:=]\s*(\d+)[,\s]+height\s*[:=]\s*(\d+)'
            matches = re.finditer(coord_pattern, response, re.IGNORECASE)
            
            for match in matches:
                face = {
                    'x': int(match.group(1)),
                    'y': int(match.group(2)),
                    'width': int(match.group(3)),
                    'height': int(match.group(4))
                }
                extracted_faces.append(face)
            
            return extracted_faces
            
        except Exception as e:
            print(f"解析人脸检测响应失败: {e}")
            return []
    
    def process_faces(self, response: str) -> List[Dict]:
        """处理人脸检测响应，返回经过验证和平滑的人脸坐标"""
        # 解析响应
        raw_faces = self.parse_face_detection_response(response)
        
        # 过滤有效坐标
        valid_faces = [face for face in raw_faces if self.is_valid_face_coordinate(face)]
        
        # 应用平滑处理
        smoothed_faces = self.smooth_face_coordinates(valid_faces)
        
        return smoothed_faces
    
    def reset(self):
        """重置处理器状态"""
        self.previous_faces = []
        self.no_face_counter = 0
