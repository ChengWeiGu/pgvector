# -*- coding: utf-8 -*-
import os
import time
import argparse
from tqdm import tqdm
import DatabaseProcess
import EmbeddingFunction
from os import listdir, walk
from os.path import basename, join, exists, dirname
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader


az_embed = EmbeddingFunction.AzureOpenAIEmbeddings()
pg_vector = DatabaseProcess.PGVector(DatabaseProcess.pg_setting)


class DEM:
    def __init__(self, directory, table_name):
        # 定義類別資訊
        self.info = {
            'path' : directory + "/DEM",
            'class_name': "DEM",
            'class_desc':"Example Projects for Product Users/Customers"
        }
        # pg table name
        self.table_name = table_name
        # 允許可以處理的語言
        self.lang_list = ['en','tw','eng','cht']
        # 允許可以處理的附檔名
        self.extension_list = ['pdf','docx']
        self.get_end_list() # _en.pdf, _tw.docx...
    
    # 將語言+副檔名進行排列組合
    def get_end_list(self) -> None:
        self.end_list = []
        for lang in self.lang_list:
            for ext in self.extension_list:
                self.end_list.append("_"+lang+"."+ext)
    
    # 依副檔名判斷檔案是否可以處理            
    def isin_extension_list(self, file) -> tuple[bool,str]:
        isin_extension = False
        extension = ''
        for ext in self.extension_list:
            if ext in file:
                isin_extension = True
                extension = ext
        return isin_extension, extension
    
    # 依檔名排列組合判斷檔案是否可以被處理
    def isin_end_list(self,file) -> tuple[bool,str]:
        isin_end = False
        end_text = ''
        for end in self.end_list:
            if end in file:
                isin_end = True
                end_text = end
        return isin_end, end_text
    
    '''**掃描檔案+建立metadaat
    * 1. 排除不正確的檔名+副檔名, 優先處理PDF格式
    * 2. 將可以處理的檔案一一建立metadata
    * 3. 使用 RecursiveCharacterTextSplitter 切割文檔
    * 4. 轉為Embedding
    * 5. 插入PostgreSQL
    * @params: None
    * @return: None
    *'''
    def scan_folder_and_create_embed2pg(self):
        filenames = [] # 紀錄可以處理的檔案路徑+檔名
        prefix_filenames = []
        extension_list = []
        for root,dirs,files in walk(self.info['path']):
            for file in files:
                filename = join(root,file)
                # filter1: 副檔名要正確
                isin_end, end_text = self.isin_end_list(file=file)
                if isin_end:
                    # filter2: do not consider duplicate prefix filename
                    isin_extension, extension = self.isin_extension_list(file=file)
                    prefix_filename = filename.replace(extension,"") # XX_en.pdf -> XX_en, XX_tw.docx -> XX_tw
                    if prefix_filename not in prefix_filenames:
                        # 優先處理PDF格式，避免重複處理
                        pdf_filename = prefix_filename + "pdf"
                        # priority pdf > docx
                        if exists(pdf_filename):
                            filenames.append(pdf_filename)
                            extension_list.append('pdf')
                        else:
                            filenames.append(filename)
                            extension_list.append(extension)
                        prefix_filenames.append(prefix_filename)
        
        # text splitter
        text_splitter_recur = RecursiveCharacterTextSplitter(
            chunk_size = 1000,
            chunk_overlap = 300,
            length_function = len,
            is_separator_regex=False
        )
        print("start scaning....")
        total_chunk_cnt = 0
        fail_list = []
        for i, filename in tqdm(enumerate(filenames),
                                desc="Process Manual Documents ",
                                total=len(filenames),
                                unit="pcs"):
            try:
                # 建立metadata
                metadata = {
                    'source':basename(filename),
                    'filename':filename,
                    'parent_folder':basename(dirname(filename)),
                    'extension':extension_list[i],
                    'class_name':self.info['class_name'],
                    'class_desc':self.info['class_desc']
                    }
                # 處理metadata格式以便插入pg, 外掛 chunk_context and embedding
                data_keys = list(metadata.keys()) + ["chunk_context","embedding"]
                col_names = ", ".join(data_keys)
                # 不同副檔 -> 不同處理方式
                content_texts = ""
                if extension_list[i].lower() == 'docx':
                    loader = Docx2txtLoader(filename)
                    data = loader.load() # 只有一個document包含全部內容
                    content_texts = data[0].page_content #取出內容
                else: # pdf
                    loader = PyPDFLoader(filename)
                    pages = loader.load_and_split() # page by page data
                    for page in pages:
                        content_texts += (page.page_content + " ")
                        
                # split and add metadata
                for chunk in text_splitter_recur.split_text(content_texts):
                    # 加入 chunk_context
                    data_values = list(metadata.values())
                    data_values.append(chunk)
                    # 轉換Embedding, 失敗試三次
                    for _ in range(3):
                        chunk_embedding = az_embed.get_embedding(chunk)
                        if chunk_embedding is not None:
                            data_values.append(chunk_embedding)
                            # 存入pg
                            data_values = [tuple(data_values)]
                            pg_vector.upsert_data(self.table_name, 
                                                  col_names, 
                                                  data_values)
                            total_chunk_cnt += 1
                            break
                        else:
                            time.sleep(10)    
                    
            except Exception as e:
                fail_list.append((filename, str(e)))
            
        print("total len of chunks: ",total_chunk_cnt)
        print("fail list:\n",fail_list)

    
