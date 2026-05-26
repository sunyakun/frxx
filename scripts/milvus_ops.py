#!/usr/bin/env python3
"""
统一的 RAG 数据处理脚本
通过命令行参数切换不同功能：
- create-collection: 创建 Milvus 集合
- generate-parquet: 生成 Parquet 文件
- import-data: 导入数据到 Milvus
- show-collection: 显示集合信息
"""

import argparse
import asyncio
import json
import math
import time
from glob import glob
from typing import Dict, List

import numpy as np
from pymilvus import DataType, MilvusException
from pymilvus.bulk_writer import (
    BulkFileType,
    LocalBulkWriter,
    bulk_import,
    get_import_progress,
)
from pymilvus.bulk_writer.constants import MB
from pymilvus.exceptions import ErrorCode
from tqdm import tqdm
from unstructured.chunking.title import chunk_by_title
from unstructured.documents.elements import NarrativeText, Title

from app.config import Settings, get_settings
from app.services.embedding import encode_text
from app.utils.clients import get_milvus_client, milvus_collection_schema


def create_collection():
    """创建 Milvus 集合"""
    settings: Settings = get_settings()

    try:
        get_milvus_client().load_collection(
            collection_name=settings.milvus_collection_name
        )
    except MilvusException as err:
        if err.code != ErrorCode.COLLECTION_NOT_FOUND:
            raise
    else:
        print(
            f"Collection {settings.milvus_collection_name} already exist, going to delete it."
        )
        get_milvus_client().drop_collection(settings.milvus_collection_name)

    get_milvus_client().create_collection(
        collection_name=settings.milvus_collection_name,
        schema=milvus_collection_schema,
        using=settings.milvus_db_name,
    )

    index_params = get_milvus_client().prepare_index_params()

    index_params.add_index(
        field_name="dense_embed",
        metric_type="IP",
        index_type="FLAT",
    )

    get_milvus_client().create_index(
        collection_name=settings.milvus_collection_name, index_params=index_params
    )

    get_milvus_client().load_collection(collection_name=settings.milvus_collection_name)

    print(f"Create collection {settings.milvus_collection_name} success.")


def generate_parquet():
    """生成 Parquet 文件"""
    batch_size = 32
    num_rows_commit = 1000

    ################### partition and chunk ###################
    eles = []
    with open("dist/《凡人修仙传》（校对版全本+番外）作者：忘语.txt") as fp:
        for line in fp.readlines():
            if line.startswith("第"):
                ele = Title(line.strip())
            else:
                ele = NarrativeText(line.strip())
            eles.append(ele)

    chunks = chunk_by_title(
        eles,
        max_characters=1000,
        overlap=50,
        include_orig_elements=True,
    )

    current_title = None
    records = []
    for chunk in chunks:
        for ele in chunk.metadata.orig_elements:
            if isinstance(ele, Title):
                current_title = ele
                break
        assert current_title is not None
        records.append(
            {"text": chunk.text, "metadata": json.dumps({"title": current_title.text})}
        )

    ################### prepare source data ###################
    writer = LocalBulkWriter(
        schema=milvus_collection_schema,
        local_path="./dist/volumes/milvus/data",
        chunk_size=512 * MB,
        file_type=BulkFileType.PARQUET,
    )
    for ary in tqdm(np.array_split(records, math.ceil(len(chunks) / batch_size))):
        sub_records: List[Dict] = ary.tolist()
        encoded_result = asyncio.run(encode_text([r["text"] for r in sub_records]))
        for record, dense in zip(sub_records, encoded_result["dense"]):
            record["dense_embed"] = dense
        for record in sub_records:
            writer.append_row(record)
        if writer.buffer_row_count % num_rows_commit == 0:
            writer.commit()
    writer.commit()
    print(f"Finish write data to files: {writer.batch_files}")


def import_data():
    """导入数据到 Milvus"""
    settings: Settings = get_settings()

    resp = bulk_import(
        url=settings.milvus_uri,
        collection_name=settings.milvus_collection_name,
        files=[
            [p.replace("./dist/volumes/", "/var/lib/")]
            for p in glob("./dist/volumes/milvus/data/*/*.parquet")
        ],
    )

    job_id = resp.json()["data"]["jobId"]

    last_progress = -1
    while True:
        resp = get_import_progress(
            url=settings.milvus_uri,
            job_id=job_id,
        )
        progress = resp.json()["data"]["progress"]
        if progress != last_progress:
            print(f"Progress: {progress}%")
            last_progress = progress
        if progress == 100:
            break
        time.sleep(1)
    print("Finish import data to milvus")


def show_collection():
    """显示集合信息"""
    settings: Settings = get_settings()

    collection_info = get_milvus_client().describe_collection(
        settings.milvus_collection_name
    )

    print(f"Collection Name: {collection_info['collection_name']}")
    print(f"Collection ID: {collection_info['collection_id']}")
    print(f"Auto ID: {collection_info['auto_id']}")
    print(f"Enable Dynamic Field: {collection_info['enable_dynamic_field']}")
    print()
    print("Fields:")
    for field in collection_info["fields"]:
        print(f"  - {field['name']}: {DataType(field['type']).name}", end="")
        if field.get("is_primary"):
            print(" (PRIMARY KEY)", end="")
        if field.get("nullable"):
            print(" (NULLABLE)", end="")
        if field.get("auto_id"):
            print(" (AUTO_ID)", end="")
        if field.get("max_length"):
            print(f" (max_length={field['max_length']})", end="")
        if field.get("dim"):
            print(f" (dim={field['dim']})", end="")
        print()

    print()
    print("Stats:")
    stats = get_milvus_client().get_collection_stats(settings.milvus_collection_name)
    print(f"  Row Count: {stats['row_count']}")


def main():
    parser = argparse.ArgumentParser(description="RAG 数据处理工具")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create-collection 子命令
    create_parser = subparsers.add_parser("create-collection", help="创建 Milvus 集合")

    # generate-parquet 子命令
    parquet_parser = subparsers.add_parser("generate-parquet", help="生成 Parquet 文件")

    # import-data 子命令
    import_parser = subparsers.add_parser("import-data", help="导入数据到 Milvus")

    # show-collection 子命令
    show_parser = subparsers.add_parser("show-collection", help="显示集合信息")

    args = parser.parse_args()

    if args.command == "create-collection":
        create_collection()
    elif args.command == "generate-parquet":
        generate_parquet()
    elif args.command == "import-data":
        import_data()
    elif args.command == "show-collection":
        show_collection()


if __name__ == "__main__":
    main()
