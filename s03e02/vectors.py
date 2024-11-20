import os
import glob
from common.report_helpers import send_report
from common.ai_helpers import create_jina_embedding
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance


qdrant_client = QdrantClient(
    url=os.getenv('QDRANT_URL'), 
    api_key=os.getenv('QDRANT_API_KEY')
)

def read_file_content(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def index_reports():
    collection_name = "weapons_reports"
    
    reports_path = os.path.join('weapons', '*.txt')
    points = []
    
    for report_file in glob.glob(reports_path):
        report_name = os.path.basename(report_file)
        report_date = report_name.split('.')[0]  # Extract date from filename
        content = read_file_content(report_file)
        
        print(f"Indexing report: {report_name} with date: {report_date}")
        
        # Create Jina embedding for the report content
        embedding = create_jina_embedding(content)
        print(f"Embedding length: {len(embedding)}")
        
        points.append({
            'vector': embedding,
            'metadata': {
                'text': content,
                'date': report_date,
                'filename': report_name
            }
        })
    
    print(f"Initializing collection with {len(points)} reports.")
    
    # Check if collection exists and delete it if it does
    if qdrant_client.collection_exists(collection_name):
        qdrant_client.delete_collection(collection_name)
    
    # Create new collection
    qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=1024,
            distance=Distance.COSINE
        )
    )
    
    qdrant_client.upsert(
        collection_name=collection_name, 
        points=[
            PointStruct(
                id=i,
                vector=point['vector'],
                payload=point['metadata']
            )
            for i, point in enumerate(points)
        ]
    )

def query_reports():
    query = "W raporcie, z którego dnia znajduje się wzmianka o kradzieży prototypu broni?"
    collection_name = "weapons_reports"
    
    print(f"Querying collection: {collection_name} with query: '{query}'")
    search_results = qdrant_client.search(
        collection_name=collection_name,
        query_vector=create_jina_embedding(query),
        limit=1
    )
    
    if search_results:
        result = search_results[0]
        report_date = result.payload.get('date')
        print(f"Found report with date: {report_date}")
        return report_date
    print("No relevant report found.")
    return None

def main():
    try:
        print("Starting indexing of reports.")
        index_reports()
        print("Indexing complete. Starting query.")
        report_date = query_reports()
        
        if report_date:
            formatted_date = report_date.replace('_', '-')
            response = send_report(formatted_date, "wektory")
            print(f"Report sent successfully: {response}")
        else:
            print("No relevant report found.")
    except Exception as e:
        print(f"Error processing reports: {str(e)}")
        raise

if __name__ == "__main__":
    main() 
