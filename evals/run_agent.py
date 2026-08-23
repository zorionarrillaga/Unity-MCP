import argparse
import asyncio
import json
import os
import sys

from openai import AsyncOpenAI
from mcp.client.streamable_http import streamable_http_client
from mcp.client.session import ClientSession
from dotenv import load_dotenv

async def main():
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True, help="MCP server port")
    parser.add_argument("--prompt", type=str, required=True, help="Prompt for the agent")
    parser.add_argument("--model", type=str, default="deepseek-chat", help="DeepSeek model name")
    parser.add_argument("--token", type=str, default="", help="Authorization Bearer token")
    args = parser.parse_args()

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("Error: DEEPSEEK_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )

    url = f"http://127.0.0.1:{args.port}/"
    print(f"Connecting to MCP server via Streamable HTTP at {url} ...")

    import httpx2
    headers = {}
    if args.token:
        headers["Authorization"] = f"Bearer {args.token}"
        print("Using Bearer token for authentication.")
        
    custom_client = httpx2.AsyncClient(headers=headers, timeout=httpx2.Timeout(5.0, read=None))

    try:
        async with streamable_http_client(url=url, http_client=custom_client) as (read, write):
            async with ClientSession(read, write) as session:
                try:
                    await session.initialize()
                except Exception as e:
                    print(f"Failed to initialize session: {type(e).__name__} - {e}")
                    if hasattr(e, 'message'):
                        print(f"Error message: {e.message}")
                    if hasattr(e, 'data'):
                        print(f"Error data: {e.data}")
                    import traceback
                    traceback.print_exc()
                    raise

                response = await session.list_tools()
                tools = response.tools
                
                print(f"Loaded {len(tools)} tools from Unity MCP.")
                openai_tools = []
                for t in tools:
                    openai_tools.append({
                        "type": "function",
                        "function": {
                            "name": t.name,
                            "description": t.description,
                            "parameters": t.input_schema
                        }
                    })

                print(f"Loaded {len(openai_tools)} tools from Unity MCP.")
                messages = [{"role": "user", "content": args.prompt}]

                while True:
                    print("Waiting for LLM response...")
                    response = await client.chat.completions.create(
                        model=args.model,
                        messages=messages,
                        tools=openai_tools,
                        tool_choice="auto",
                    )

                    message = response.choices[0].message
                    messages.append(message)

                    if not message.tool_calls:
                        print(f"Final response: {message.content}")
                        break

                    for tool_call in message.tool_calls:
                        print(f"\nExecuting Tool: {tool_call.function.name}")
                        print(f"Arguments: {tool_call.function.arguments}")

                        try:
                            args_dict = json.loads(tool_call.function.arguments)
                        except json.JSONDecodeError:
                            args_dict = {}

                        try:
                            result = await session.call_tool(tool_call.function.name, args_dict)
                            result_text = "\n".join([c.text for c in result.content if c.type == "text"])
                            print(f"Tool Result: {result_text}")

                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": tool_call.function.name,
                                "content": result_text
                            })
                        except Exception as e:
                            print(f"Tool execution failed: {e}")
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": tool_call.function.name,
                                "content": f"Error: {e}"
                            })

    except Exception as ex:
        import traceback
        traceback.print_exc()
        print(f"Agent execution failed: {ex}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
