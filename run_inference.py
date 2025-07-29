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
    parser.add_argument('-b','--benchmark', type=str, help='benchmark inference, 請輸入query')
    parser.add_argument('-i','--identity', type=str, help='benchmark identity: customer or distributor or empty str')
    args = parser.parse_args()
    
    # init working context and agent object
    working_context = ""
    segment = "===================================================================="
    
    # init db and embed func
    pg_vector = DatabaseProcess.PGVector(DatabaseProcess.pg_setting)
    az_embed = EmbeddingFunction.AzureOpenAIEmbeddings()
    
    
    if args.js:
        '''**
        * js object demo
        * 1. convert text to embedding
        * 2. 組合並獲取 Working Context 
        *'''
        # query = "How to use mouse event in JS Object?"
        query = args.js
        if query.strip() == "":
            print("query is empty")
            exit()
        # conver query into embedding
        time_period_js_start_time = time.time()
        query_embedding = az_embed.get_embedding(query)
        # vector search
        results = pg_vector.query_jssdk_nearest(vec=query_embedding, top_k=10)
        time_period_js_end_time = time.time()
        # working context for LLM later
        working_context = "\n".join([segment + "\n" + res['chunk_context'] for res in results])
        print(working_context)
        print(f"\njs vector search time: {time_period_js_end_time - time_period_js_start_time} sec")
    
    if args.spec:
        '''**
        * spec object demo
        * 1. convert text to embedding
        * 2. 組合並獲取 Working Context
        *'''
        query = args.spec
        if query.strip() == "":
            print("query is empty")
            exit()
        # conver query into embedding
        time_period_spec_start_time = time.time()
        query_embedding = az_embed.get_embedding(query)
        # vector search
        results = pg_vector.query_spec_nearest(vec=query_embedding, top_k=10)
        time_period_spec_end_time = time.time()
        # working context for LLM later
        working_context = "\n".join([segment + "\n" + "HMI model: " + res['model'] + "\n"+ res['chunk_context'] for res in results])
        print(working_context)
        print(f"\nspec vector search time: {time_period_spec_end_time - time_period_spec_start_time} sec")
        
    
    if args.manual:
        '''**
        * manual object demo
        * 1. convert text to embedding
        * 2. 組合並獲取 Working Context
        *'''
        query = args.manual
        if query.strip() == "":
            print("query is empty")
            exit()
        # conver query into embedding
        time_period_manual_start_time = time.time()
        query_embedding = az_embed.get_embedding(query)
        # vector search
        results = pg_vector.query_manual_nearest(vec=query_embedding, top_k=10)
        time_period_manual_end_time = time.time()
        # working context for LLM later
        working_context = "\n".join([segment + "\n" + "Source: " + res['source'] + "\n"+ "Document Content: \n" + res['chunk_context'] for res in results])
        print(working_context)
        print(f"\nmanual vector search time: {time_period_manual_end_time - time_period_manual_start_time} sec")
    
    
    if args.benchmark and args.identity:
        '''**
        * benchmark object demo
        * 1. convert text to embedding
        * 2. 組合並獲取 Working Context
        *'''
        query = args.benchmark
        if query.strip() == "":
            print("query is empty")
            exit()
        
        identity = args.identity
        if identity.strip() not in ["customer","distributor"]:
            print("identity is not one of customer or distributor, use customer as default")
            identity = "customer"
            
        # conver query into embedding
        time_period_benchmark_start_time = time.time()
        query_embedding = az_embed.get_embedding(query)
        # vector search
        results = pg_vector.query_benchmark_nearest_by_identity(vec=query_embedding, 
                                                                identity=identity, 
                                                                top_k=10)
        time_period_benchmark_end_time = time.time()
        # working context for LLM later
        working_context = "\n".join([segment + "\n" + res['chunk_context'] for res in results])
        print(working_context)
        print(f"\nbenchmark vector search time: {time_period_benchmark_end_time - time_period_benchmark_start_time} sec")