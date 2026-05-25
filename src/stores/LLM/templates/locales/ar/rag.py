from string import Template

""" RAG PROMPTS """

system_prompt = "\n".join([
    "أنت مساعد ذكي ومفيد للإجابة على الأسئلة بناءً على المستندات المسترجعة التالية:",
    "يرجى استخدام المستندات المسترجعة التالية فقط للإجابة على السؤال. إذا لم تعرف الإجابة، فقل إنك لا تعرف. لا تستخدم أي معلومات غير موجودة في المستندات المسترجعة.",
])

""" Document template for RAG """
retrieved_doc_prompt = Template("\n".join([
    "المستند ${doc_num}:",
    "${chunk_text}",
]))

""" Footer prompt for RAG """
footer_template = "\n".join([
    "بناءً على المستندات المسترجعة أعلاه، يرجى الإجابة على السؤال التالي:",
    "الإجابة:",
])