import json
import os
import requests
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import configparser
from typing import Dict, List
import threading
import time

class VDFTranslatorGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("VDF翻译工具 - 支持Steam所有语言")
        self.root.geometry("900x750")
        
        # 配置文件路径
        self.config_file = os.path.join(os.path.expanduser("~"), ".vdf_translator_config.ini")
        
        # Steam支持的语言代码映射
        self.steam_languages = {
            "arabic": "阿拉伯语",
            "bulgarian": "保加利亚语",
            "schinese": "简体中文",
            "tchinese": "繁体中文",
            "czech": "捷克语",
            "danish": "丹麦语",
            "dutch": "荷兰语",
            "english": "英语",
            "finnish": "芬兰语",
            "french": "法语",
            "german": "德语",
            "greek": "希腊语",
            "hungarian": "匈牙利语",
            "italian": "意大利语",
            "japanese": "日语",
            "koreana": "韩语",
            "norwegian": "挪威语",
            "polish": "波兰语",
            "portuguese": "葡萄牙语",
            "brazilian": "巴西葡萄牙语",
            "romanian": "罗马尼亚语",
            "russian": "俄语",
            "spanish": "西班牙语",
            "latam": "拉丁美洲西班牙语",
            "swedish": "瑞典语",
            "thai": "泰语",
            "turkish": "土耳其语",
            "ukrainian": "乌克兰语",
            "vietnamese": "越南语",
            "indonesian": "印度尼西亚语",
        }
        
        # 翻译状态
        self.translation_status = {}  # 记录每种语言的翻译状态
        self.translation_thread = None
        self.translation_cancelled = False
        
        # 初始化配置
        self.load_config()
        
        self.setup_ui()
        self.load_saved_api_key()
    
    def setup_ui(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # API密钥输入区域
        api_frame = ttk.LabelFrame(main_frame, text="API设置", padding="10")
        api_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(api_frame, text="DeepSeek API密钥:").grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.api_key_var = tk.StringVar(value=self.api_key if hasattr(self, 'api_key') else "")
        self.api_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, width=80, show="*")
        self.api_entry.grid(row=0, column=1, padx=(10, 5), pady=2, sticky=(tk.W, tk.E))
        
        self.show_api_btn = ttk.Button(api_frame, text="显示", command=self.toggle_api_visibility)
        self.show_api_btn.grid(row=0, column=2, padx=(5, 0), pady=2)
        
        self.save_api_btn = ttk.Button(api_frame, text="保存API密钥", command=self.save_api_key)
        self.save_api_btn.grid(row=0, column=3, padx=(10, 0), pady=2)
        
        # 源文件选择区域
        source_frame = ttk.LabelFrame(main_frame, text="源文件", padding="10")
        source_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(source_frame, text="源VDF文件:").grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.source_file_var = tk.StringVar()
        self.source_entry = ttk.Entry(source_frame, textvariable=self.source_file_var, width=80)
        self.source_entry.grid(row=0, column=1, padx=(10, 5), pady=2, sticky=(tk.W, tk.E))
        
        self.browse_btn = ttk.Button(source_frame, text="浏览", command=self.browse_source_file)
        self.browse_btn.grid(row=0, column=2, padx=(5, 0), pady=2)
        
        # 目标语言选择区域
        target_frame = ttk.LabelFrame(main_frame, text="目标语言", padding="10")
        target_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 语言选择列表
        lang_frame = ttk.Frame(target_frame)
        lang_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # 创建滚动框架
        canvas = tk.Canvas(lang_frame, height=200, width=750)
        scrollbar = ttk.Scrollbar(lang_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 语言选择复选框
        self.lang_vars = {}
        row = 0
        col = 0
        for lang_code, lang_name in self.steam_languages.items():
            var = tk.BooleanVar()
            self.lang_vars[lang_code] = var
            cb = ttk.Checkbutton(scrollable_frame, text=f"{lang_name} ({lang_code})", variable=var)
            cb.grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            col += 1
            if col > 3:  # 每行最多4个复选框
                col = 0
                row += 1
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 全选/取消全选按钮
        button_frame = ttk.Frame(target_frame)
        button_frame.grid(row=1, column=0, pady=(10, 0))
        
        ttk.Button(button_frame, text="全选", command=self.select_all_languages).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="取消全选", command=self.deselect_all_languages).grid(row=0, column=1, padx=5)
        
        # 输出目录选择
        output_frame = ttk.LabelFrame(main_frame, text="输出设置", padding="10")
        output_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(output_frame, text="输出目录:").grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.output_dir_var = tk.StringVar(value=os.getcwd())
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_dir_var, width=80)
        self.output_entry.grid(row=0, column=1, padx=(10, 5), pady=2, sticky=(tk.W, tk.E))
        
        self.browse_output_btn = ttk.Button(output_frame, text="浏览", command=self.browse_output_dir)
        self.browse_output_btn.grid(row=0, column=2, padx=(5, 0), pady=2)
        
        # 翻译按钮和进度条
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        self.translate_btn = ttk.Button(control_frame, text="开始翻译", command=self.start_translation_thread)
        self.translate_btn.grid(row=0, column=0, padx=5)
        
        self.cancel_btn = ttk.Button(control_frame, text="取消翻译", command=self.cancel_translation, state=tk.DISABLED)
        self.cancel_btn.grid(row=0, column=1, padx=5)
        
        self.progress = ttk.Progressbar(control_frame, mode='determinate', length=300)
        self.progress.grid(row=0, column=2, padx=20, sticky=(tk.W, tk.E))
        
        # 状态标签
        self.status_label = ttk.Label(control_frame, text="就绪")
        self.status_label.grid(row=1, column=0, columnspan=3, pady=(10, 0))
        
        # 进度和日志区域
        log_frame = ttk.LabelFrame(main_frame, text="翻译日志", padding="10")
        log_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
    
    def load_config(self):
        """加载配置文件"""
        self.config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
            self.api_key = self.config.get('API', 'key', fallback='')
        else:
            self.api_key = ''
    
    def save_config(self):
        """保存配置到文件"""
        if not self.config.has_section('API'):
            self.config.add_section('API')
        self.config.set('API', 'key', self.api_key)
        
        with open(self.config_file, 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)
    
    def load_saved_api_key(self):
        """加载保存的API密钥"""
        if self.api_key:
            self.api_key_var.set('*' * len(self.api_key))  # 显示为星号
    
    def toggle_api_visibility(self):
        """切换API密钥显示/隐藏"""
        current = self.api_key_var.get()
        if current.startswith('*'):
            # 显示实际密钥
            self.api_key_var.set(self.api_key)
            self.show_api_btn.config(text="隐藏")
        else:
            # 隐藏密钥
            self.api_key_var.set('*' * len(current))
            self.show_api_btn.config(text="显示")
    
    def save_api_key(self):
        """保存API密钥"""
        api_key = self.api_key_var.get()
        if api_key.startswith('*'):
            messagebox.showwarning("警告", "请输入实际的API密钥，而不是星号")
            return
        
        if not api_key:
            messagebox.showwarning("警告", "API密钥不能为空")
            return
        
        self.api_key = api_key
        self.save_config()
        messagebox.showinfo("成功", "API密钥已保存")
    
    def browse_source_file(self):
        """浏览选择源文件"""
        filename = filedialog.askopenfilename(
            title="选择源VDF文件",
            filetypes=[("VDF files", "*.vdf"), ("All files", "*.*")]
        )
        if filename:
            self.source_file_var.set(filename)
    
    def browse_output_dir(self):
        """浏览选择输出目录"""
        dirname = filedialog.askdirectory(title="选择输出目录")
        if dirname:
            self.output_dir_var.set(dirname)
    
    def select_all_languages(self):
        """全选语言"""
        for var in self.lang_vars.values():
            var.set(True)
    
    def deselect_all_languages(self):
        """取消全选语言"""
        for var in self.lang_vars.values():
            var.set(False)
    
    def log_message(self, message):
        """在日志区域添加消息"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()
    
    def update_status(self, message):
        """更新状态标签"""
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def extract_tokens_from_vdf(self, vdf_file_path: str) -> tuple:
        """从VDF文件中提取语言和tokens"""
        with open(vdf_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # 简单解析VDF格式
        lines = content.split('\n')
        language = None
        tokens = {}
        current_section = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('"Language"'):
                # 提取语言
                if i + 1 < len(lines):
                    lang_line = lines[i + 1].strip()
                    if lang_line.startswith('"') and lang_line.endswith('"'):
                        language = lang_line[1:-1]
            elif '"Tokens"' in line:
                current_section = 'tokens'
            elif current_section == 'tokens' and line.startswith('"NEW_ACHIEVEMENT_'):
                # 解析token行
                parts = line.split('"')
                if len(parts) >= 4:
                    key = parts[1]
                    value = parts[3] if len(parts) > 3 else ""
                    tokens[key] = value
        
        return language, tokens

    def translate_text(self, text: str, target_language: str) -> str:
        """使用DeepSeek API翻译单个文本"""
        if not text.strip() or self.translation_cancelled:
            return text
            
        # 获取目标语言的本地名称
        target_lang_name = self.steam_languages.get(target_language, target_language)
        
        prompt = f"""
        请将以下文本从中文翻译成{target_lang_name}。
        请保持原文的语气和风格，不要添加额外的解释或说明。
        如果原文是游戏成就名称或描述，请使用适合游戏语境的表达方式。
        原文: {text}
        翻译结果:
        """
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            translated_text = result['choices'][0]['message']['content'].strip()
            # 清理可能的额外文本
            if "翻译结果:" in translated_text:
                translated_text = translated_text.split("翻译结果:")[-1].strip()
            return translated_text
        except Exception as e:
            self.log_message(f"翻译错误: {e}")
            return text

    def translate_tokens(self, tokens: Dict[str, str], target_language: str) -> Dict[str, str]:
        """翻译所有tokens"""
        translated_tokens = {}
        total_tokens = len([v for v in tokens.values() if v.strip()])
        current = 0
        
        self.log_message(f"开始翻译 {total_tokens} 个文本项到 {self.steam_languages.get(target_language, target_language)}...")
        
        for key, value in tokens.items():
            if self.translation_cancelled:
                break
                
            if value.strip():  # 只翻译非空值
                current += 1
                self.log_message(f"翻译进度: {current}/{total_tokens} - {key}")
                translated_value = self.translate_text(value, target_language)
                translated_tokens[key] = translated_value
            else:
                translated_tokens[key] = value  # 保持空值不变
        
        return translated_tokens

    def create_vdf_content(self, language: str, tokens: Dict[str, str]) -> str:
        """创建VDF文件内容"""
        vdf_content = '"lang"\n{\n'
        vdf_content += f'\t"Language"\t"{language}"\n'
        vdf_content += '\t"Tokens"\n\t{\n'
        
        for key, value in tokens.items():
            vdf_content += f'\t\t"{key}"\t"{value}"\n'
        
        vdf_content += '\t}\n}'
        return vdf_content

    def start_translation_thread(self):
        """启动翻译线程"""
        if self.translation_thread and self.translation_thread.is_alive():
            messagebox.showwarning("警告", "翻译已在进行中，请等待完成或取消当前任务")
            return
        
        self.translation_thread = threading.Thread(target=self.start_translation, daemon=True)
        self.translation_thread.start()

    def start_translation(self):
        """开始翻译过程"""
        # 验证API密钥
        api_key = self.api_key_var.get()
        if api_key.startswith('*'):
            messagebox.showerror("错误", "请先显示并验证API密钥")
            return
        
        if not api_key:
            messagebox.showerror("错误", "请先输入API密钥")
            return
        
        # 验证源文件
        source_file = self.source_file_var.get()
        if not source_file or not os.path.exists(source_file):
            messagebox.showerror("错误", "请选择有效的源VDF文件")
            return
        
        # 获取选中的语言
        selected_languages = [lang for lang, var in self.lang_vars.items() if var.get()]
        if not selected_languages:
            messagebox.showerror("错误", "请至少选择一种目标语言")
            return
        
        # 验证输出目录
        output_dir = self.output_dir_var.get()
        if not output_dir or not os.path.exists(output_dir):
            messagebox.showerror("错误", "请选择有效的输出目录")
            return
        
        # 重置翻译状态
        self.translation_cancelled = False
        self.translation_status = {lang: "pending" for lang in selected_languages}
        
        # 启用取消按钮
        self.root.after(0, lambda: self.cancel_btn.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.translate_btn.config(state=tk.DISABLED))
        
        try:
            # 提取源文件信息
            source_lang, tokens = self.extract_tokens_from_vdf(source_file)
            self.root.after(0, lambda: self.log_message(f"源文件语言: {source_lang}"))
            self.root.after(0, lambda: self.log_message(f"找到 {len(tokens)} 个翻译项"))
            
            total_languages = len(selected_languages)
            completed_languages = 0
            
            # 为每个选中的语言翻译
            for i, target_lang in enumerate(selected_languages):
                if self.translation_cancelled:
                    self.root.after(0, lambda: self.log_message("翻译已取消"))
                    break
                
                self.root.after(0, lambda i=i, target_lang=target_lang: 
                               self.update_status(f"正在翻译到 {self.steam_languages[target_lang]} ({i+1}/{total_languages})"))
                self.root.after(0, lambda target_lang=target_lang: 
                               self.log_message(f"\n开始翻译到 {self.steam_languages[target_lang]}..."))
                
                try:
                    # 翻译tokens
                    translated_tokens = self.translate_tokens(tokens, target_lang)
                    
                    # 如果翻译被取消，跳出循环
                    if self.translation_cancelled:
                        self.translation_status[target_lang] = "cancelled"
                        break
                    
                    # 创建VDF内容
                    vdf_content = self.create_vdf_content(target_lang, translated_tokens)
                    
                    # 生成输出文件名
                    base_name = os.path.splitext(os.path.basename(source_file))[0]
                    # 提取基础ID (假设格式为 "数字_loc_语言")
                    try:
                        base_id = base_name.split('_loc_')[0]
                    except IndexError:
                        self.log_message("源文件名格式不正确，无法提取基础ID")
                        continue  # 跳过当前语言，继续下一个

                    output_filename = f"{base_id}_loc_{target_lang}.vdf"
                    output_path = os.path.join(output_dir, output_filename)
                    
                    # 保存文件
                    with open(output_path, 'w', encoding='utf-8', newline='\n') as file:
                        file.write(vdf_content)
                    
                    self.translation_status[target_lang] = "completed"
                    self.root.after(0, lambda path=output_path, lang=target_lang: 
                                   self.log_message(f"翻译完成! 文件已保存到: {path}"))
                    
                except Exception as e:
                    self.translation_status[target_lang] = "failed"
                    self.root.after(0, lambda e=e, lang=target_lang: 
                                   self.log_message(f"翻译到 {self.steam_languages[lang]} 时出错: {e}"))
                    continue  # 跳过当前语言，继续下一个
                
                completed_languages += 1
                progress = (completed_languages / total_languages) * 100
                self.root.after(0, lambda p=progress: self.set_progress_value(p))
            
            # 翻译完成后的处理
            if not self.translation_cancelled:
                failed_languages = [lang for lang, status in self.translation_status.items() if status == "failed"]
                cancelled_languages = [lang for lang, status in self.translation_status.items() if status == "cancelled"]
                completed_languages = [lang for lang, status in self.translation_status.items() if status == "completed"]
                
                self.handle_translation_summary(failed_languages, cancelled_languages, completed_languages, total_languages)
        
        except Exception as e:
            self.root.after(0, lambda e=e: self.log_message(f"翻译过程中出错: {e}"))
            self.root.after(0, lambda e=e: messagebox.showerror("错误", f"翻译过程中出错: {e}"))
        finally:
            # 恢复按钮状态
            self.root.after(0, lambda: self.cancel_btn.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.translate_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.update_status("完成"))
            self.root.after(0, lambda: self.set_progress_value(0))  # 直接使用方法重置进度条

    def cancel_translation(self):
        """取消翻译过程"""
        self.translation_cancelled = True
        self.root.after(0, lambda: self.log_message("正在取消翻译..."))
        self.root.after(0, lambda: self.update_status("取消中..."))

    def run(self):
        """运行GUI应用"""
        self.root.mainloop()

    def handle_translation_summary(self, failed_languages, cancelled_languages, completed_languages, total_languages):
        summary_msg = f"\n翻译完成! 总计: {total_languages}, 成功: {len(completed_languages)}, 失败: {len(failed_languages)}, 取消: {len(cancelled_languages)}"
        self.root.after(0, lambda: self.log_message(summary_msg))
        
        if failed_languages:
            failed_names = [self.steam_languages[lang] for lang in failed_languages]
            self.root.after(0, lambda: self.log_message(f"失败的语言: {', '.join(failed_names)}"))
        
        if completed_languages:
            completed_names = [self.steam_languages[lang] for lang in completed_languages]
            self.root.after(0, lambda: self.log_message(f"成功翻译的语言: {', '.join(completed_names)}"))
        
        self.root.after(0, lambda: messagebox.showinfo("完成", summary_msg))

    def set_progress_value(self, value):
        self.progress['value'] = value

def main():
    app = VDFTranslatorGUI()
    app.run()

if __name__ == "__main__":
    main()
