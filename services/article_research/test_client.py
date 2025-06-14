import asyncio
import websockets
import json
import logging
from datetime import datetime
import sys
import signal

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResearchWorkflowTestClient:
    """AutoGen研究工作流测试客户端"""

    # send message to our url
    def __init__(self, uri: str = "ws://localhost:8000/ws/chat"):
        self.uri = uri
        self.websocket = None
        self.connected = False
        self.running = True

    async def connect(self):
        """connect to websocker"""
        try:
            self.websocket = await websockets.connect(self.uri)
            self.connected = True
            print(f"✅ 成功连接到 {self.uri}")
            return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False

    async def send_message(self, content: str, message_type: str = "user_message"):
        """发送消息到服务器"""
        if not self.connected or not self.websocket:
            print("❌ 未连接到服务器")
            return False

        try:
            message = {
                "content": content,
                "type": message_type,
                "role": "user",
                "name": "user",
                "timestamp": datetime.now().isoformat()
            }
            await self.websocket.send(json.dumps(message))
            return True
        except Exception as e:
            print(f"❌ 发送消息失败: {e}")
            return False

    # client listen from  server
    async def listen_for_messages(self):
        if not self.connected or not self.websocket:
            print("❌ 未连接到服务器")
            return

        try:
            async for message in self.websocket:
                if not self.running:
                    break

                try:
                    data = json.loads(message)
                    completed = await self.handle_message(data)
                    if completed:
                        print("\n🎉 工作流程已完成！")
                        break
                except json.JSONDecodeError:
                    print(f"❌ 无效的JSON消息: {message}")
                except Exception as e:
                    print(f"❌ 处理消息时出错: {e}")
        except websockets.exceptions.ConnectionClosed:
            print("\n🔌 服务器关闭了连接")
        except Exception as e:
            print(f"\n❌ 监听消息时出错: {e}")

    async def handle_message(self, message: dict):
        """处理来自服务器的消息"""
        msg_type = message.get("type", "unknown")
        content = message.get("content", "")
        name = message.get("name", "unknown")
        timestamp = message.get("timestamp", "")

        # 新增代理消息类型
        if msg_type == "agent_message":
            emoji = self.get_agent_emoji(name)
            print(f"\n{emoji} [{name.upper()}] {content}")

            # 检查是否需要用户输入
            if "需要您的输入" in content or "请提供反馈" in content:
                print("\n❓ 代理请求输入...")
                await self.handle_user_input_request(content)

            # 聊天消息
        elif msg_type == "chat_message":
            print(f"\n💬 [{name.upper()}] {content}")

            # 检查终止条件
            if "APPROVE" in content:
                print("\n✅ 工作流程已完成！")
                return True

            # 系统消息
        elif msg_type == "system_message":
            print(f"\n🤖 [系统] {content}")

            # 用户消息
        elif msg_type == "user_message":
            print(f"\n👤 [用户] {content}")

            # 工作流状态
        elif msg_type == "workflow_started":
            print(f"\n🚀 [工作流启动] {content}")

        elif msg_type == "workflow_completed":
            print(f"\n✅ [工作流完成] {content}")
            self.running = False # set running flag = False
            return True

        elif msg_type == "error":
            print(f"\n❌ [错误] {content}")

        else:
            # 代理消息或其他类型
            emoji = self.get_agent_emoji(name)
            print(f"\n{emoji} [{name.upper()}] {content}")

        # 检查完成关键词
        content_lower = content.lower()
        if any(term in content_lower for term in ["approve", "完成", "终止", "结束", "finish"]):
            print("\n✅ 工作流程已完成！")
            self.running = False  # 设置运行标志为False
            return True

        return False

    def get_agent_emoji(self, agent_name: str) -> str:
        """根据代理名称返回表情符号"""
        emoji_map = {
            "survey_director": "📋",
            "paper_retriever": "🔍",
            "paper_summarizer": "📝",
            "survey_analyst": "📊",
            "user_proxy": "👤",
            "assistant": "🤖",
            "system": "⚙️"
        }
        return emoji_map.get(agent_name.lower(), "🔬")

    async def handle_user_input_request(self, prompt: str):
        """处理用户输入请求"""
        print(f"\n⌨️  代理请求输入: {prompt}")
        print("请输入指令 (Go on/More details/Fix up some questions/APPROVE):")

        # 根据提示生成模拟响应
        user_response = self.get_simulated_response(prompt)
        print(f"🤔 模拟回复: {user_response}")

        # 发送用户响应
        await self.send_message(user_response)

    def get_simulated_response(self, prompt: str) -> str:
        """根据提示生成模拟用户响应"""
        prompt_lower = prompt.lower()

        # 常见的研究工作流响应
        if any(word in prompt_lower for word in ["继续", "下一步", "proceed", "continue"]):
            return "继续"
        elif any(word in prompt_lower for word in ["详细", "详细信息", "more details", "elaborate"]):
            return "请提供更详细的分析"
        elif any(word in prompt_lower for word in ["修改", "改进", "refine", "improve"]):
            return "REFINE 文献综述部分"
        elif any(word in prompt_lower for word in ["扩展", "展开", "expand"]):
            return "EXPAND 研究方法"
        elif any(word in prompt_lower for word in ["总结", "摘要", "summarize"]):
            return "SUMMARIZE"
        elif any(word in prompt_lower for word in ["批准", "确认", "approve", "confirm"]):
            return "APPROVE"
        elif any(word in prompt_lower for word in ["指令", "命令", "command"]):
            return "继续研究"
        else:
            # 默认响应
            return "继续"

    async def close(self):
        """关闭WebSocket连接"""
        self.running = False
        if self.websocket and self.connected:
            try:
                # 发送关闭通知
                await self.websocket.send(json.dumps({
                    "type": "close",
                    "content": "客户端关闭连接",
                    "name": "client",
                    "timestamp": datetime.now().isoformat()
                }))
                # 等待服务器确认
                await asyncio.sleep(0.5)
            except:
                pass
            finally:
                await self.websocket.close()
                self.connected = False
                print("🔌 连接已关闭")


