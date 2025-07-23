# -*- coding: utf-8 -*-
import os
import ast
import psycopg2
import configparser
import EmbeddingFunction
from psycopg2.extras import execute_values


config=configparser.ConfigParser()
config.read("Config.ini")

## default pg setting
pg_setting = {
    'host': config['POSTGRES_DB']['host'],
    'database': config['POSTGRES_DB']['database'],
    'user': config['POSTGRES_DB']['user'],
    'password': config['POSTGRES_DB']['password'],
    'port': config['POSTGRES_DB']['port']
}

embed_dim = EmbeddingFunction.embed_dim


class PGVector:
    
    def __init__(self, pg_setting):
        self.pg_setting = pg_setting
    
    def get_connection(self):
        return psycopg2.connect(**self.pg_setting)
    
    def upsert_data(self, tbl_names:str, col_names:str, pairs:list[tuple]):
        """批次寫入"""
        sql = f"INSERT INTO {tbl_names} ({col_names}) VALUES %s ON CONFLICT DO NOTHING"
        with self.get_connection() as conn, conn.cursor() as cur:
            execute_values(cur, sql, pairs)
            conn.commit()
    
    def create_jssdk_table(self, embed_dim = embed_dim, table_name = "jssdk"):
        return_json = {
            "status":"fail",
            "error_reason":""
        }
        try:
            ddl = f"""
            CREATE EXTENSION IF NOT EXISTS vector;
            CREATE TABLE IF NOT EXISTS {table_name} (
                id bigserial PRIMARY KEY,
                source varchar(256),
                url varchar(512),
                root_url varchar(512),
                class_name varchar(256),
                description text,
                chunk_context text,
                embedding vector({embed_dim})
            );
            """
            with self.get_connection() as conn, conn.cursor() as cur:
                cur.execute(ddl)
                conn.commit()
        
            return_json["status"] = "success"
        
        except Exception as e:
            error_reason = f"create jssdk fail because {e}"
            return_json["error_reason"] = error_reason
            print(error_reason)
        
        return return_json
    
    def query_jssdk_nearest(self, vec, table_name = "jssdk", top_k = 10):
        """回傳與 vec 最近的 K 筆"""
        #  PostgreSQL 無法自動進行型別轉換，須明確地進行型別轉換 ::vector
        sql = f"""
            SELECT url, class_name, description, chunk_context,
                embedding <-> %s::vector AS distance
            FROM   {table_name}
            ORDER BY distance ASC
            LIMIT {top_k};
            """
            
        results = []
        with self.get_connection() as conn, conn.cursor() as cur:
            cur.execute(sql, (vec,))
            rows = cur.fetchall() # 獲取所有查詢結果
            columns = [desc[0] for desc in cur.description] # 獲取欄位名稱
            # 將結果輸出為 list[dict]
            results = [dict(zip(columns, row)) for row in rows]
            
        return results
    
            
if __name__ == "__main__":
    pg_vector = PGVector(pg_setting)
    ret_json = pg_vector.create_jssdk_table(embed_dim=embed_dim)
    print(ret_json)
    
    
    