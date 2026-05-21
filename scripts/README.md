# RAG 数据处理工具使用说明

## 统一脚本 `milvus_ops.py`

`scripts/milvus_ops.py` 是整合了所有 RAG 相关功能的统一脚本，通过命令行参数切换不同功能。

## 使用方法

### 1. 创建 Milvus 集合
```bash
python scripts/milvus_ops.py create-collection
```
功能：创建 Milvus 集合、添加索引并加载数据集。

### 2. 生成 Parquet 文件
```bash
python scripts/milvus_ops.py generate-parquet
```
功能：从《凡人修仙传》文本生成包含向量的 Parquet 文件。

### 3. 导入数据到 Milvus
```bash
python scripts/milvus_ops.py import-data
```
功能：将生成的 Parquet 文件导入到 Milvus 数据库。

### 4. 显示集合信息
```bash
python scripts/milvus_ops.py show-collection
```
功能：显示 Milvus 集合的详细信息和统计。

## 功能说明

### create-collection
- 删除已存在的集合（如果存在）
- 创建新的集合
- 配置稠密向量和稀疏向量的索引
- 加载集合到内存

### generate-parquet
- 读取《凡人修仙传》文本文件
- 按标题进行分块
- 生成稠密和稀疏嵌入向量
- 输出为 Parquet 格式文件

### import-data
- 将 Parquet 文件批量导入 Milvus
- 显示导入进度
- 等待导入完成

### show-collection
- 显示集合的基本信息
- 列出字段定义
- 显示数据统计信息

## 注意事项

1. 确保环境变量已经正确配置（MILVUS_URI 等）
2. 执行顺序建议：
   - 先执行 `create-collection`
   - 然后执行 `generate-parquet`
   - 最后执行 `import-data`
3. 每个步骤执行成功后再进行下一步
4. 可以随时使用 `show-collection` 查看集合状态