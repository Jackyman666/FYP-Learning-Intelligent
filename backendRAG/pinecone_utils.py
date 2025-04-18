import json
import time
import openai
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
import os

# ✅ Load environment variables (best practice for security)
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
AZURE_OPENAI_API_KEY = os.getenv("OPENAI_EMBEDDING_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("OPENAI_EMBEDDING_ENDPOINT")
AZURE_OPENAI_VERSION = "2023-05-15"  # Update if needed


class PineconeUtils:
    def __init__(self, index_name="trail", namespace="2012"):
        """Initialize Pinecone and Azure OpenAI configurations."""
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        self.index_name = index_name
        self.namespace = namespace
        
        self.pc = Pinecone(api_key=PINECONE_API_KEY)

        
        # ✅ Wait for the index to be ready
        while not self.pc.describe_index(self.index_name).status["ready"]:
            time.sleep(1)

        self.index = self.pc.Index(self.index_name)

        # ✅ Set up Azure OpenAI API
        openai.api_type = "azure"
        openai.base_url = AZURE_OPENAI_ENDPOINT
        openai.api_version = AZURE_OPENAI_VERSION
        openai.api_key = AZURE_OPENAI_API_KEY

    def delete_record(self, namespace=None, record_id=None, delete_all=False):
        """Delete a single record or all records in a namespace."""
        namespace = namespace or self.namespace
        if delete_all:
            self.index.delete(namespace=namespace, delete_all=True)
        else:
            self.index.delete(namespace=namespace, ids=record_id)

    def get_embeddings(self, text_list):
        """Generate embeddings for a list of texts using Azure OpenAI."""
        response = openai.embeddings.create(
            model="text-embedding-3-large",
            input=text_list
        )
        return [e.embedding for e in response.data]  # Extract 3072-dim vectors

    def insert_reading_material(self, json_data):
        """Insert reading materials into Pinecone with metadata."""
        title = json_data.get("title", "")
        subtitle = json_data.get("subtitle", "")
        text_id = json_data.get("text_id", "")

        paragraphs = []
        paragraph_ids = []
        metadata_list = []

        para_count = 0
        for section_data in json_data.get("content", []):
            section = section_data.get("section", "")

            for paragraph in section_data.get("paragraphs", []):
                para_count += 1
                paragraph_id = f"PartA-Text1-P{para_count}"
                paragraphs.append(paragraph)
                paragraph_ids.append(paragraph_id)
                metadata_list.append({
                    "text_id": text_id,
                    "title": title,
                    "subtitle": subtitle,
                    "section": section,
                    "text": paragraph 
                })
        # for i in range(len(paragraphs)):
        # print('-',paragraph_ids[i],'#',paragraphs[i],metadata_list[i]["section"])
        # print(len(paragraphs))

        # 🔥 Generate embeddings
        vectors = self.get_embeddings(paragraphs)

        # 🔹 Batch upsert into Pinecone
        upsert_data = [
            {"id": pid, "values": vec, "metadata": meta}
            for pid, vec, meta in zip(paragraph_ids, vectors, metadata_list)
        ]
        
        self.index.upsert(vectors=upsert_data, namespace=self.namespace)
        print(f"✅ Inserted {len(vectors)} paragraphs into Pinecone!")

    def query_pinecone(self, namespace, query_text, top_k):
        """Query Pinecone with a search phrase and return the top results."""
        query_vector = self.get_embeddings(query_text)  # Convert query to embedding

        results = self.index.query(
            namespace=namespace,
            vector=query_vector,
            top_k=top_k,
            include_values=False,
            include_metadata=True
        )

        return results
    
    def query_all(self, namespace):
        metadata_filter = {"text": {"$ne": ""}}
        
        results = self.index.query(
            namespace=namespace,
            vector=[0] * 3072,
            top_k=500,
            include_values=False,
            filter=metadata_filter,
            include_metadata=True
        )
        return results

# 🔥 Example Usage
if __name__ == "__main__":
    pinecone_util = PineconeUtils()

    # Insert reading materials
    with open("learning-intelligent/backendRAG/PastPaper/2012/PartA/reading_materials.json", "r", encoding="utf-8") as f:
        reading_data = json.load(f)

    # pinecone_util.insert_reading_material(reading_data)

    # Query example
    query = "Where is Polar Cafe?"
    # results = pinecone_util.query_pinecone(2012,query,3)
    results = pinecone_util.query_all("2012")
    print("🔹 Query Results:", results)