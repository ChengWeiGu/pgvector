# pgvector   
Here shows some simple steps to create local pg server and to use pgvector for vector search   

## Platform   
- Windows X64, Anaconda, Python3.11.11. Please install packages with   
  
  ```bash
  pip install -r requirements.txt
  ```
  
- PostgreSQL is built by docker-compose.yml on WSL, Ubuntu. Please follow the guidelines:   
  1. Make sure you have installed wsl on Windows
     
     ```bash
     wsl --install -d Ubuntu
     wsl -l -v
     wsl -d Ubuntu
     ```

  2. You have to open docker desktop and intergrate WSL:   
     
     ```markdown
     Settings → Resources ▸ WSL Integration check distro   
     ```

  3. Build project file for postgres   

     ```bash
     # build dir under Home
     cd ~
     mkdir ~/pgvector-demo && cd ~/pgvector-demo
     
     # build compose file
     nano docker-compose.yml
     ```

  4. Start container   

     ```bash
     docker compose up -d
     docker ps      # 應看到 pgvector-db 正在 LISTEN 5432
     ```

  5. Initializing pgvector with psql   

     ```bash
     # enter the container (pgvector-db), then connect to the db (retrieval_db) with the user (postgres)
     # next, you will enter the interface terminal that enable you to use psql CMD
     docker exec -it pgvector-db psql -U postgres -d retrieval_db
     
     # In psql
     CREATE EXTENSION IF NOT EXISTS vector;
     \dx   -- 應列出 vector 代表成功
     \q
     ```

## Data Scopes   
- Summary Tables
  | **Scope**  | **Description**                                                                                                                                       | **Source**                                                                                         |
  |-----------|-------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
  | **Data1** | The Weintek JSSDK (JavaScript Software Development Kit) is a toolkit provided by Weintek to enable advanced scripting capabilities in its HMI products using JavaScript. | [Weintek JSSDK](https://dl.weintek.com/public/Document/JS_Object_SDK/Current/)    |
  | **Data2** | Weintek provides datasheets for its HMI models including detailed specifications and features of each device.                                          | Internal SVN or [Official Website](https://www.weintek.com/globalw/)                               |
  | **Data3** | Weintek offer many kind of manuals for user about EBPro, trouble shooting, FAQs, demo projects, ...etc.                                               | Internal SVN or [Official Website](https://www.weintek.com/globalw/)                               |
  
- Folder structure from SVN
  
  1. Take **Data2** for an example, the schema of source is:   
      ```markdown
      SVN_datasheet/
      ├── Accessory 
      ├── cMT 
      ├── eMT600 
      ├── eMT3000
      ├── ...
      └── mTV
      ```
  
  2. Take **Data3** for an example, the schema of source is:   
      ```markdown
      SVN_manual/
      ├── EDM // Example Projects for Product Users/Customers
      ├── EBP // This is EBPro User-Guide Manual for All Chapters
      ├── FAQ // Frequently Asked Questions for Product Users/Customers
      ├── FBA // Official Video Explanation for Weintek
      └── UM0 // Operation Manual for All Products
      ``` 

## Preparation Work   
In `config.ini`, please properly set azure endpoint, api version, api key, ...etc. before running ETL.   
```markdown
endpoint=<your endpoint>
api_key1=<your api_key1>
api_key2=<your api_key2>
region=<e.g. eastus, westus,...>
api_version=2024-12-01-preview
chat_model=gpt-4o-2024-11-20
embed_model=text-embedding-3-large
embed_dim=3072
api_type=azure
```
  
## ETL Scripts    
Please run the following scripts to prepare vector table for each data scope   

  ```bash
  # JSSDK ETL: create a table named 'jssdk' and convert data from web crawler into embedding
  python run_jssdk.py -t jssdk

  # SPEC ETL: create a table named 'spec' and convert file into embedding from folder 'SVN_datasheet'
  python run_spec.py -t spec -s "./SVN_datasheet"

  # MANUAL ETL: create a table named 'manual' and convert file into embedding from folder 'SVN_manual'
  python run_manual.py -t manual -s "./SVN_manual"
  ```

## Inference   
To use each table for vector search, please run   
```bash
python run_inference.py <flag> <query>
```
Where `<flag>` is one of   

`-j`: vector search on jssdk scope   
`-s`: vector search on datasheets scope   
`-m`: vector search on manual scope   

and `<query>`, not empty, is any question you want to ask.   

Try the following examples:   

- JSSDK   
```markdown
// Example 1: jssdk
python run_inference.py -j "How to use mouse event for js object?"
```

- Spec   
```markdown
// Example 2: spec
python run_inference.py -s "please show me the spec of cMT2158X"
```

- Manual   
```markdown
// Example 3: manual
python run_inference.py -m "how to install ebpro on windows?"
```

