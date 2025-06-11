import asyncio
import websockets
import json

async def test_research_workflow():
    uri = "ws://localhost:8000/ws/chat"
    async with websockets.connect(uri) as websocket:
        # 发送初始主题
        initial_message = {
            "content": "大语言模型在推荐系统中的应用",
            "role": "user",
            "name": "user"
        }
        await websocket.send(json.dumps(initial_message))

        print("发送了初始主题: 大语言模型在推荐系统中的应用")
        print("等待回复...")

        # 接收并打印所有回复
        while True:
            try:
                response = await websocket.recv()
                message = json.loads(response)

                if message.get("type") == "error":
                    print(f"错误: {message['content']}")
                    break

                # 显示代理回复
                source = message.get("name", message.get("source", "unknown"))
                print(f"{source}: {message['content']}")

                # 检查是否需要用户输入
                if message.get("type") == "UserInputRequestedEvent":
                    # 模拟用户输入
                    # 在实际测试中，你可以根据提示输入相应内容
                    # 这里我们预设一些测试输入
                    if "请输入你的指令" in message["content"]:
                        # 模拟输入REFINE来细化某个部分
                        user_input = "REFINE 研究方法"
                    else:
                        # 默认继续
                        user_input = "继续"

                    print(f"发送用户输入: {user_input}")
                    user_message = {
                        "content": user_input,
                        "role": "user",
                        "name": "user"
                    }
                    await websocket.send(json.dumps(user_message))

                # 检查是否应该终止对话
                if "APPROVE" in message.get("content", ""):
                    print("检测到APPROVE，对话将终止")
                    break

            except websockets.exceptions.ConnectionClosedOK:
                print("连接已正常关闭")
                break

asyncio.get_event_loop().run_until_complete(test_research_workflow())