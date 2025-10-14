#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單測試 Tkinter 勾選框統計更新
"""

import tkinter as tk
from tkinter import ttk

def test_checkbutton_update():
    """測試勾選框統計更新"""
    root = tk.Tk()
    root.title("勾選框測試")
    root.geometry("400x300")
    
    # 儲存變數
    project_vars = {}
    
    # 統計標籤
    stats_label = tk.Label(root, text="已選擇: 0 個專案", font=("Arial", 12))
    stats_label.pack(pady=20)
    
    # 更新統計函數
    def update_stats(*args):
        selected_count = sum(1 for var in project_vars.values() if var.get())
        text = f"已選擇: {selected_count} 個專案"
        stats_label.config(text=text)
        print(f"統計更新: {text}")  # 調試輸出
    
    # 創建測試專案
    frame = ttk.Frame(root)
    frame.pack(padx=20, pady=10, fill="both", expand=True)
    
    for i in range(5):
        project_name = f"test_project_{i+1}"
        
        item_frame = ttk.Frame(frame)
        item_frame.pack(fill="x", pady=5)
        
        var = tk.BooleanVar(value=False)
        project_vars[project_name] = var
        
        # 使用 trace 監聽變數變化
        var.trace_add('write', update_stats)
        
        checkbox = ttk.Checkbutton(
            item_frame,
            text=project_name,
            variable=var
        )
        checkbox.pack(side="left")
    
    # 快速選擇按鈕
    btn_frame = ttk.Frame(root)
    btn_frame.pack(pady=10)
    
    def select_all():
        for var in project_vars.values():
            var.set(True)
    
    def deselect_all():
        for var in project_vars.values():
            var.set(False)
    
    ttk.Button(btn_frame, text="全選", command=select_all).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="全不選", command=deselect_all).pack(side="left", padx=5)
    
    print("測試開始 - 請嘗試勾選專案，觀察統計是否更新")
    root.mainloop()


if __name__ == "__main__":
    test_checkbutton_update()
