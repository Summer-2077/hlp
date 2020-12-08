# -*- coding: utf-8 -*-
"""
Created on Mon Dec  7 20:06:57 2020

@author: 九童
"""
import tensorflow as tf
import copy

class DecoderBeamSearch(object):

    def __init__(self, beam_size, max_length, worst_score):
        self.BEAM_SIZE = beam_size  # 保存原始beam大小，用于重置
        self.MAX_LEN = max_length - 1
        self.MIN_SCORE = worst_score  # 保留原始worst_score，用于重置

        self.candidates = []  # 保存中间状态序列的容器，元素格式为(score, sequence)类型为(float, [])
        self.result = []  # 用来保存已经遇到结束符的序列

    def __len__(self):
        """当前候选结果数
        """
        return len(self.candidates)

    def reset(self, dec_input):
        """重置搜索

        :param inputs: 已经序列化的输入句子
        :param dec_input: 解码器输入序列
        :return: 无返回值
        """
        self.candidates = []  # 保存中间状态序列的容器，元素格式为(score, sequence)类型为(float, [])
        self.candidates.append((1, dec_input))
        self.dec_inputs = dec_input
        self.beam_size = self.BEAM_SIZE  # 新一轮中，将beam_size重置为原beam大小
        self.worst_score = self.MIN_SCORE  # 新一轮中，worst_score重置
        self.result = []  # 用来保存已经遇到结束符的序列

    def get_search_inputs(self):
        """为下一步预测生成输入

        :return: requests, dec_inputs
        """
        # 生成多beam的decoder的输入
        temp = self.candidates[0][1]
        for i in range(1, len(self)):
            temp = tf.concat([temp, self.candidates[i][1]], axis=0)
        self.dec_inputs = copy.deepcopy(temp)

        return self.dec_inputs

    def _reduce_end(self, end_sign):
        """
        当序列遇到了结束token，需要将该序列从容器中移除
        :return: 无返回值
        """
        for idx, (s, dec) in enumerate(self.candidates):
            temp = dec.numpy()
            if temp[0][-1] == end_sign:
                self.result.append((self.candidates[idx][0], self.candidates[idx][1]))
                del self.candidates[idx]
                self.beam_size -= 1

    def expand(self, predictions, end_sign):
        """ 根据预测结果对候选进行扩展

        往容器中添加预测结果，在本方法中对预测结果进行整理、排序的操作
        :param predictions: 传入每个时间步的模型预测值
        :return: 无返回值
        """
        prev_candidates = copy.deepcopy(self.candidates)
        self.candidates.clear()
        predictions = predictions.numpy()
        for i in range(self.dec_inputs.shape[0]):
            for _ in range(self.beam_size):
                token_index = tf.argmax(input=predictions[i], axis=0)
                # 计算分数
                score = prev_candidates[i][0] * predictions[i][token_index]
                predictions[i][token_index] = 0
                # 判断容器容量以及分数比较
                if len(self) < self.beam_size or score > self.worst_score:
                    self.candidates.append(
                        (score, tf.concat([prev_candidates[i][1], tf.constant([[token_index.numpy()]], shape=(1, 1))], axis=-1)))
                    if len(self) > self.beam_size:
                        sorted_scores = sorted([(s, idx) for idx, (s, _) in enumerate(self.candidates)])
                        del self.candidates[sorted_scores[0][1]]
                        self.worst_score = sorted_scores[1][0]
                    else:
                        self.worst_score = min(score, self.worst_score)
        self._reduce_end(end_sign=end_sign)

    def get_result(self, top_k=1):
        """获得概率最高的top_k个结果

        :return: 概率最高的top_k个结果
        """
        results = [element[1] for element in sorted(self.result)[-top_k:]]
        return results