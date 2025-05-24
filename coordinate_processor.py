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
    """坐标处理器，负责解析、验证和平滑人类活动检测坐标"""

    def __init__(self, canvas_width: int, canvas_height: int):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.previous_humans = []
        self.no_human_counter = 0

    def is_valid_human_coordinate(self, human: Dict) -> bool:
        """验证人类检测坐标是否合理"""
        try:
            # 检查坐标是否为数字
            if not all(isinstance(human.get(key), (int, float)) for key in ['x', 'y', 'width', 'height']):
                return False

            x, y, width, height = human['x'], human['y'], human['width'], human['height']

            # 检查坐标是否在合理范围内
            if x < 0 or y < 0 or width <= 0 or height <= 0:
                return False

            # 检查坐标是否在画布范围内
            if x + width > self.canvas_width or y + height > self.canvas_height:
                return False

            # 检查人类检测框大小是否合理
            if width < MIN_HUMAN_SIZE or height < MIN_HUMAN_SIZE:
                return False

            if (width > self.canvas_width * MAX_HUMAN_SIZE_RATIO or
                height > self.canvas_height * MAX_HUMAN_SIZE_RATIO):
                return False

            # 检查宽高比是否合理
            aspect_ratio = width / height
            if aspect_ratio < HUMAN_ASPECT_RATIO_MIN or aspect_ratio > HUMAN_ASPECT_RATIO_MAX:
                return False

            return True

        except (KeyError, TypeError, ZeroDivisionError):
            return False

    def is_valid_face_coordinate(self, face: Dict) -> bool:
        """验证人脸坐标是否合理（保持向后兼容）"""
        return self.is_valid_human_coordinate(face)

    def calculate_human_similarity(self, human1: Dict, human2: Dict) -> float:
        """计算两个人类检测框的相似度（0-1之间，1表示完全相同）"""
        try:
            # 计算中心点距离
            center1_x = human1['x'] + human1['width'] / 2
            center1_y = human1['y'] + human1['height'] / 2
            center2_x = human2['x'] + human2['width'] / 2
            center2_y = human2['y'] + human2['height'] / 2

            # 计算中心点距离与画布对角线的比值（归一化）
            canvas_diagonal = math.sqrt(self.canvas_width**2 + self.canvas_height**2)
            center_distance = math.sqrt((center1_x - center2_x)**2 + (center1_y - center2_y)**2)
            normalized_distance = 1 - (center_distance / canvas_diagonal)

            # 计算大小相似度
            area1 = human1['width'] * human1['height']
            area2 = human2['width'] * human2['height']
            area_ratio = min(area1, area2) / max(area1, area2)

            # 综合相似度（距离和大小各占权重）
            return normalized_distance * 0.7 + area_ratio * 0.3

        except (KeyError, TypeError, ZeroDivisionError):
            return 0.0

    def calculate_face_similarity(self, face1: Dict, face2: Dict) -> float:
        """计算两个人脸框的相似度（保持向后兼容）"""
        return self.calculate_human_similarity(face1, face2)

    def find_most_similar_human(self, human: Dict, human_array: List[Dict]) -> Optional[Dict]:
        """查找最相似的人类检测"""
        max_similarity = 0
        most_similar_human = None

        for candidate_human in human_array:
            similarity = self.calculate_human_similarity(human, candidate_human)
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_human = candidate_human

        # 只有相似度大于阈值才认为是相似的人类检测
        return most_similar_human if max_similarity > SIMILARITY_THRESHOLD else None

    def find_most_similar_face(self, face: Dict, face_array: List[Dict]) -> Optional[Dict]:
        """查找最相似的人脸（保持向后兼容）"""
        return self.find_most_similar_human(face, face_array)

    def smooth_human_coordinates(self, current_humans: List[Dict]) -> List[Dict]:
        """平滑人类检测坐标，减少抖动"""
        # 如果没有当前人类检测，增加无人类计数器
        if not current_humans:
            self.no_human_counter += 1

            # 如果连续多次没有检测到人类，才清除之前的检测框
            if self.no_human_counter >= MAX_NO_HUMAN_COUNT:
                self.previous_humans = []
                return []
            else:
                # 否则继续使用之前的检测框
                return self.previous_humans

        # 重置无人类计数器
        self.no_human_counter = 0

        # 如果之前没有人类检测，直接使用当前检测
        if not self.previous_humans:
            self.previous_humans = current_humans.copy()
            return current_humans

        # 平滑处理：将当前检测与之前检测进行匹配和平均
        smoothed_humans = []

        # 处理当前检测到的每个人类
        for current_human in current_humans:
            # 查找之前帧中最相似的人类检测
            similar_previous_human = self.find_most_similar_human(current_human, self.previous_humans)

            if similar_previous_human:
                # 如果找到相似的检测，进行平滑处理（加权平均）
                weight = SMOOTHING_WEIGHT  # 当前帧权重
                smoothed_human = {
                    'x': round(current_human['x'] * weight + similar_previous_human['x'] * (1 - weight)),
                    'y': round(current_human['y'] * weight + similar_previous_human['y'] * (1 - weight)),
                    'width': round(current_human['width'] * weight + similar_previous_human['width'] * (1 - weight)),
                    'height': round(current_human['height'] * weight + similar_previous_human['height'] * (1 - weight))
                }
                smoothed_humans.append(smoothed_human)
            else:
                # 如果没有找到相似的检测，直接使用当前检测
                smoothed_humans.append(current_human)

        # 更新previous_humans用于下一次比较
        self.previous_humans = smoothed_humans.copy()

        return smoothed_humans

    def smooth_face_coordinates(self, current_faces: List[Dict]) -> List[Dict]:
        """平滑人脸坐标，减少抖动（保持向后兼容）"""
        return self.smooth_human_coordinates(current_faces)

    def parse_human_activity_response(self, response: str) -> List[Dict]:
        """解析SmolVLM返回的JSON响应，提取人类活动检测坐标"""
        try:
            # 检查响应是否明确表示没有人类活动
            no_human_indicators = [
                "no human", "no humans", "no person", "no people", "no activity",
                "cannot detect", "didn't detect", "not detect", "no one"
            ]

            if any(indicator in response.lower() for indicator in no_human_indicators):
                return []

            # 检查是否有空的humans数组
            if '"humans":[]' in response or '"humans": []' in response:
                return []

            # 尝试直接解析完整JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                try:
                    json_str = json_match.group(0)
                    data = json.loads(json_str)

                    # 优先查找humans字段
                    if data and 'humans' in data and isinstance(data['humans'], list):
                        if not data['humans']:
                            return []

                        # 过滤出有效的人类检测坐标
                        valid_humans = []
                        for human in data['humans']:
                            if (isinstance(human, dict) and
                                all(key in human for key in ['x', 'y', 'width', 'height'])):
                                valid_humans.append(human)

                        return valid_humans

                    # 向后兼容：如果没有humans字段，尝试faces字段
                    elif data and 'faces' in data and isinstance(data['faces'], list):
                        if not data['faces']:
                            return []

                        # 过滤出有效的坐标
                        valid_humans = []
                        for face in data['faces']:
                            if (isinstance(face, dict) and
                                all(key in face for key in ['x', 'y', 'width', 'height'])):
                                valid_humans.append(face)

                        return valid_humans

                except json.JSONDecodeError:
                    pass

            # 尝试从文本中提取单个人类检测坐标对象
            human_obj_pattern = r'\{\s*"x"\s*:\s*(\d+)\s*,\s*"y"\s*:\s*(\d+)\s*,\s*"width"\s*:\s*(\d+)\s*,\s*"height"\s*:\s*(\d+)\s*\}'
            matches = re.finditer(human_obj_pattern, response)

            extracted_humans = []
            for match in matches:
                human = {
                    'x': int(match.group(1)),
                    'y': int(match.group(2)),
                    'width': int(match.group(3)),
                    'height': int(match.group(4))
                }
                extracted_humans.append(human)

            if extracted_humans:
                return extracted_humans

            # 尝试提取数字坐标
            coord_pattern = r'x\s*[:=]\s*(\d+)[,\s]+y\s*[:=]\s*(\d+)[,\s]+width\s*[:=]\s*(\d+)[,\s]+height\s*[:=]\s*(\d+)'
            matches = re.finditer(coord_pattern, response, re.IGNORECASE)

            for match in matches:
                human = {
                    'x': int(match.group(1)),
                    'y': int(match.group(2)),
                    'width': int(match.group(3)),
                    'height': int(match.group(4))
                }
                extracted_humans.append(human)

            return extracted_humans

        except Exception as e:
            print(f"解析人类活动检测响应失败: {e}")
            return []

    def parse_face_detection_response(self, response: str) -> List[Dict]:
        """解析SmolVLM返回的JSON响应，提取人脸坐标（保持向后兼容）"""
        return self.parse_human_activity_response(response)

    def process_humans(self, response: str) -> List[Dict]:
        """处理人类活动检测响应，返回经过验证和平滑的人类检测坐标"""
        # 解析响应
        raw_humans = self.parse_human_activity_response(response)

        # 过滤有效坐标
        valid_humans = [human for human in raw_humans if self.is_valid_human_coordinate(human)]

        # 应用平滑处理
        smoothed_humans = self.smooth_human_coordinates(valid_humans)

        return smoothed_humans

    def process_faces(self, response: str) -> List[Dict]:
        """处理人脸检测响应，返回经过验证和平滑的人脸坐标（保持向后兼容）"""
        return self.process_humans(response)

    def reset(self):
        """重置处理器状态"""
        self.previous_humans = []
        self.no_human_counter = 0
        # 保持向后兼容
        self.previous_faces = []
        self.no_face_counter = 0
