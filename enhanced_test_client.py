"""
修复的测试客户端 - 真正的交互式实现
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime
import sys
import signal
from typing import Dict, Any
import threading
import queue

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrueInteractiveClient:
    """真正的交互式客户端"""

    def __init__(self, base_uri: str = "ws://localhost:8000"):
        self.base_uri = base_uri
        self.websocket = None
        self.connected = False
        self.running = True
        self.workflow_type = None
        self.input_queue = queue.Queue()
        self.waiting_for_input = False
        self.workflow_started = False

    async def connect(self, workflow_type: str):
        """连接到指定工作流"""
        self.workflow_type = workflow_type
        uri = f"{self.base_uri}/ws/{workflow_type}"

        try:
            self.websocket = await websockets.connect(uri)
            self.connected = True
            print(f"\n✅ 成功连接到 {workflow_type} 工作流")
            print(f"🔗 连接地址: {uri}")
            return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False

    async def send_message(self, content: str):
        """发送消息到服务器"""
        if not self.connected or not self.websocket:
            print("❌ 未连接到服务器")
            return False

        try:
            message = {
                "content": content,
                "type": "user_message",
                "name": "user",
                "timestamp": datetime.now().isoformat()
            }
            await self.websocket.send(json.dumps(message))
            return True
        except Exception as e:
            print(f"❌ 发送消息失败: {e}")
            return False

    def start_input_thread(self):
        """启动输入处理线程"""
        def input_worker():
            print("\n📝 输入线程已启动，您可以随时输入...")
            while self.running:
                try:
                    user_input = input().strip()
                    if user_input:
                        self.input_queue.put(user_input)
                        if user_input.upper() in ["QUIT", "EXIT", "CLOSE"]:
                            self.running = False
                            break
                except (EOFError, KeyboardInterrupt):
                    self.input_queue.put("APPROVE")
                    self.running = False
                    break
                except Exception as e:
                    logger.error(f"输入线程错误: {e}")

        input_thread = threading.Thread(target=input_worker, daemon=True)
        input_thread.start()

    async def process_user_input(self):
        """处理用户输入队列"""
        while self.running:
            try:
                if not self.input_queue.empty():
                    user_input = self.input_queue.get_nowait()

                    if user_input.upper() in ["QUIT", "EXIT", "CLOSE"]:
                        print(f"\n👋 用户主动退出")
                        self.running = False
                        break

                    # 发送用户输入
                    await self.send_message(user_input)
                    print(f"📤 已发送: {user_input}")

                await asyncio.sleep(0.1)  # 避免CPU占用过高

            except Exception as e:
                logger.error(f"处理用户输入时出错: {e}")

    async def listen_for_messages(self):
        """监听服务器消息"""
        try:
            async for message in self.websocket:
                if not self.running:
                    break

                try:
                    data = json.loads(message)
                    completed = await self.handle_message(data)
                    if completed:
                        print(f"\n🎉 {self.workflow_type} 工作流程已完成！")
                        self.running = False
                        break
                except json.JSONDecodeError:
                    print(f"❌ 无效的JSON消息: {message}")
                except Exception as e:
                    print(f"❌ 处理消息时出错: {e}")

        except websockets.exceptions.ConnectionClosed:
            print(f"\n🔌 {self.workflow_type} 工作流连接已关闭")
        except Exception as e:
            print(f"\n❌ 监听消息时出错: {e}")

    async def handle_message(self, message: dict):
        """处理来自服务器的消息"""
        msg_type = message.get("type", "unknown")
        content = message.get("content", "")
        name = message.get("name", "unknown")

        # 根据消息类型显示
        if msg_type == "agent_message":
            emoji = self.get_agent_emoji(name, self.workflow_type)
            print(f"\n{emoji} [{name.upper()}] {content}")

        elif msg_type == "system_message":
            print(f"\n🤖 [系统] {content}")

        elif msg_type == "user_message":
            print(f"\n👤 [用户] {content}")

        elif msg_type == "workflow_started":
            print(f"\n🚀 [启动] {content}")
            self.workflow_started = True

        elif msg_type == "workflow_completed":
            print(f"\n✅ [完成] {content}")
            return True

        elif msg_type == "error":
            print(f"\n❌ [错误] {content}")

        elif msg_type == "user_input_requested":
            print(f"\n⌨️  [需要输入] {content}")
            self.waiting_for_input = True

        else:
            emoji = self.get_agent_emoji(name, self.workflow_type)
            print(f"\n{emoji} [{name.upper()}] {content}")

        return False

    def get_agent_emoji(self, agent_name: str, workflow_type: str) -> str:
        """根据代理名称返回表情符号"""
        survey_emojis = {
            "surveydirector": "📋", "paperretriever": "🔍",
            "papersummarizer": "📝", "surveyanalyst": "📊"
        }
        solution_emojis = {
            "solutiondirector": "🎯", "solutiondesigner": "🏗️",
            "designreviewer": "🔍", "solutionrefiner": "⚙️"
        }
        paper_emojis = {
            "paperdirector": "📚", "writingassistant": "✍️",
            "referencemanager": "📖", "figuregenerator": "📊",
            "paperpolisher": "✨"
        }

        workflow_emoji_map = {
            "survey": survey_emojis,
            "solution": solution_emojis,
            "paper": paper_emojis
        }

        emoji_map = workflow_emoji_map.get(workflow_type, {})
        return emoji_map.get(agent_name.lower(), "🤖")

    async def run_interactive_session(self, initial_message: str):
        """运行交互式会话"""
        print(f"\n🎯 启动 {self.workflow_type} 交互式会话")
        print("=" * 60)
        print("💡 使用指南:")
        print("- 随时输入您的指导意见")
        print("- 输入 'APPROVE' 完成工作流")
        print("- 输入 'QUIT' 强制退出")
        print("- 按 Ctrl+C 也可以退出")
        print("=" * 60)

        # 启动输入处理线程
        self.start_input_thread()

        # 发送初始消息
        print(f"\n📤 发送初始消息: {initial_message}")
        await self.send_message(initial_message)

        # 同时运行消息监听和用户输入处理
        try:
            await asyncio.gather(
                self.listen_for_messages(),
                self.process_user_input()
            )
        except asyncio.CancelledError:
            print("\n⛔ 会话被取消")
        except Exception as e:
            print(f"\n❌ 会话出错: {e}")

    async def close(self):
        """关闭连接"""
        self.running = False
        if self.websocket and self.connected:
            try:
                await self.websocket.close()
                self.connected = False
                print(f"\n🔌 {self.workflow_type} 工作流连接已关闭")
            except:
                pass


async def test_interactive_workflow(workflow_type: str, initial_message: str):
    """测试交互式工作流"""
    client = TrueInteractiveClient()

    if not await client.connect(workflow_type):
        return

    try:
        await client.run_interactive_session(initial_message)
    except KeyboardInterrupt:
        print(f"\n⛔ {workflow_type} 工作流测试被用户中断")
    except Exception as e:
        print(f"\n❌ {workflow_type} 工作流测试过程中出错: {e}")
    finally:
        await client.close()


def main():
    """主函数"""
    print("🚀 AutoGen 真正交互式工作流测试客户端")
    print("=" * 60)
    print("请选择测试模式:")
    print("1. 文献调研工作流")
    print("2. 方案设计工作流")
    print("3. 论文写作工作流")
    print("4. 退出")

    try:
        choice = input("\n请输入选择 (1-4): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n👋 再见！")
        return

    # 设置信号处理器
    def signal_handler(sig, frame):
        print("\n⛔ 收到退出信号，正在关闭...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    workflow_map = {
        "1": "survey",
        "2": "solution",
        "3": "paper"
    }

    if choice in workflow_map:
        workflow_type = workflow_map[choice]

        # 获取初始消息
        try:
            initial_message = input(f"\n📝 请输入 {workflow_type} 工作流的初始消息: ").strip()
            if not initial_message:
                default_messages = {
                    "survey": "深度学习在计算机视觉中的最新进展",
                    "solution": "基于深度学习的图像识别系统设计",
                    "paper": "深度学习图像识别技术的综述论文"
                }
                initial_message = default_messages[workflow_type]
                print(f"使用默认消息: {initial_message}")

            asyncio.run(test_interactive_workflow(workflow_type, initial_message))

        except (EOFError, KeyboardInterrupt):
            print("\n👋 再见！")

    elif choice == "4":
        print("👋 再见！")
    else:
        print("❌ 无效选择")


if __name__ == "__main__":
    main()