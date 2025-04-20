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
    def __init__(self, index_name="trail", namespace="PastPaper"):
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

    def deleteRecord(self, namespace=None, record_id=None, delete_all=False):
        """Delete a single record or all records in a namespace."""
        namespace = namespace or self.namespace
        if delete_all:
            self.index.delete(namespace=namespace, delete_all=True)
        else:
            self.index.delete(namespace=namespace, ids=record_id)

    def getEmbeddings(self, text_list):
        """Generate embeddings for a list of texts using Azure OpenAI."""
        response = openai.embeddings.create(
            model="text-embedding-3-large",
            input=text_list
        )
        return [e.embedding for e in response.data]  # Extract 3072-dim vectors

    def insertReadingMaterials(self, year, part, text_id):
        """Insert a reading material from a .txt file as a single document-level vector."""
        
        # 📄 Read the full text content from the file
        with open(f"PastPaper/{year}/Part{part}/text{text_id}.txt", "r", encoding="utf-8") as f:
            full_text = f.read().strip()

        # 🧠 Generate embedding from the full text
        embedding = self.getEmbeddings([full_text])[0]

        # 🆔 Create a unique vector ID
        vector_id = f"{year}-{part}-text{text_id}"

        # 📎 Minimal metadata
        metadata = {
            "year": str(year),
            "part": part,
            "text_id": str(text_id),
            "text": full_text
        }

        # 🚀 Upsert to Pinecone
        self.index.upsert(
            vectors=[{
                "id": vector_id,
                "values": embedding,
                "metadata": metadata
            }],
            namespace=self.namespace
        )

        print(f"✅ Inserted text file: {vector_id} into Pinecone!")

    def queryPinecone(self, namespace, query_text, top_k):
        """Query Pinecone with a search phrase and return the top results."""
        query_vector = self.getEmbeddings(query_text)  # Convert query to embedding

        results = self.index.query(
            namespace = namespace,
            vector=query_vector,
            top_k=top_k,
            include_values=False,
            include_metadata=True
        )

        return results
    
    def queryAll(self, namespace):
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
    # pinecone_util.insertReadingMaterials(2013, "B2", 4)

    # pinecone_util.insert_reading_material(reading_data)

    # Query example
    query = "Give me an article thats related to Chinese History"
    results = pinecone_util.queryPinecone("PastPaper",query,3)
    # results = pinecone_util.queryAll("PastPaper")
    print("🔹 Query Results:", results)