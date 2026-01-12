import tkinter as tk
from gui import SignInApp
import traceback

# 简化版主应用，只运行GUI部分
if __name__ == "__main__":
    try:
        print("启动每日签到提醒系统...")
        root = tk.Tk()
        app = SignInApp(root)
        root.mainloop()
    except Exception as e:
        print(f"应用启动失败: {e}")
        print("详细错误信息:")
        traceback.print_exc()
        input("按回车键退出...")