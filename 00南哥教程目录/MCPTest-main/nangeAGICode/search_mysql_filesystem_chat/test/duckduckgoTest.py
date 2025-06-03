# pip install duckduckgo_search==6.4.2


from duckduckgo_search import DDGS

search_query = 'python programming'

results = DDGS().text(
    keywords = search_query,
    region = "cn-zh",
    safesearch = 'off',
    timelimit = '7d',
    max_results=5
)

# 拼接字符串
results = "\n".join(f"{item['title']} - {item['href']} - {item['body']}" for item in results)

print(results)