'''**
* 1. 繼承DEM
* 2. 改寫info
*'''          
class FAQ(DEM):
    def __init__(self, directory, table_name):
        self.info = {
            'path' : directory + "/FAQ",
            'class_name': "FAQ",
            'class_desc':"Frequently Asked Questions for Product Users/Customers"
        }
        self.table_name = table_name
        self.lang_list = ['en','tw','eng','cht','ENG']
        self.extension_list = ['pdf','docx']
        self.get_end_list() # _en.pdf, _tw.docx...


'''**
* 1. 繼承DEM
* 2. 改寫info, scan_folder_and_create_embed2pg
* 3. scan_folder_and_create_embed2pg中改寫可以處理的檔名
*'''  
class EBP(DEM):
    def __init__(self, directory, table_name):
        self.info = {
            'path' : directory + "/EBP",
            'class_name': "EBP",
            'class_desc':"This is EBPro User-Guide Manual for All Chapters"
        }
        self.table_name = table_name
    
    def scan_folder_and_create_embed2pg(self):
        # 規定只能處理的檔案+副檔名
        files = ['EasyBuilder-Pro-V61001-UserManual-cht.pdf','EasyBuilder-Pro-V61001-UserManual-eng.pdf']
        filenames = [(self.info['path'] + '/' + f) for f in files]
        extension_list = ['pdf','pdf']
        
        # text splitter
        text_splitter_recur = RecursiveCharacterTextSplitter(
            chunk_size = 1000,
            chunk_overlap = 300,
            length_function = len,
            is_separator_regex=False
        )
        print("start scaning....")
        total_chunk_cnt = 0
        fail_list = []
        for i, filename in tqdm(enumerate(filenames),
                                desc="Process Manual Documents ",
                                total=len(filenames),
                                unit="pcs"):
            try:
                # 建立metadata
                metadata = {'source':basename(filename),
                            'filename':filename,
                            'parent_folder':basename(dirname(filename)),
                            'extension':extension_list[i],
                            'class_name':self.info['class_name'],
                            'class_desc':self.info['class_desc']}
                # 處理metadata格式以便插入pg, 外掛 chunk_context and embedding
                data_keys = list(metadata.keys()) + ["chunk_context","embedding"]
                col_names = ", ".join(data_keys)
                # 不同副檔 -> 不同處理方式
                content_texts = ""
                if extension_list[i] == 'docx':
                    loader = Docx2txtLoader(filename)
                    data = loader.load() # 只有一個document包含全部內容
                    content_texts = data[0].page_content #取出內容
                else: # pdf
                    loader = PyPDFLoader(filename)
                    pages = loader.load_and_split() # page by page data
                    for page in pages:
                        content_texts += (page.page_content + " ")
                # split and add metadata
                for chunk in text_splitter_recur.split_text(content_texts):
                    # 加入 chunk_context
                    data_values = list(metadata.values())
                    data_values.append(chunk)
                    # 轉換Embedding, 失敗試三次
                    for _ in range(3):
                        chunk_embedding = az_embed.get_embedding(chunk)
                        if chunk_embedding is not None:
                            data_values.append(chunk_embedding)
                            # 存入pg
                            data_values = [tuple(data_values)]
                            pg_vector.upsert_data(self.table_name, 
                                                  col_names, 
                                                  data_values)
                            total_chunk_cnt += 1
                            break
                        else:
                            time.sleep(10)  
            except Exception as e:
                fail_list.append((filename, str(e)))
            
        print("total len of chunks: ",total_chunk_cnt)
        print("fail list:\n",fail_list) 
        