"""自动测试工作流"""
async def test_automatic_workflow():

    print("🎯 启动自动测试模式")
    print("=" * 50)

    client = ResearchWorkflowTestClient()
    if not await client.connect():
        return
    test_topics = [
        "大语言模型在推荐系统中的应用",
        "深度学习在计算机视觉中的最新进展",
        "强化学习在自动驾驶中的应用",
        "Transformer架构在自然语言处理中的创新"
    ]

    try:
        # choose topic
        topic = test_topics[3]
        print(f"🔍 开始研究主题: {topic}")
        print("-" * 50)

        listen_task = asyncio.create_task(client.listen_for_messages())
        await asyncio.sleep(1)
        await client.send_message(topic)

        try:
            await asyncio.wait_for(listen_task, timeout=600)  # 10分钟超时
        except asyncio.TimeoutError:
            print("\n⏰ 测试超时")

    except KeyboardInterrupt:
        print("\n⛔ 用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
    finally:
        await client.close()


async def test_interactive_workflow():
    """交互式测试工作流"""
    print("🎯 启动交互式测试模式")
    print("💡 您可以手动输入回复或输入 'quit' 退出")
    print("=" * 50)

    client = ResearchWorkflowTestClient()

    if not await client.connect():
        return

    try:
        listen_task = asyncio.create_task(client.listen_for_messages())

        topic = input("\n📝 请输入研究主题: ").strip()
        if not topic:
            topic = "大语言模型在推荐系统中的应用"
            print(f"使用默认主题: {topic}")

        print(f"🔍 开始研究: {topic}")
        await client.send_message(topic)

        # 在后台处理用户输入
        def handle_user_input(loop):
            while client.running:
                try:
                    user_input = input().strip()
                    if user_input.lower() in ['APPROVE']:
                        client.running = False
                        ## 必须要关闭事件循环
                        asyncio.run_coroutine_threadsafe(client.close(), loop)
                        break
                    if user_input:
                        # 使用事件循环发送消息
                        asyncio.run_coroutine_threadsafe(
                            client.send_message(user_input),
                            loop
                        )
                except (EOFError, KeyboardInterrupt):
                        client.running = False
                        asyncio.run_coroutine_threadsafe(client.close(), loop)
                        break
                except Exception as e:
                    print(f"输入处理错误: {e}")
                    client.running = False
                    asyncio.run_coroutine_threadsafe(client.close(), loop)
                    break

        loop = asyncio.get_running_loop()
        # 启动用户输入处理线程
        import threading
        input_thread = threading.Thread(target=handle_user_input,args=(loop,), daemon=False)
        input_thread.start()

        # 等待监听任务完成
        try:
            await listen_task
        finally:
            # 确保输入线程结束
            if input_thread.is_alive():
                input_thread.join(timeout=2.0)
            await client.close()

    except KeyboardInterrupt:
        print("\n⛔ 用户中断测试")
    except Exception as e:
        print(f"\n❌ 交互式测试出错: {e}")
    finally:
        await client.close()


async def test_stress_workflow():
    """压力测试 - 多个并发会话"""
    print("🎯 启动压力测试模式")
    print("⚡ 将创建多个并发会话")
    print("=" * 50)

    topics = [
        "深度学习在医疗诊断中的应用",
        "区块链技术在金融领域的创新",
        "人工智能在教育个性化中的作用"
    ]

    async def run_single_session(session_id: int, topic: str):
        """运行单个会话"""
        print(f"🔄 会话 {session_id}: 开始研究 '{topic}'")

        client = ResearchWorkflowTestClient()

        try:
            if await client.connect():
                # 启动监听
                listen_task = asyncio.create_task(client.listen_for_messages())

                # 发送主题
                await client.send_message(topic)

                # 等待完成（较短超时用于压力测试）
                await asyncio.wait_for(listen_task, timeout=180)

                print(f"✅ 会话 {session_id}: 完成")
        except asyncio.TimeoutError:
            print(f"⏰ 会话 {session_id}: 超时")
        except Exception as e:
            print(f"❌ 会话 {session_id}: 出错 - {e}")
        finally:
            await client.close()

    # 创建并发任务
    tasks = []
    for i, topic in enumerate(topics):
        task = asyncio.create_task(run_single_session(i + 1, topic))
        tasks.append(task)
        await asyncio.sleep(2)  # 错开启动时间

    # 等待所有任务完成
    try:
        await asyncio.gather(*tasks)
        print("\n🎉 所有压力测试会话完成！")
    except Exception as e:
        print(f"\n❌ 压力测试出错: {e}")


def main():
    """主函数 - 选择测试模式"""
    print("🚀 AutoGen 研究工作流测试客户端")
    print("=" * 50)
    print("请选择测试模式:")
    print("1. 自动测试 (推荐)")
    print("2. 交互式测试")
    print("3. 压力测试")
    print("4. 退出")

    try:
        choice = input("\n请输入选择 (1-4): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n👋 再见！")
        return

    # 设置信号处理器用于优雅退出
    def signal_handler(sig, frame):
        print("\n⛔ 收到退出信号，正在关闭...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # 根据选择运行相应的测试
    if choice == "1":
        asyncio.run(test_automatic_workflow())
    elif choice == "2":
        asyncio.run(test_interactive_workflow())
    elif choice == "3":
        asyncio.run(test_stress_workflow())
    elif choice == "4":
        print("👋 再见！")
    else:
        print("❌ 无效选择，使用默认自动测试模式")
        asyncio.run(test_automatic_workflow())


if __name__ == "__main__":
    main()