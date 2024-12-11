'''
!pip install pandas

关键节点，网络法，计算项目工期和成本
'''
import pandas as pd

from dataclasses import dataclass
from decimal import Decimal
from typing import List
from copy import deepcopy
from itertools import combinations

@dataclass
class Task:
    name: str # 任务名
    duration: float # 任务工期
    predecessors: list # 前置任务名列表
    cost: Decimal = None # 任务成本
    speed_up_duration: float = None # 加速工期
    speed_up_cost: Decimal = None # 加速成本

    ES: float = 0 # Early Start
    TF: float = 0 # Total Finish
    EF: float = 0 # Early Finish
    LS: float = 0 # Late Start
    FF: float = 0 # Free Finish
    LF: float = 0 # Late Finish
    
    is_critical: bool = False # 是否为关键路径节点
    is_speed_up: bool = False # 是否为加速节点
    index: int = -1 # 任务索引
    
class TaskTool:
    @staticmethod
    def calc_ES_EF(tasks_df: pd.DataFrame) -> pd.DataFrame:
        '''
        计算Early Start和Early Finish
        '''
        tasks_df['ES'] = 0
        tasks_df['EF'] = 0
        
        for i, row in tasks_df.iterrows():
                        
            duration = row['speed_up_duration'] if row['is_speed_up'] else row['duration']
            
            if len(row['predecessors']) == 0:
                # tasks_df.at[i, 'ES'] = 0
                tasks_df.at[i, 'EF'] = duration
                continue
            
            max_ef = 0
            for pred in row['predecessors']:
                ef = tasks_df.loc[tasks_df['name'] == pred, 'EF'].values[0]
                if ef > max_ef:
                    max_ef = ef
                    
            tasks_df.at[i, 'ES'] = max_ef
            tasks_df.at[i, 'EF'] = max_ef + duration
            
        return tasks_df
    
    @staticmethod
    def calc_LS_LF(tasks_df: pd.DataFrame) -> pd.DataFrame:
        '''
        计算Late Start和Late Finish
        '''
        tasks_df['LS'] = 0
        tasks_df['LF'] = 0
        
        new_tasks_df = tasks_df.sort_values(by='EF', ascending=False, inplace=False)
        
        for _, new_row in new_tasks_df.iterrows():
            i = new_row['index']
            # row = tasks_df.iloc[i]
            row = tasks_df.iloc[i]
            duration = row['speed_up_duration'] if row['is_speed_up'] else row['duration']
            
            if row['EF'] == tasks_df['EF'].max(): # 最后一个任务
                tasks_df.at[i, 'LF'] = row['EF']
                tasks_df.at[i, 'LS'] = row['EF'] - duration
                continue
            
            befores = tasks_df[tasks_df['predecessors'].apply(lambda x: row['name'] in x)]
            
            min_ls = tasks_df['EF'].max()
            
            for j, before in befores.iterrows():
                ls = tasks_df.at[j, 'LS']
                if ls < min_ls:
                    min_ls = ls
                    
            tasks_df.at[i, 'LF'] = min_ls
            tasks_df.at[i, 'LS'] = min_ls - duration
            
        return tasks_df
    
    @staticmethod
    def calc_TF_FF(tasks_df: pd.DataFrame) -> pd.DataFrame:
        '''
        计算Total Finish和Free Finish
        '''
        tasks_df['TF'] = tasks_df['LS'] - tasks_df['ES']
        tasks_df['FF'] = 0
        
        for i, row in tasks_df.iterrows():
            befores = tasks_df[tasks_df['predecessors'].apply(lambda x: row['name'] in x)]
            if len(befores) == 0:
                tasks_df.at[i, 'FF'] = tasks_df.at[i, 'TF']
                continue
            
            if befores.empty:
                min_es = row['EF']
                
            else:
                min_es = befores['ES'].min()
                
            tasks_df.at[i, 'FF'] = min_es - row['EF']
            
        return tasks_df
    
    @staticmethod
    def calc_critical_node(tasks_df: pd.DataFrame) -> pd.DataFrame:
        '''
        计算关键路径节点
        '''
        tasks_df['is_critical'] = (tasks_df['TF'] == 0) & (tasks_df['FF'] == 0)
        return tasks_df
    
    @staticmethod
    def process(tasks_df: pd.DataFrame) -> pd.DataFrame:
        tasks_df = TaskTool.calc_ES_EF(tasks_df)
        tasks_df = TaskTool.calc_LS_LF(tasks_df)
        tasks_df = TaskTool.calc_TF_FF(tasks_df)
        tasks_df = TaskTool.calc_critical_node(tasks_df)
        return tasks_df
        
    @staticmethod
    def get_total_duration(tasks_df: pd.DataFrame) -> float:
        '''
        计算总工期
        '''
        return tasks_df['EF'].max()
    
    @staticmethod
    def get_total_cost(tasks_df: pd.DataFrame) -> Decimal:
        '''
        计算总成本
        '''
        cost_series = tasks_df.apply(
            lambda row: row['speed_up_cost'] if row['is_speed_up'] else row['cost'],
            axis=1
        )
        return cost_series.sum()
    