'''**
* 1. 繼承DEM
* 2. 改寫info
*'''      
class UM0(DEM):
    def __init__(self, directory, table_name):
        self.info = {
            'path' : directory + "/UM0",
            'class_name': "UM0",
            'class_desc':"Operation Manual for All Products"
        }
        self.table_name = table_name
        self.lang_list = ['en','tw','eng','cht']
        self.extension_list = ['pdf','docx']
        self.get_end_list() # _en.pdf, _tw.docx...


'''**
* 1. 繼承DEM
* 2. 改寫info, get_end_list
* 3. get_end_list當中檔案名稱不含 "_" (特殊)
*'''   
class FBA(DEM):
    def __init__(self, directory, table_name):
        self.info = {
            'path' : directory + "/FBA",
            'class_name': "FBA",
            'class_desc':"Official Video Explanation for Weintek"
        }
        self.table_name = table_name
        self.lang_list = [''] # 不卡控
        # self.extension_list = ['pdf','docx']
        self.extension_list = ['DOCX','PDF']
        self.get_end_list() # .pdf, .docx...
        
    def get_end_list(self):
        self.end_list = []
        for lang in self.lang_list:
            for ext in self.extension_list:
                self.end_list.append(lang+"."+ext)



def main():
    parser = argparse.ArgumentParser(description='FAE Manual Document')
    parser.add_argument('-t','--table_name', type=str, default="manual", help='創建Postgres Table名稱存入manual')
    parser.add_argument('-s', '--src', type=str, default="./SVN_manual", help='User Guide Manual 資料夾位置')
    args = parser.parse_args()
    
    table_name = args.table_name
    if table_name.strip() == "":
        print("table_name is empty")
        return
    
    directory = args.src
    if directory.strip() == "":
        print("directory is empty")
        return
    
    
    print(f"Create table '{table_name}' if not exists....")
    ret_json = pg_vector.create_manual_table(table_name=table_name)
    if ret_json["status"] == "fail":
        print(ret_json["error_reason"])
        return
    
    print("start creating manual documents....")
    
    # for dem scanner
    print("\nstart dem scanning....")
    dem_scanner = DEM(args.src, args.table_name)
    dem_scanner.scan_folder_and_create_embed2pg()
    print("dem done\n")
    
    
    # for faq scanner
    print("\nstart faq scanning....")
    faq_scanner = FAQ(args.src, args.table_name)
    faq_scanner.scan_folder_and_create_embed2pg()
    print("faq done\n")
    
    
    # for ebp scanner
    print("\nstart ebp scanning....")
    ebp_scanner = EBP(args.src, args.table_name)
    ebp_scanner.scan_folder_and_create_embed2pg()
    print("ebp done\n")
    
    
    # for um0 scanner
    print("\nstart um0 scanning....")
    um0_scanner = UM0(args.src, args.table_name)
    um0_scanner.scan_folder_and_create_embed2pg()
    print("um0 done\n")
    
    
    # for FBA scanner
    print("\nstart fba scanning....")
    fba_scanner = FBA(args.src, args.table_name)
    fba_scanner.scan_folder_and_create_embed2pg()
    print("fba done\n")
    
    print("\nall done")        
    
        
if __name__ == "__main__":
    main()
    