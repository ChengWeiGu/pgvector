# -*- coding: utf-8 -*-
import time
import argparse
import DatabaseProcess
import EmbeddingFunction



if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Inference for chroma')
    parser.add_argument('-j','--js',type=str, help='jssdk inference, 請輸入query')
    parser.add_argument('-s','--spec', type=str, help='spec inference, 請輸入query')
    parser.add_argument('-m','--manual', type=str, help='manual inference, 請輸入query')
    args = parser.parse_args()
    
    # init working context and agent object
    working_context = ""
    segment = "===================================================================="
    # summary_agent = OpenAIFunction.SummaryAgent()
    
    if args.js:
        '''**
        * js object demo
        * 1. 連線至 postgres with pgvector
        * 2. 組合並獲取 Working Context 
        *'''
        pg_vector = DatabaseProcess.PGVector(DatabaseProcess.pg_setting)
        az_embed = EmbeddingFunction.AzureOpenAIEmbeddings()
        # query = "How to use mouse event in JS Object?"
        query = args.js
        # conver query into embedding
        query_embedding = az_embed.get_embedding(query)
        # vector search
        time_period_js_start_time = time.time()
        results = pg_vector.query_jssdk_nearest(vec=query_embedding, top_k=10)
        time_period_js_end_time = time.time()
        # working context for LLM later
        working_context = "\n".join([segment + "\n" + res['chunk_context'] for res in results])
        print(working_context)
        print(f"\njs vector search time: {time_period_js_end_time - time_period_js_start_time} sec")