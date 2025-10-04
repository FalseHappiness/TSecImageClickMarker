import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import random
import string
import json
from PIL import Image, ImageTk
import io
import utils
import threading
import glob


def is_valid_marked_dir(dir_path):
    # 检查目录是否包含至少一个序号子目录，并且子目录中有bg.jpg、sprite.jpg和data.json
    subdir_list = [d for d in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, d)) and d.isdigit()]
    if not subdir_list:
        return False

    # 检查第一个子目录是否有必要的文件
    test_dir = os.path.join(dir_path, subdir_list[0])
    required_files = {"bg.jpg", "sprite.jpg", "data.json"}
    existing_files = set(os.listdir(str(test_dir)))

    return required_files.issubset(existing_files)


# noinspection PyArgumentList,PyTypeChecker
class CaptchaMarkerApp:
    def __init__(self, rt):
        self.root = rt
        self.root.title("腾讯验证码采集工具")

        # 初始化变量
        self.total_count = tk.IntVar(value=100)
        self.start_index = tk.IntVar(value=1)
        self.current_index = 0
        self.output_dir = ""
        self.browse_dir = ""  # 浏览模式下的目录
        self.browse_mode = False  # 是否处于浏览模式
        self.browse_files = []  # 浏览模式下的文件列表
        self.browse_index = 0  # 浏览模式下的当前索引

        self.bg_image = None
        self.sprite_image = None
        self.bg_photo = None
        self.sprite_photo = None
        self.points = []  # 当前正在标记的点
        self.blocks = []  # 已完成的块
        self.current_block_id = 0
        self.is_running = False

        # UI elements
        self.user_input_complete = None
        self.sprite_label = None
        self.bg_canvas = None
        self.status_label = None
        self.output_dir_entry = None
        self.prev_button = None
        self.next_button = None
        self.browse_button = None
        self.edit_button = None
        self.save_button = None
        self.clear_all_marks_button = None
        self.delete_current_block_button = None
        self.finish_current_block_button = None

        # 创建界面
        self.create_widgets()

        # 设置默认输出目录
        self.set_default_output_dir()

        # 绑定键盘事件
        self.root.bind("<Left>", self.prev_image)
        self.root.bind("<Right>", self.next_image)

    def create_widgets(self):
        # 控制面板框架
        control_frame = ttk.LabelFrame(self.root, text="控制面板", padding=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        # 总数设置
        ttk.Label(control_frame, text="总数:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(control_frame, textvariable=self.total_count, width=10).grid(row=0, column=1, sticky=tk.W)

        # 开始序数设置
        ttk.Label(control_frame, text="开始序数:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(control_frame, textvariable=self.start_index, width=10).grid(row=1, column=1, sticky=tk.W)

        # 输出目录设置
        ttk.Label(control_frame, text="输出目录:").grid(row=2, column=0, sticky=tk.W)
        self.output_dir_entry = ttk.Entry(control_frame, width=30)
        self.output_dir_entry.grid(row=2, column=1, sticky=tk.W)
        ttk.Button(control_frame, text="浏览...", command=self.select_output_dir).grid(row=2, column=2)

        # 浏览和编辑按钮
        self.browse_button = ttk.Button(control_frame, text="浏览标记数据", command=self.browse_marked_data)
        self.browse_button.grid(row=3, column=0, columnspan=3, pady=5)

        self.edit_button = ttk.Button(control_frame, text="编辑当前标记", command=self.toggle_edit_mode,
                                      state=tk.DISABLED)
        self.edit_button.grid(row=4, column=0, columnspan=3, pady=5)

        # 按钮区域
        ttk.Button(control_frame, text="开始采集", command=self.start_capture).grid(row=5, column=0, columnspan=3,
                                                                                    pady=5)
        ttk.Button(control_frame, text="停止采集", command=self.stop_capture).grid(row=6, column=0, columnspan=3)

        # 状态信息
        self.status_label = ttk.Label(control_frame, text="准备就绪")
        self.status_label.grid(row=7, column=0, columnspan=3, pady=10)

        # 图像显示框架
        image_frame = ttk.Frame(self.root)
        image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 导航按钮框架
        nav_frame = ttk.Frame(image_frame)
        nav_frame.pack(fill=tk.X, pady=5)

        self.prev_button = ttk.Button(nav_frame, text="上一张 (←)", command=self.prev_image, state=tk.DISABLED)
        self.prev_button.pack(side=tk.LEFT, padx=5)

        self.next_button = ttk.Button(nav_frame, text="下一张 (→)", command=self.next_image, state=tk.DISABLED)
        self.next_button.pack(side=tk.LEFT, padx=5)

        # 背景图画布
        self.bg_canvas = tk.Canvas(image_frame, width=600, height=400, bg="white")
        self.bg_canvas.pack(fill=tk.BOTH, expand=True)
        self.bg_canvas.bind("<Button-1>", self.on_bg_click)
        self.bg_canvas.bind("<Button-3>", self.on_bg_right_click)

        # Sprite图像显示
        sprite_frame = ttk.Frame(image_frame)
        sprite_frame.pack(fill=tk.X, pady=5)
        ttk.Label(sprite_frame, text="拼图:").pack(side=tk.LEFT)
        self.sprite_label = ttk.Label(sprite_frame)
        self.sprite_label.pack(side=tk.LEFT)

        # 标记控制按钮
        button_frame = ttk.Frame(image_frame)
        button_frame.pack(fill=tk.X, pady=5)

        self.finish_current_block_button = ttk.Button(button_frame, text="完成当前标记",
                                                      command=self.finish_current_block)
        self.finish_current_block_button.pack(side=tk.LEFT, padx=5)
        self.delete_current_block_button = ttk.Button(button_frame, text="删除当前块",
                                                      command=self.delete_current_block)
        self.delete_current_block_button.pack(side=tk.LEFT, padx=5)
        self.clear_all_marks_button = ttk.Button(button_frame, text="清除所有标记", command=self.clear_all_marks)
        self.clear_all_marks_button.pack(side=tk.LEFT, padx=5)
        self.save_button = ttk.Button(button_frame, text="保存并下一张", command=self.save_and_next)
        self.save_button.pack(side=tk.LEFT, padx=5)

    def set_default_output_dir(self):
        # 生成随机字符作为默认输出目录
        rand_str = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        default_dir = os.path.join(os.getcwd(), f"output_{rand_str}")
        self.output_dir = default_dir
        self.output_dir_entry.delete(0, tk.END)
        self.output_dir_entry.insert(0, default_dir)

    def select_output_dir(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.output_dir = dir_path
            self.output_dir_entry.delete(0, tk.END)
            self.output_dir_entry.insert(0, dir_path)

    def browse_marked_data(self):
        dir_path = filedialog.askdirectory()
        if not dir_path:
            return

        # 检查目录结构
        if not is_valid_marked_dir(dir_path):
            messagebox.showerror("错误", "这不是一个有效的标记数据目录")
            return

        self.browse_dir = dir_path
        self.browse_mode = True
        self.is_running = False
        self.status_label.config(text="浏览模式")
        self.save_button.config(text="保存")

        # 获取所有序号目录
        self.browse_files = sorted(
            [d for d in glob.glob(os.path.join(dir_path, "*")) if os.path.isdir(d) and d.split(os.sep)[-1].isdigit()],
            key=lambda x: int(os.path.basename(x))
        )

        if not self.browse_files:
            messagebox.showwarning("警告", "没有找到标记数据")
            return

        self.browse_index = 0
        self.prev_button.config(state=tk.NORMAL if len(self.browse_files) > 1 else tk.DISABLED)
        self.next_button.config(state=tk.NORMAL if len(self.browse_files) > 1 else tk.DISABLED)
        # noinspection DuplicatedCode
        self.edit_button.config(state=tk.NORMAL)

        self.clear_all_marks_button.config(state=tk.DISABLED)
        self.delete_current_block_button.config(state=tk.DISABLED)
        self.finish_current_block_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)

        self.load_marked_data(self.browse_files[0])

    def load_marked_data(self, dir_path):
        try:
            # 加载背景图
            with open(os.path.join(dir_path, "bg.jpg"), "rb") as f:
                bg_img_data = f.read()

            # 加载拼图
            with open(os.path.join(dir_path, "sprite.jpg"), "rb") as f:
                sprite_img_data = f.read()

            # 加载标记数据
            with open(os.path.join(dir_path, "data.json"), "r", encoding="utf-8") as f:
                data = json.load(f)

            # 显示图片和标记
            self.display_images(bg_img_data, sprite_img_data)
            self.blocks = data["blocks"]
            self.current_block_id = max([block["id"] for block in self.blocks], default=0)
            self.redraw_bg_image()

            # 更新状态
            index = int(os.path.basename(dir_path))
            self.status_label.config(text=f"浏览: {index} ({self.browse_index + 1}/{len(self.browse_files)})")

        except Exception as e:
            messagebox.showerror("错误", f"加载标记数据失败: {str(e)}")

    def toggle_edit_mode(self):
        if not self.browse_mode:
            return

        # 切换编辑模式
        if self.edit_button.cget("text") == "编辑当前标记":
            self.edit_button.config(text="退出编辑模式")
            self.status_label.config(text=f"编辑模式: {os.path.basename(self.browse_files[self.browse_index])}")

            self.clear_all_marks_button.config(state=tk.NORMAL)
            self.delete_current_block_button.config(state=tk.NORMAL)
            self.finish_current_block_button.config(state=tk.NORMAL)
            self.save_button.config(state=tk.NORMAL)
        else:
            self.edit_button.config(text="编辑当前标记")
            self.load_marked_data(self.browse_files[self.browse_index])  # 重新加载原始数据
            self.status_label.config(
                text=f"浏览: {os.path.basename(self.browse_files[self.browse_index])} ({self.browse_index + 1}/{len(self.browse_files)})")

            self.clear_all_marks_button.config(state=tk.DISABLED)
            self.delete_current_block_button.config(state=tk.DISABLED)
            self.finish_current_block_button.config(state=tk.DISABLED)
            self.save_button.config(state=tk.DISABLED)

    def change_image(self):
        self.load_marked_data(self.browse_files[self.browse_index])

        # 更新按钮状态
        self.prev_button.config(state=tk.NORMAL if self.browse_index > 0 else tk.DISABLED)
        self.next_button.config(state=tk.NORMAL if self.browse_index < len(self.browse_files) - 1 else tk.DISABLED)

    def prev_image(self, _=None):
        if not self.browse_mode or len(self.browse_files) <= 1:
            return

        if self.browse_index > 0:
            self.browse_index -= 1

            self.change_image()

    def next_image(self, _=None):
        if not self.browse_mode or len(self.browse_files) <= 1:
            return

        if self.browse_index < len(self.browse_files) - 1:
            self.browse_index += 1

            self.change_image()

    def save_position_data(self, dir_path):
        # 保存标记数据
        data = {
            "blocks": self.blocks,
            "image_size": {
                "width": self.bg_image.width,
                "height": self.bg_image.height
            }
        }

        with open(os.path.join(dir_path, "data.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def save_current_marked_data(self):
        if not self.browse_mode or self.edit_button.cget("text") != "退出编辑模式":
            return

        dir_path = self.browse_files[self.browse_index]
        try:
            # 保存修改后的标记数据
            self.save_position_data(dir_path)

            messagebox.showinfo("成功", "标记数据已保存")

        except Exception as e:
            messagebox.showerror("错误", f"保存标记数据失败: {str(e)}")

    def start_capture(self):
        if self.is_running:
            return

        # 退出浏览模式
        if self.browse_mode:
            self.browse_mode = False
            # noinspection DuplicatedCode
            self.prev_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)
            self.edit_button.config(state=tk.DISABLED)

            self.clear_all_marks_button.config(state=tk.NORMAL)
            self.delete_current_block_button.config(state=tk.NORMAL)
            self.finish_current_block_button.config(state=tk.NORMAL)
            self.save_button.config(state=tk.NORMAL)

        self.current_index = self.start_index.get() - 1
        self.is_running = True
        self.status_label.config(text="正在采集...")
        self.save_button.config(text="保存并下一张")

        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)

        # 在后台线程中开始采集
        threading.Thread(target=self.capture_loop, daemon=True).start()

    def stop_capture(self):
        self.is_running = False
        self.status_label.config(text="采集已停止")

    def capture_loop(self):
        while self.is_running and self.current_index < self.total_count.get():
            self.current_index += 1
            self.status_label.config(text=f"正在处理第 {self.current_index} 张")

            try:
                # 获取验证码数据
                data = utils.get_captcha_data()
                if not data:
                    raise Exception("获取验证码数据失败")

                # 获取验证码图片
                bg_img_data, sprite_img_data = utils.get_captcha_images(data)

                # 显示图片
                self.root.after(0, self.display_images, bg_img_data, sprite_img_data)

                # 等待用户标记
                self.wait_for_user_input()

                # 保存数据
                self.save_data(bg_img_data, sprite_img_data)

            except Exception as e:
                self.root.after(0, messagebox.showerror, "错误", f"处理第 {self.current_index} 张时出错: {str(e)}")
                continue

        self.root.after(0, self.stop_capture)

    def wait_for_user_input(self):
        # 等待用户完成标记
        self.user_input_complete = False
        while not self.user_input_complete and self.is_running:
            self.root.update()
            self.root.update_idletasks()
            if not self.is_running:
                break

    def display_images(self, bg_img_data, sprite_img_data):
        # 清空之前的标记
        self.points = []
        self.blocks = []
        self.current_block_id = 0
        self.bg_canvas.delete("all")

        # 显示背景图
        self.bg_image = Image.open(io.BytesIO(bg_img_data))
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        self.bg_canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_photo)
        self.bg_canvas.config(width=self.bg_photo.width(), height=self.bg_photo.height())

        # 显示拼图
        self.sprite_image = Image.open(io.BytesIO(sprite_img_data))
        self.sprite_photo = ImageTk.PhotoImage(self.sprite_image)
        self.sprite_label.config(image=self.sprite_photo)

    def on_bg_click(self, event):
        if not self.bg_image:
            return

        # 检查是否在编辑模式
        if self.browse_mode and self.edit_button.cget("text") != "退出编辑模式":
            return

        # 检查是否点击了已有的点
        for i, point in enumerate(self.points):
            x, y = point
            if (event.x - x) ** 2 + (event.y - y) ** 2 <= 25:  # 5像素半径内
                # 删除这个点
                self.points.pop(i)
                self.redraw_bg_image()
                return

        # 检查是否点击了已完成的块
        for i, block in enumerate(self.blocks):
            for x, y in block["points"]:
                if (event.x - x) ** 2 + (event.y - y) ** 2 <= 25:  # 5像素半径内
                    # 右键点击已完成的块的点会删除该块
                    if hasattr(event, 'num') and event.num == 3:
                        self.delete_block(i)
                    return

        # 添加新点
        self.points.append((event.x, event.y))
        self.redraw_bg_image()

    def on_bg_right_click(self, event):
        if not self.bg_image:
            return

        # 检查是否在编辑模式
        if self.browse_mode and self.edit_button.cget("text") != "退出编辑模式":
            return

        if len(self.points) > 0:
            # 右键点击完成当前块
            self.finish_current_block()
        else:
            # 检查是否点击了已完成的块
            for i, block in enumerate(self.blocks):
                for x, y in block["points"]:
                    if (event.x - x) ** 2 + (event.y - y) ** 2 <= 25:  # 5像素半径内
                        self.delete_block(i)
                        return

    def redraw_bg_image(self):
        if not self.bg_image:
            return

        # 重新绘制背景图和标记
        self.bg_canvas.delete("all")
        self.bg_canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_photo)

        # 绘制已完成的块
        for block in self.blocks:
            if len(block["points"]) > 1:
                # 绘制连线
                points = []
                for x, y in block["points"]:
                    points.extend([x, y])
                # 连接第一个和最后一个点
                points.extend([block["points"][0][0], block["points"][0][1]])
                self.bg_canvas.create_line(*points, fill="red", width=2)

            # 绘制点
            for x, y in block["points"]:
                self.bg_canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="blue", outline="blue")

            # 计算块的中心位置并显示序号
            if block["points"]:
                # 计算所有点的平均值得到中心位置
                center_x = sum(p[0] for p in block["points"]) / len(block["points"])
                center_y = sum(p[1] for p in block["points"]) / len(block["points"])
                self.bg_canvas.create_text(
                    center_x, center_y,
                    text=str(block["id"]),
                    fill="green",
                    font=('Arial', 25, 'bold'),
                    anchor="center"
                )
                self.bg_canvas.create_text(
                    center_x, center_y,
                    text=str(block["id"]),
                    fill="white",
                    font=('Arial', 20, 'normal'),
                    anchor="center"
                )

        # 绘制当前正在标记的点
        for x, y in self.points:
            self.bg_canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="green", outline="green")

        # 绘制当前点的连线
        if len(self.points) > 1:
            points = []
            for x, y in self.points:
                points.extend([x, y])
            self.bg_canvas.create_line(*points, fill="green", width=2)

    def finish_current_block(self):
        if len(self.points) < 3:
            messagebox.showwarning("警告", "至少需要3个点才能形成一个块")
            return

        # 保存当前块
        self.current_block_id += 1
        self.blocks.append({
            "id": self.current_block_id,
            "points": self.points.copy()
        })

        # 清空当前点
        self.points = []
        self.redraw_bg_image()

        # 如果在浏览模式下编辑，自动保存
        # if self.browse_mode and self.edit_button.cget("text") == "退出编辑模式":
        # self.save_current_marked_data()

    def delete_current_block(self):
        if not self.blocks:
            return

        # 删除最后一个块
        self.delete_block(len(self.blocks) - 1)

        # 如果在浏览模式下编辑，自动保存
        # if self.browse_mode and self.edit_button.cget("text") == "退出编辑模式":
        #     self.save_current_marked_data()

    def delete_block(self, index):
        if 0 <= index < len(self.blocks):
            # 删除指定块
            self.blocks.pop(index)

            # 重新编号所有块
            for i, block in enumerate(self.blocks):
                block["id"] = i + 1
            self.current_block_id = len(self.blocks)

            self.redraw_bg_image()

    def clear_all_marks(self):
        # 清除所有标记
        self.points = []
        self.blocks = []
        self.current_block_id = 0
        self.redraw_bg_image()

        # 如果在浏览模式下编辑，自动保存
        # if self.browse_mode and self.edit_button.cget("text") == "退出编辑模式":
        #     self.save_current_marked_data()

    def save_and_next(self):
        # 如果在浏览模式下编辑
        if self.browse_mode and self.edit_button.cget("text") == "退出编辑模式":
            self.save_current_marked_data()
            return

        if not self.blocks:
            messagebox.showwarning("警告", "请至少标记一个块")
            return

        self.user_input_complete = True

    def save_data(self, bg_img_data, sprite_img_data):
        # 创建序号文件夹
        save_dir = os.path.join(self.output_dir, str(self.current_index))
        os.makedirs(save_dir, exist_ok=True)

        # 保存图片
        with open(os.path.join(save_dir, "bg.jpg"), "wb") as f:
            f.write(bg_img_data)

        with open(os.path.join(save_dir, "sprite.jpg"), "wb") as f:
            f.write(sprite_img_data)

        # 保存标记数据
        self.save_position_data(save_dir)

        self.status_label.config(text=f"已保存第 {self.current_index} 张")


if __name__ == "__main__":
    root = tk.Tk()
    app = CaptchaMarkerApp(root)
    root.mainloop()
