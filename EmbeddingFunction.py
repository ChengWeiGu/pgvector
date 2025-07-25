# -*- coding: utf-8 -*-
import os
import tiktoken
import configparser
import openai
from openai import AzureOpenAI, OpenAIError


config=configparser.ConfigParser()
config.read("Config.ini")


'''Token Calculator for LLM
* @params: text - string of text, model_name - model name
* @return: number of tokens
**'''
def num_tokens_from_string_llm(text: str, model_name: str = "gpt-4o") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(model_name)
    tokens = encoding.encode(text)
    num_tokens = len(tokens)
    return num_tokens


'''Token Calculator for Embedding
* @params: text - string of text, encoding_name - model encoding name
* @return: number of tokens
* cl100k_base for  hird-generation embedding models like text-embedding-3-small
**'''
def num_tokens_from_string_embed(string: str, encoding_name: str="cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens



## default az setting
endpoint = config['AOAI_DEFAULT']['endpoint']
api_key1 = config['AOAI_DEFAULT']['api_key1']
api_key2 = config['AOAI_DEFAULT']['api_key2']
region = config['AOAI_DEFAULT']['region']
api_version = config['AOAI_DEFAULT']['api_version']
chat_model = config['AOAI_DEFAULT']['chat_model']
embed_model = config['AOAI_DEFAULT']['embed_model']
embed_dim = config['AOAI_DEFAULT']['embed_dim']
api_type = config['AOAI_DEFAULT']['api_type']



class AzureOpenAIEmbeddings:
    
    def __init__(self, model=embed_model, dimension=embed_dim):
        self.model = model
        self.dimension = dimension
        self.client = AzureOpenAI(
            api_key=api_key1,
            api_version=api_version,
            azure_endpoint=endpoint
        )

    def get_embedding(self, text):
        try:
            response = self.client.embeddings.create(input=text, model=self.model)
            embedding = response.data[0].embedding
            return embedding
        except OpenAIError as e:
            print(f"Error getting embedding: {e}")
            return None

    
    

if __name__ == "__main__":
    az_embed = AzureOpenAIEmbeddings()
    
    # aoai method
    embedding = az_embed.get_embedding("Hello, world!")
    if embedding is not None:
        print(f"Embedding: {embedding}\n=>Total length of embedding: {len(embedding)}")
    else:
        print("Failed to get embedding.")
        
    
    # num_tokens = num_tokens_from_string_llm("這是一段測試文字，用於計算 LLM token 的數量。")
    # print(f"Number of tokens: {num_tokens}")
    
    # num_tokens = num_tokens_from_string_embed("這是一段測試文字，用於計算 embedding token 的數量。")
    # print(f"Number of tokens: {num_tokens}")