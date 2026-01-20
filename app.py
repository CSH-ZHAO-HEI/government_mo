import json
import random
import os

class WrongQuestionBook:
    def __init__(self, filename="wrong_book.json"):
        self.filename = filename
        self.questions = self.load_data()

    def load_data(self):
        """從檔案讀取數據"""
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def save_data(self):
        """儲存數據到檔案"""
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.questions, f, ensure_ascii=False, indent=4)

    def add_question(self):
        """新增題目"""
        q_text = input("請輸入題目內容: ")
        answer = input("請輸入正確答案: ")
        # 初始化錯誤次數為 0
        self.questions.append({
            "id": len(self.questions) + 1,
            "content": q_text,
            "answer": answer,
            "wrong_count": 0
        })
        self.save_data()
        print("--- 題目已添加 ---")

    def view_book(self):
        """查看錯題本"""
        if not self.questions:
            print("\n目前錯題本是空的。")
            return
        
        print("\n--- 錯題本列表 ---")
        for q in self.questions:
            print(f"ID: {q['id']} | 題目: {q['content']} | 答案: {q['answer']} | 錯誤次數: {q['wrong_count']}")
        print("------------------")

    def delete_question(self):
        """刪除錯題"""
        self.view_book()
        if not self.questions: return
        
        try:
            target_id = int(input("請輸入要刪除的題目 ID: "))
            # 根據 ID 過濾
            original_count = len(self.questions)
            self.questions = [q for q in self.questions if q['id'] != target_id]
            
            if len(self.questions) < original_count:
                self.save_data()
                print(f"ID {target_id} 的題目已刪除。")
            else:
                print("找不到該 ID。")
        except ValueError:
            print("請輸入有效的數字 ID。")

    def quiz_mode(self):
        """隨機測驗模式"""
        if not self.questions:
            print("\n錯題本內沒有題目，請先添加。")
            return

        print("\n=== 進入隨機測驗模式 (輸入 'exit' 退出) ===")
        # 隨機打亂題目順序
        quiz_list = self.questions.copy()
        random.shuffle(quiz_list)

        for q in quiz_list:
            print(f"\n題目: {q['content']}")
            user_ans = input("你的答案: ").strip()

            if user_ans.lower() == 'exit':
                break
            
            if user_ans == q['answer']:
                print("✅ 正確！")
            else:
                # 答錯則增加對應題目的錯誤次數
                print(f"❌ 錯誤！正確答案是: {q['answer']}")
                for item in self.questions:
                    if item['id'] == q['id']:
                        item['wrong_count'] += 1
                self.save_data()
        
        print("\n=== 測驗結束 ===")

def main():
    book = WrongQuestionBook()
    
    while True:
        print("\n--- 錯題管理系統 ---")
        print("1. 新增題目")
        print("2. 查看所有題目 (及錯誤次數)")
        print("3. 刪除題目")
        print("4. 開始隨機測驗")
        print("5. 退出程式")
        
        choice = input("請選擇功能 (1-5): ")
        
        if choice == '1':
            book.add_question()
        elif choice == '2':
            book.view_book()
        elif choice == '3':
            book.delete_question()
        elif choice == '4':
            book.quiz_mode()
        elif choice == '5':
            print("程式已退出。")
            break
        else:
            print("無效輸入，請重試。")

if __name__ == "__main__":
    main()
