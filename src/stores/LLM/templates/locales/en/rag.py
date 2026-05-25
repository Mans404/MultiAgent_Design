from string import Template

""" RAG PROMPTS """

system_prompt = "\n".join([
    "You are a helpful assistant for answering questions based on the following retrieved documents:",
    "Please use only the following retrieved documents to answer the question. If you don't know the answer, say you don't know. Do not use any information that is not in the retrieved documents.",
])

""" Document template for RAG """
retrieved_doc_prompt = Template("\n".join([
    "Document ${doc_num}:",
    "${chunk_text}",
]))

""" Footer prompt for RAG """
footer_template = "\n".join([
    "Based on the above retrieved documents, please answer the following question:",
    "Answer:"
])