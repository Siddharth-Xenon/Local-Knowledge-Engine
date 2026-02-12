from neo4j import GraphDatabase
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.retrievers import Text2CypherRetriever
from neo4j_graphrag.llm import OpenAILLM
from app.inference.llm_adapter import Node1LLM


from app.config import settings


def main():
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    driver.verify_connectivity()

    try:
        # Create Cypher LLM
        t2c_llm = OpenAILLM(model_name="gpt-5.2", api_key=settings.openai_api_key)
        # t2c_llm = Node1LLM()
        # tag::examples[]
        # Cypher examples as input/query pairs
        examples = [
            # "USER INPUT: How many users are flagged?' QUERY:MATCH (c:Customer)-[:OWNS_ACCOUNT]->(a:Account)<-[:EXECUTED_ON]-(t:Transaction)-[:RESULTS_IN]->(d:Decision) WHERE d.decision_type = 'flagged' ",
            # """USER INPUT:most voilataed policy and specific rule? QUERY: MATCH (p:Policy)-[:CONTAINS_RULE]->(r:Rule) RETURN p.policy_id, r.rule_id, COUNT(r) AS violations ORDER BY violations DESC LIMIT 1 """,
        ]
        # end::examples[]

        # tag::retriever[]
        # Build the retriever
        retriever = Text2CypherRetriever(
            driver=driver,
            llm=t2c_llm,
            examples=examples,
        )
        # end::retriever[]

        llm = Node1LLM()
        rag = GraphRAG(retriever=retriever, llm=llm)

        query_text = "Which user is the biggest fraudster in terms of amount?"
        response = rag.search(query_text=query_text, return_context=True)
        print("QUERY: ", query_text)
        print(response.answer)
        print("\n\nCYPHER :", response.retriever_result.metadata["cypher"])
        print("CONTEXT:", response.retriever_result.items)

        query_text = "Average transaction amount"
        response = rag.search(query_text=query_text, return_context=True)
        print("QUERY: ", query_text)
        print(response.answer)
        print("\n\nCYPHER :", response.retriever_result.metadata["cypher"])
        print("CONTEXT:", response.retriever_result.items)

        query_text = "most voilataed policy and specific rule"
        response = rag.search(query_text=query_text, return_context=True)
        print("QUERY: ", query_text)

        print(response.answer)
        print("\n\nCYPHER :", response.retriever_result.metadata["cypher"])
        print("CONTEXT:", response.retriever_result.items)

    finally:
        driver.close()


if __name__ == "__main__":
    main()