class TaskPlan:
    def __init__(self, tasks:List[Task]|pd.DataFrame):
        # self.tasks = deepcopy(tasks)
        if isinstance(tasks, pd.DataFrame):
            self.tasks_df = tasks
        elif isinstance(tasks, list):
            self.tasks_df = pd.DataFrame(tasks)
            
        # if not all(self.tasks_df['index'].values == -1):
        self.tasks_df['index'] = list(range(len(tasks)))
        self.calc_critical_path()
        self.tasks_df['save_duration'] = self.tasks_df['duration'] - self.tasks_df['speed_up_duration']
        # self.tasks_df['speed_up_can_save'] = 0
        speed_up_can_save = []
        for i, row in self.tasks_df.iterrows():
            tmp_tasks_df = deepcopy(self.tasks_df)
            tmp_tasks_df.at[i, 'is_speed_up'] = True
            tmp_tasks_df = TaskTool.process(tmp_tasks_df)
            total_duration = TaskTool.get_total_duration(tmp_tasks_df)
            speed_up_can_save.append(self.total_duration - total_duration)
        self.tasks_df['speed_up_can_save'] = speed_up_can_save
            
        
    @property
    def total_duration(self):
        return TaskTool.get_total_duration(self.tasks_df)
    
    @property
    def total_cost(self):
        return TaskTool.get_total_cost(self.tasks_df)
    
    @property
    def critical_path(self):
        return self.tasks_df[self.tasks_df['is_critical']]['name'].values.tolist()
    
    @property
    def critical_nodes(self)->pd.DataFrame:
        return self.tasks_df[self.tasks_df['is_critical']]
        
    def calc_critical_path(self):
        self.tasks_df = TaskTool.process(self.tasks_df)
        
    def print_critical_path(self):
        print('Critical Path:', self.critical_path)
        print('Total Duration:', self.total_duration)
        print('Total Cost:', self.total_cost)
        

    def min_duration_plan(self)->'TaskPlan':
        tasks_df = deepcopy(self.tasks_df)
        
        tasks_df['is_speed_up'] = True
        tasks_df = TaskTool.process(tasks_df)
        
        return TaskPlan(tasks_df)
        
    def calc_all_plans(self)->pd.DataFrame:
        '''
        计算所有的赶工计划
        '''
        tasks = self.tasks_df['index'].values.tolist()
        all_combinations = []
        
        for ele in range(1, len(tasks)+1):
            all_combinations.extend(combinations(tasks, ele))
        
        all_plans = []
        for combination in all_combinations:
            speed_up_tasks = []
            
            tmp_df = deepcopy(self.tasks_df)
            for task_id in combination:
                tmp_df.at[task_id, 'is_speed_up'] = True
                speed_up_tasks.append(tmp_df.at[task_id, 'name'])
            tmp_df = TaskTool.process(tmp_df)
            all_plans.append({
                'speed_up_tasks': speed_up_tasks,
                'save_duration': self.total_duration - TaskTool.get_total_duration(tmp_df),
                'extra_cost': TaskTool.get_total_cost(tmp_df) - self.total_cost,
                'total_duration': TaskTool.get_total_duration(tmp_df),
                'total_cost': TaskTool.get_total_cost(tmp_df),
                'critical_path': tmp_df[tmp_df['is_critical']]['name'].values.tolist()
            })
            
        return pd.DataFrame(all_plans)
    
    def get_min_cost_plan(self)->pd.DataFrame:
        '''
        获取最小成本的赶工计划
        '''
        
        all_plans = self.calc_all_plans()
        
        saving_days = all_plans['save_duration'].unique()
        
        result = []
        for saving_day in saving_days:
            if saving_day == 0:
                continue
            min_cost = all_plans[all_plans['save_duration'] == saving_day]['extra_cost'].min()
            min_plans = all_plans[(all_plans['save_duration'] == saving_day) & (all_plans['extra_cost'] == min_cost)]
            result.append(min_plans)
            
        return pd.concat(result)
            
if __name__ == '__main__':
    tasks = [
        Task(name="A", duration=4, cost=1500, speed_up_duration=3, speed_up_cost=1900, predecessors=[]),
        Task(name="B", duration=6, cost=1000, speed_up_duration=4, speed_up_cost=1300, predecessors=["A"]),
        Task(name="C", duration=8, cost=1700, speed_up_duration=6, speed_up_cost=2000, predecessors=["A"]),
        Task(name="D", duration=7, cost=1200, speed_up_duration=5, speed_up_cost=1400, predecessors=["A"]),
        Task(name="E", duration=4, cost=500, speed_up_duration=3, speed_up_cost=600, predecessors=["B"]),
        Task(name="F", duration=6, cost=2000, speed_up_duration=4, speed_up_cost=2400, predecessors=["B", "C", "D"]),
        Task(name="G", duration=6, cost=1600, speed_up_duration=4, speed_up_cost=1800, predecessors=["D"]),
        Task(name="H", duration=6, cost=2400, speed_up_duration=4, speed_up_cost=3100, predecessors=["F", "G"])
    ]

    plan = TaskPlan(tasks)
    plan.print_critical_path()
    plan.get_min_cost_plan().to_csv("test.csv", index=False)