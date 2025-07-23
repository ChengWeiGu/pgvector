# -*- coding: utf-8 -*-
import os
import configparser
import openai
from openai import AzureOpenAI, OpenAIError


config=configparser.ConfigParser()
config.read("Config.ini")


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