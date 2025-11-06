import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image
from tkinterdnd2 import TkinterDnD, DND_FILES
import math
import tempfile
from typing import Tuple, Optional

# 客户端原始代码
class ImageResizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("图片大小/尺寸调整工具 - jerryxiao.dev@outlook.com")
        self.root.geometry("750x600")
        self.root.configure(bg="#f0f0f0")

        # 创建拖放区域
        self.drop_frame = tk.Frame(root, bg="#e0e0e0", bd=2, relief=tk.GROOVE)
        self.drop_frame.pack(padx=50, pady=20, fill=tk.BOTH, expand=True)

        # 拖放区域提示文字
        self.drop_label = tk.Label(
            self.drop_frame,
            text="将图像文件拖放到此处\n或点击选择图像",
            bg="#e0e0e0",
            font=("SimHei", 12)
        )
        self.drop_label.pack(expand=True)

        # 注册拖放功能
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.on_drop)

        # 添加选择文件按钮
        self.select_btn = ttk.Button(
            root,
            text="选择图像文件",
            command=self.select_image
        )
        self.select_btn.pack(pady=10)

        # 显示当前选择的文件路径和信息
        self.file_info_frame = ttk.LabelFrame(root, text="文件信息")
        self.file_info_frame.pack(padx=20, pady=5, fill=tk.X)

        self.file_path_var = tk.StringVar()
        self.file_path_label = tk.Label(
            self.file_info_frame,
            textvariable=self.file_path_var,
            bg="#f0f0f0",
            wraplength=700,
            justify=tk.LEFT
        )
        self.file_path_label.pack(pady=5, padx=10, anchor=tk.W)

        self.file_stats_var = tk.StringVar()
        self.file_stats_label = tk.Label(
            self.file_info_frame,
            textvariable=self.file_stats_var,
            bg="#f0f0f0",
            justify=tk.LEFT
        )
        self.file_stats_label.pack(pady=5, padx=10, anchor=tk.W)

        # 调整方式选择
        self.option_frame = ttk.LabelFrame(root, text="调整方式")
        self.option_frame.pack(padx=20, pady=5, fill=tk.X)

        self.resize_option = tk.StringVar(value="dimension")

        ttk.Radiobutton(
            self.option_frame,
            text="按像素尺寸调整",
            variable=self.resize_option,
            value="dimension",
            command=self.update_input_fields
        ).pack(side=tk.LEFT, padx=20, pady=10)

        ttk.Radiobutton(
            self.option_frame,
            text="按文件大小调整",
            variable=self.resize_option,
            value="filesize",
            command=self.update_input_fields
        ).pack(side=tk.LEFT, padx=20, pady=10)

        # 参数输入区域
        self.params_frame = ttk.LabelFrame(root, text="调整参数")
        self.params_frame.pack(padx=20, pady=10, fill=tk.X)

        # 像素尺寸调整参数
        self.dimension_frame = ttk.Frame(self.params_frame)

        ttk.Label(self.dimension_frame, text="宽度 (px):").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.width_entry = ttk.Entry(self.dimension_frame, width=10)
        self.width_entry.grid(row=0, column=1, padx=5, pady=10)

        ttk.Label(self.dimension_frame, text="高度 (px):").grid(row=0, column=2, padx=10, pady=10, sticky=tk.W)
        self.height_entry = ttk.Entry(self.dimension_frame, width=10)
        self.height_entry.grid(row=0, column=3, padx=5, pady=10)

        self.preserve_ratio_var = tk.BooleanVar(value=True)
        self.preserve_ratio_check = ttk.Checkbutton(
            self.dimension_frame,
            text="保持宽高比",
            variable=self.preserve_ratio_var,
            command=self.update_ratio_lock
        )
        self.preserve_ratio_check.grid(row=0, column=4, padx=20, pady=10)

        # 绑定宽度输入事件，自动计算高度（如果保持比例）
        self.width_entry.bind("<FocusOut>", self.calculate_height)
        self.width_entry.bind("<Return>", self.calculate_height)
        self.height_entry.bind("<FocusOut>", self.calculate_width)
        self.height_entry.bind("<Return>", self.calculate_width)

        # 文件大小调整参数
        self.filesize_frame = ttk.Frame(self.params_frame)

        ttk.Label(self.filesize_frame, text="目标大小:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.size_value_entry = ttk.Entry(self.filesize_frame, width=10)
        self.size_value_entry.grid(row=0, column=1, padx=5, pady=10)

        self.size_unit_var = tk.StringVar(value="KB")
        size_unit_combo = ttk.Combobox(
            self.filesize_frame,
            textvariable=self.size_unit_var,
            values=["KB", "MB", "B"],
            width=5,
            state="readonly"
        )
        size_unit_combo.grid(row=0, column=2, padx=5, pady=10)

        # 容差设置
        ttk.Label(self.filesize_frame, text="容差范围:").grid(row=0, column=3, padx=10, pady=10, sticky=tk.W)
        self.tolerance_var = tk.StringVar(value="20")
        ttk.Entry(self.filesize_frame, textvariable=self.tolerance_var, width=5).grid(row=0, column=4, padx=5, pady=10)
        ttk.Label(self.filesize_frame, text="%").grid(row=0, column=5, padx=0, pady=10)

        # 处理按钮
        self.process_btn = ttk.Button(
            root,
            text="开始调整",
            command=self.process_image,
            state=tk.DISABLED
        )
        self.process_btn.pack(pady=15)

        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        self.status_bar = tk.Label(
            root,
            textvariable=self.status_var,
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg="#f0f0f0"
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # 存储当前选中的图像路径和信息
        self.current_image_path = None
        self.current_image_size = 0  # 字节
        self.current_image_dimensions = (0, 0)  # 宽, 高
        self.original_aspect_ratio = 1.0  # 宽高比
        self.updating_dimensions = False  # 防止递归更新

        # 初始显示像素尺寸调整参数
        self.update_input_fields()
        self.update_ratio_lock()

    def update_input_fields(self):
        """根据选择的调整方式显示对应的输入字段"""
        # 先隐藏所有参数框架
        for widget in self.params_frame.winfo_children():
            widget.pack_forget()

        # 显示选中的参数框架
        if self.resize_option.get() == "dimension":
            self.dimension_frame.pack(fill=tk.X, padx=10, pady=5)
        else:
            self.filesize_frame.pack(fill=tk.X, padx=10, pady=5)

    def update_ratio_lock(self):
        """根据保持宽高比选项更新输入框状态"""
        if self.preserve_ratio_var.get() and self.current_image_dimensions != (0, 0):
            # 保持宽高比时，用户只能修改一个维度，另一个会自动计算
            # 这里不直接禁用，而是通过代码控制，避免用户困惑
            self.width_entry.unbind("<KeyRelease>")
            self.height_entry.unbind("<KeyRelease>")
        else:
            # 不保持宽高比时，两个维度都可自由编辑
            pass

    def calculate_width(self, event=None):
        """根据高度计算宽度（保持宽高比）"""
        if not self.preserve_ratio_var.get() or self.current_image_dimensions == (0, 0) or self.updating_dimensions:
            return

        try:
            # 防止递归更新
            self.updating_dimensions = True

            # 获取高度输入
            height_text = self.height_entry.get().strip()
            if height_text:
                height = int(height_text)
                if height > 0:
                    # 根据宽高比计算宽度
                    width = int(height * self.original_aspect_ratio)
                    # 更新宽度输入框
                    self.width_entry.delete(0, tk.END)
                    self.width_entry.insert(0, str(width))
        except ValueError:
            # 输入不是有效的数字，不做处理
            pass
        finally:
            self.updating_dimensions = False

    def calculate_height(self, event=None):
        """根据宽度计算高度（保持宽高比）"""
        if not self.preserve_ratio_var.get() or self.current_image_dimensions == (0, 0) or self.updating_dimensions:
            return

        try:
            # 防止递归更新
            self.updating_dimensions = True

            # 获取宽度输入
            width_text = self.width_entry.get().strip()
            if width_text:
                width = int(width_text)
                if width > 0:
                    # 根据宽高比计算高度
                    height = int(width / self.original_aspect_ratio)
                    # 更新高度输入框
                    self.height_entry.delete(0, tk.END)
                    self.height_entry.insert(0, str(height))
        except ValueError:
            # 输入不是有效的数字，不做处理
            pass
        finally:
            self.updating_dimensions = False

    def on_drop(self, event):
        """处理拖放事件"""
        # 获取拖放的文件路径
        file_path = event.data.strip('{}')  # 去除路径前后可能的大括号

        # 检查是否是图像文件
        if self.is_valid_image(file_path):
            self.load_image(file_path)
        else:
            messagebox.showerror("错误", "请拖放有效的图像文件（支持JPG、PNG、BMP等格式）")

    def select_image(self):
        """通过文件选择对话框选择图像"""
        file_path = filedialog.askopenfilename(
            title="选择图像文件",
            filetypes=[
                ("图像文件", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff"),
                ("所有文件", "*.*")
            ]
        )

        if file_path and self.is_valid_image(file_path):
            self.load_image(file_path)

    def load_image(self, file_path):
        """加载图像并更新信息"""
        self.current_image_path = file_path
        self.file_path_var.set(f"文件路径: {file_path}")

        # 获取文件大小
        self.current_image_size = os.path.getsize(file_path)
        size_str = self.format_size(self.current_image_size)

        # 获取图像尺寸
        with Image.open(file_path) as img:
            self.current_image_dimensions = img.size  # (宽, 高)
            self.original_aspect_ratio = img.width / img.height

        # 更新统计信息
        self.file_stats_var.set(
            f"当前大小: {size_str} | 像素尺寸: {self.current_image_dimensions[0]}x{self.current_image_dimensions[1]}px"
        )

        # 填充当前尺寸到输入框
        self.width_entry.delete(0, tk.END)
        self.width_entry.insert(0, str(self.current_image_dimensions[0]))
        self.height_entry.delete(0, tk.END)
        self.height_entry.insert(0, str(self.current_image_dimensions[1]))

        # 估计一个合理的目标文件大小（当前大小的70%）
        target_size = int(self.current_image_size * 0.7)
        if target_size >= 1024 * 1024:
            self.size_value_entry.delete(0, tk.END)
            self.size_value_entry.insert(0, f"{target_size / (1024 * 1024):.1f}")
            self.size_unit_var.set("MB")
        elif target_size >= 1024:
            self.size_value_entry.delete(0, tk.END)
            self.size_value_entry.insert(0, f"{target_size / 1024:.0f}")
            self.size_unit_var.set("KB")
        else:
            self.size_value_entry.delete(0, tk.END)
            self.size_value_entry.insert(0, str(target_size))
            self.size_unit_var.set("B")

        self.process_btn.config(state=tk.NORMAL)
        self.status_var.set(f"已加载图像: {os.path.basename(file_path)}")

    def is_valid_image(self, file_path) -> bool:
        """检查文件是否为有效的图像"""
        if not os.path.isfile(file_path):
            return False

        try:
            with Image.open(file_path):
                return True
        except Exception:
            return False

    def format_size(self, size_bytes: int) -> str:
        """将字节数转换为易读的格式（B, KB, MB）"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.2f} MB"

    def validate_dimension_input(self) -> Optional[Tuple[int, int]]:
        """验证像素尺寸输入"""
        try:
            width = int(self.width_entry.get().strip())
            height = int(self.height_entry.get().strip())

            if width <= 0 or height <= 0:
                messagebox.showerror("错误", "宽度和高度必须是大于0的整数")
                return None

            return (width, height)

        except ValueError:
            messagebox.showerror("错误", "请输入有效的宽度和高度（整数）")
            return None

    def validate_filesize_input(self) -> Optional[Tuple[int, float]]:
        """验证文件大小输入，返回(目标大小字节, 容差比例)"""
        try:
            size_value = float(self.size_value_entry.get().strip())
            size_unit = self.size_unit_var.get()

            # 验证容差
            tolerance = float(self.tolerance_var.get().strip())
            if tolerance <= 0 or tolerance > 50:
                messagebox.showerror("错误", "容差范围必须是0-50之间的数值")
                return None

            if size_value <= 0:
                messagebox.showerror("错误", "文件大小必须大于0")
                return None

            # 转换为字节
            if size_unit == "MB":
                size_bytes = int(size_value * 1024 * 1024)
            elif size_unit == "KB":
                size_bytes = int(size_value * 1024)
            else:  # B
                size_bytes = int(size_value)

            # 检查是否远大于原始大小
            if size_bytes > self.current_image_size * 2:
                if not messagebox.askyesno("警告", "目标大小远大于原始大小，可能无法达到预期效果，是否继续？"):
                    return None

            return (size_bytes, tolerance / 100)

        except ValueError:
            messagebox.showerror("错误", "请输入有效的数值")
            return None

    def resize_by_dimension(self, target_size: Tuple[int, int]) -> str:
        """按像素尺寸调整图像"""
        width, height = target_size

        try:
            with Image.open(self.current_image_path) as img:
                # 调整图像大小
                resized_img = img.resize(target_size, resample=Image.Resampling.LANCZOS)

                # 生成新文件名
                output_path = self.get_output_path()

                # 保存调整后的图像
                if output_path.lower().endswith((".jpg", ".jpeg")):
                    resized_img.save(output_path, quality=90)
                else:
                    resized_img.save(output_path)

                return output_path

        except Exception as e:
            raise Exception(f"调整尺寸失败: {str(e)}")

    def find_optimal_quality(self, img, target_size_bytes, tolerance, temp_file):
        """通过迭代找到最佳质量参数，使文件大小在目标范围内"""
        # 初始质量范围
        min_quality = 1
        max_quality = 95
        best_quality = 80  # 初始猜测
        best_size = float('inf')
        iterations = 0

        # 最多尝试10次找到合适的质量
        while iterations < 10:
            iterations += 1
            # 保存临时文件测试大小
            img.save(temp_file, quality=best_quality)
            current_size = os.path.getsize(temp_file)

            # 计算当前大小与目标的差距
            size_ratio = current_size / target_size_bytes

            # 如果在可接受范围内，返回当前质量
            if (1 - tolerance) <= size_ratio <= (1 + tolerance):
                return best_quality

            # 调整质量参数（非线性调整，因为质量和文件大小不是线性关系）
            if size_ratio > 1:  # 当前文件太大，降低质量
                # 大文件需要更大幅度降低质量
                adjust = int(10 * math.log(size_ratio, 2)) + 1
                new_quality = best_quality - adjust
            else:  # 当前文件太小，提高质量
                # 小文件只需小幅提高质量
                adjust = int(5 * math.log(1 / size_ratio, 2)) + 1
                new_quality = best_quality + adjust

            # 确保质量在有效范围内
            new_quality = max(min_quality, min(new_quality, max_quality))

            # 如果质量不再变化，说明无法通过质量调整达到目标
            if new_quality == best_quality:
                break

            best_quality = new_quality
            best_size = current_size

        return best_quality

    def resize_by_filesize(self, target_size_bytes: int, tolerance: float) -> str:
        """按目标文件大小调整图像，确保在容差范围内"""
        # 计算可接受的大小范围
        min_acceptable = int(target_size_bytes * (1 - tolerance))
        max_acceptable = int(target_size_bytes * (1 + tolerance))

        # 如果目标大小大于当前大小，直接复制
        if target_size_bytes >= self.current_image_size:
            output_path = self.get_output_path()
            with Image.open(self.current_image_path) as img:
                img.save(output_path)
            return output_path

        # 创建临时文件用于测试
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_filename = temp_file.name

        try:
            # 对于JPEG格式，尝试通过调整质量来达到目标大小
            file_ext = os.path.splitext(self.current_image_path)[1].lower()
            output_path = self.get_output_path()

            # 如果是PNG等无损格式，先尝试转为JPEG
            if file_ext in (".png", ".bmp", ".gif"):
                messagebox.showinfo("提示", "无损格式图像将转换为JPEG以减小文件大小")
                output_path = os.path.splitext(output_path)[0] + ".jpg"
                file_ext = ".jpg"

            with Image.open(self.current_image_path) as img:
                # 如果是透明图像，处理透明度
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    background = Image.new(img.mode[:-1], img.size, (255, 255, 255))
                    background.paste(img, img.split()[-1])
                    img = background

                current_width, current_height = img.size
                current_scale = 1.0

                # 先尝试只调整质量
                optimal_quality = self.find_optimal_quality(img, target_size_bytes, tolerance, temp_filename)
                img.save(temp_filename, quality=optimal_quality)
                current_size = os.path.getsize(temp_filename)

                # 检查是否在可接受范围内
                if min_acceptable <= current_size <= max_acceptable:
                    img.save(output_path, quality=optimal_quality)
                    return output_path

                # 如果仅调整质量不够，开始调整尺寸
                scale_factor = 1.0
                # 计算需要缩小的比例
                if current_size > max_acceptable:
                    scale_factor = math.sqrt(max_acceptable / current_size) * 0.95
                else:  # current_size < min_acceptable
                    scale_factor = math.sqrt(min_acceptable / current_size) * 1.05

                # 应用缩放
                new_width = int(current_width * scale_factor)
                new_height = int(current_height * scale_factor)

                # 确保尺寸不会太小
                min_dimension = 100
                new_width = max(min_dimension, new_width)
                new_height = max(min_dimension, new_height)

                # 调整尺寸后再次尝试找到最佳质量
                resized_img = img.resize((new_width, new_height), resample=Image.Resampling.LANCZOS)
                optimal_quality = self.find_optimal_quality(resized_img, target_size_bytes, tolerance, temp_filename)
                resized_img.save(output_path, quality=optimal_quality)

                # 最终检查
                final_size = os.path.getsize(output_path)
                if final_size > max_acceptable or final_size < min_acceptable:
                    # 进行最后一次微调
                    size_ratio = final_size / target_size_bytes
                    if size_ratio > 1:
                        new_quality = max(1, optimal_quality - 5)
                    else:
                        new_quality = min(95, optimal_quality + 5)
                    resized_img.save(output_path, quality=new_quality)

            return output_path

        except Exception as e:
            raise Exception(f"调整文件大小失败: {str(e)}")
        finally:
            # 清理临时文件
            if os.path.exists(temp_filename):
                try:
                    os.unlink(temp_filename)
                except:
                    pass

    def get_output_path(self) -> str:
        """生成输出文件路径"""
        dir_name = os.path.dirname(self.current_image_path)
        file_name = os.path.basename(self.current_image_path)
        name_without_ext, ext = os.path.splitext(file_name)
        output_file_name = f"{name_without_ext}_resized{ext}"
        return os.path.join(dir_name, output_file_name)

    def process_image(self):
        """处理图像调整流程"""
        if not self.current_image_path:
            return

        try:
            self.status_var.set("正在处理...")
            self.root.update()  # 更新界面显示

            if self.resize_option.get() == "dimension":
                # 按像素尺寸调整
                target_dimension = self.validate_dimension_input()
                if target_dimension is None:  # 输入无效
                    self.status_var.set("输入无效")
                    return

                output_path = self.resize_by_dimension(target_dimension)
                new_size = os.path.getsize(output_path)
                new_size_str = self.format_size(new_size)

                messagebox.showinfo(
                    "成功",
                    f"图像尺寸调整完成！\n原始尺寸: {self.current_image_dimensions[0]}x{self.current_image_dimensions[1]}px\n"
                    f"目标尺寸: {target_dimension[0]}x{target_dimension[1]}px\n"
                    f"文件大小: {new_size_str}\n保存路径: {output_path}"
                )

            else:
                # 按文件大小调整
                result = self.validate_filesize_input()
                if result is None:  # 输入无效
                    self.status_var.set("输入无效")
                    return

                target_filesize, tolerance = result
                output_path = self.resize_by_filesize(target_filesize, tolerance)
                new_size = os.path.getsize(output_path)
                new_size_str = self.format_size(new_size)
                target_size_str = self.format_size(target_filesize)
                min_acceptable_str = self.format_size(int(target_filesize * (1 - tolerance)))
                max_acceptable_str = self.format_size(int(target_filesize * (1 + tolerance)))

                with Image.open(output_path) as img:
                    new_dimensions = img.size

                messagebox.showinfo(
                    "成功",
                    f"图像文件大小调整完成！\n原始大小: {self.format_size(self.current_image_size)}\n"
                    f"目标大小: {target_size_str} (可接受范围: {min_acceptable_str}-{max_acceptable_str})\n"
                    f"实际大小: {new_size_str}\n"
                    f"像素尺寸: {new_dimensions[0]}x{new_dimensions[1]}px\n保存路径: {output_path}"
                )

            self.status_var.set(f"已保存到: {output_path}")

        except Exception as e:
            self.status_var.set(f"处理失败: {str(e)}")
            messagebox.showerror("错误", f"处理失败！\n错误信息: {str(e)}")


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ImageResizerApp(root)
    root.mainloop()
