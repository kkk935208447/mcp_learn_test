from pprint import pprint


def main():
    print("Hello")


    # from openai import OpenAI
    # client = OpenAI(api_key="sk-O2YWhKoQd040E2703188T3BLBKFJ0ACC522f182247EaBeab", base_url="https://c-z0-api-01.hash070.com/v1")
    # prompt = """
    # Write a bash script that takes a matrix represented as a string with 
    # format '[1,2],[3,4],[5,6]' and prints the transpose in the same format.
    # """

    # response = client.responses.create(
    #     model="o4-mini",
    #     reasoning={"effort": "medium"},
    #     input=[
    #         {
    #             "role": "user", 
    #             "content": prompt
    #         }
    #     ]
    # )

    # print(response)



    # from openai import OpenAI
    # client = client = OpenAI(api_key="sk-O2YWhKoQd040E2703188T3BLBKFJ0ACC522f182247EaBeab", base_url="https://c-z0-api-01.hash070.com/v1")
    # prompt = """
    # 请说明一下9.6 与 10.1 那个数大？
    # """
    # response = client.chat.completions.create(
    #     model="o4-mini",
    #     reasoning_effort="medium",
    #     messages=[
    #         {
    #             "role": "user", 
    #             "content": prompt
    #         }
    #     ]
    # )
    # pprint(response.model_dump())



    from openai import OpenAI
    # 使用本地的 ollama 部署的模型，需要先启动
    # apikey 可以随便填
    client = client = OpenAI(api_key="none", base_url="http://127.0.0.1:11434/v1") 
    prompt = """
    请说明一下9.6、10.1与8.99 那个数大？
    """

    response = client.chat.completions.create(
        model="qwen3:8b",
        # 猜测：ollama 的模型没有作用
        # reasoning_effort="high",
        messages=[
            {
                "role": "user", 
                "content": prompt
            }
        ]
    )
    pprint(response.model_dump())


if __name__ == "__main__":
    main()
