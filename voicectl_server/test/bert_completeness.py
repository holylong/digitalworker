import os
from transformers import pipeline

# ================= 配置区域 =================
LOCAL_MODEL_PATH = "/home/skyer/WorkStation/dataset/DeBERTa-v3-base-mnli-fever-anli" 
# ===========================================

def test_bert_completeness():
    print(f"正在从本地加载模型: {LOCAL_MODEL_PATH} ...")
    
    if not os.path.exists(LOCAL_MODEL_PATH):
        print(f"\n[错误] 找不到本地模型目录：{LOCAL_MODEL_PATH}")
        return

    try:
        classifier = pipeline(
            "zero-shot-classification", 
            model=LOCAL_MODEL_PATH,
        )
        print("模型加载成功！\n")
    except Exception as e:
        print(f"\n[错误] 模型加载失败: {e}")
        return

    # --- 关键修改 1：使用更具描述性的标签 ---
    # 模型很难理解抽象的“完整”，但能理解“包含了完整的意图”
    candidate_labels = [
        "这是一个包含了完整意图的句子", 
        "这是一个未说完或只有动词的短语"
    ]

    # --- 关键修改 2：修改假设模版 ---
    # 默认模版通常是 "This text is about {}."
    # 我们改为 "This text is {}." 或中文 "这句话是 {}。"
    # 这会帮助模型判断句子的“状态”，而不是“主题”
    template = "这句话是 {}。" 

    # 测试用例
    test_cases = [
        "帮我打开",           
        "帮我打开客厅的灯",   
        "我想听",            
        "今天天气怎么样",    
        "导航到",            
        "导航到北京天安门",   
        "停",                
        "把那个... 那个...", 
        "播放",              
        "播放周杰伦的稻香"    
    ]

    print("="*60)
    print("{:<25} | {:<15} | {:<10}".format("输入文本", "判定结果", "置信度"))
    print("="*60)

    for text in test_cases:
        # --- 关键修改 3：传入模版 ---
        result = classifier(text, candidate_labels, hypothesis_template=template)
        
        predicted_label = result['labels'][0]
        confidence = result['scores'][0]
        
        # 根据新的标签内容进行简单的后处理，方便打印
        if "完整" in predicted_label:
            status = "✅ 完整"
            final_label = "完整"
        else:
            status = "⏳ 不完整"0
            final_label = "不完整"
            
        print("{:<25} | {:<15} | {:.2f}%".format(text, status, confidence * 100))

if __name__ == "__main__":
    test_bert_completeness()