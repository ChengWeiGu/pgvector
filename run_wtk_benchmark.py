# -*- coding: utf-8 -*-
import time
import argparse
from tqdm import tqdm
import pandas as pd
import configparser
import DatabaseProcess
import EmbeddingFunction

config=configparser.ConfigParser()
config.read("Config.ini")


az_embed = EmbeddingFunction.AzureOpenAIEmbeddings()
pg_vector = DatabaseProcess.PGVector(DatabaseProcess.pg_setting)


class Benchmark2PGVector:
    
    def __init__(self, benchmark_file_path, 
                 benchmark_sheet_name, 
                 pg_table_name):
        
        self.benchmark_file_path=benchmark_file_path
        self.benchmark_sheet_name=benchmark_sheet_name
        self.pg_table_name=pg_table_name
        self.benchmark_df = self.preprocess_benchmark_df()
    
    def preprocess_benchmark_df(self):
        # read excel
        benchmark_df=pd.read_excel(self.benchmark_file_path, 
                                   sheet_name=self.benchmark_sheet_name,
                                   skiprows=1)
        benchmark_df=benchmark_df.fillna('')
        benchmark_df['備註'] = benchmark_df['備註'].apply(lambda x: str(x).strip())
        # end customer flag
        benchmark_df['customer_flag'] = benchmark_df['備註'].apply(lambda x: 1 if (x.startswith('Feedback') or x in ['End Customer', 'Ava', 'FAQ']) else 0)
        # distributor flag, then use 80 to replace 81
        benchmark_df['distributor_flag'] = benchmark_df['備註'].apply(lambda x: 1 if (x.startswith('Feedback') or x in ['Distributor', 'End Customer', 'Ava', 'FAQ']) else 0)
        benchmark_df.loc[benchmark_df['Order'] == 81, 'distributor_flag'] = 0
        # change order to id-order
        benchmark_df['Order'] = benchmark_df['Order'].apply(lambda x: f"id-{x}")
        # reset index
        benchmark_df=benchmark_df.reset_index(drop=True)
        return benchmark_df

    def write_benchmark_to_pgvector(self):
        doc_cnt = 0
        fail_list = []
        for idx , row in tqdm(self.benchmark_df.iterrows(), 
                              total=len(self.benchmark_df),
                              desc="Processing chunks: ",
                              unit=" ea"):
            try:
                _id = row['Order']
                _question = row["Question"]
                _answer_gt = row["Summarize Agent Response GT"]
                if _answer_gt.strip() in ["NA","N/A",""]:
                    _answer_gt = row["Filter Agent Response GT"]
                
                # define metadata
                metadata = {
                    "source": row['備註'],
                    "pic":row["PIC"],
                    "robot_resp":row["Robot Response"],
                    "feedback_advice":row["Feedback Advice"],
                    "human_think_domain_gt": row["Human Think Domain GT"],
                    "category_gt":row["9-Class GT"],
                    "planner_gt":row["Planner GT"],
                    "customer_flag":row["customer_flag"],
                    "distributor_flag":row["distributor_flag"]
                }
                # 處理metadata格式以便插入pg, 外掛 chunk_context and embedding
                data_keys = list(metadata.keys()) + ["chunk_context","embedding"]
                col_names = ", ".join(data_keys)
                # make chunk_context
                chunk_context = f"Question: {_question}\nGround Truth Answer: {_answer_gt}"
                # 加入 chunk_context
                data_values = list(metadata.values())
                data_values.append(chunk_context)
                # 轉換Embedding, 失敗試三次
                for _ in range(3):
                    chunk_embedding = az_embed.get_embedding(chunk_context)
                    if chunk_embedding is not None:
                        data_values.append(chunk_embedding)
                        # 存入pg
                        data_values = [tuple(data_values)]
                        pg_vector.upsert_data(self.pg_table_name, 
                                              col_names, 
                                              data_values)
                        doc_cnt += 1
                        break
                    else:
                        time.sleep(10)
            except Exception as e:
                fail_list.append((_id, str(e)))
        
        print(f"There are {doc_cnt} added")
        print("fail list:\n",fail_list)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Spec document')
    parser.add_argument('-t', '--table_name', type=str, default="wtk_benchmark", help='創建Postgres Table名稱存入benchmark')
    parser.add_argument('-s', '--sheet_name', type=str, default="Datasets100", help='參考的Sheet名稱')
    parser.add_argument('-d', '--doc_path', type=str, default="./Weinbot_Benchmark.xlsx", help='Benchmark Excel 資料夾位置')
    args = parser.parse_args()
    
    table_name = args.table_name
    if table_name.strip() == "":
        print("table_name is empty")
        exit()
    
    sheet_name = args.sheet_name
    if sheet_name.strip() == "":
        print("sheet_name is empty")
        exit()
    
    doc_path = args.doc_path
    if doc_path.strip() == "":
        print("excel document path is empty")
        exit()
        
        
    print(f"Create table '{table_name}' if not exists....")
    ret_json = pg_vector.create_benchmark_table(table_name=table_name)
    if ret_json["status"] == "fail":
        print(ret_json["error_reason"])
        exit()
    
    
    print("start for customer...")
    benchmark_writter = Benchmark2PGVector(benchmark_file_path = doc_path, 
                                           benchmark_sheet_name = sheet_name, 
                                           pg_table_name = table_name)
    benchmark_writter.write_benchmark_to_pgvector()
    print("done for end cust")