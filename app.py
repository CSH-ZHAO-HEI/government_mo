import json
import random
import os

class StudySystem:
    def __init__(self, filename="data_store.json"):
        self.filename = filename
        self.data = self.load_data()

    def load_data(self):
        """讀取數據，若檔案不存在則回傳空列表"""
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def save_data(self):
        """儲存目前所有題目與錯誤次數"""
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    def run_quiz(self, question_pool, mode_name):
        """通用的測驗邏輯"""
        if not question_pool:
            print(f"\n[提示] 目前{mode_name}沒有題目可供測試。")
            return

        print(f"\n=== {mode_name}模式 (輸入 'exit' 退出測驗) ===")
        quiz_items = list(question_pool)
        random.shuffle(quiz_items)

        for q in quiz_items:
            print(f"\n題目: {q['content']}")
            user_ans = input("你的答案: ").strip()

            if user_ans.lower() == 'exit':
                break
            
            if user_ans == q['answer']:
                print("✅ 正確！")
            else:
                print(f"❌ 錯誤！正確答案是: {q['answer']}")
                # 更新原始數據中的錯誤次數
                for item in self.data:
                    if item['id'] == q['id']:
                        item['wrong_count'] += 1
                self.save_data()
        print("\n=== 測驗結束 ===")

    def wrong_book_management(self):
        """模式二：錯題本管理 (包含查看、新增、刪除)"""
        while True:
            print("\n--- 錯題本管理介面 ---")
            print("1. 查看所有題目與錯誤次數")
            print("2. 新增題目")
            print("3. 刪除題目")
            print("4. 返回主選單")
            
            choice = input("請選擇操作 (1-4): ")
            
            if choice == '1':
                if not self.data:
                    print("目前沒有任何題目。")
                else:
                    print("\n{:<5} {:<20} {:<15} {:<5}".format("ID", "內容", "答案", "錯誤次數"))
                    for q in self.data:
                        print("{:<5} {:<20} {:<15} {:<5}".format(q['id'], q['content'], q['answer'], q['wrong_count']))
            
            elif choice == '2':
                content = input("請輸入新題目內容: ")
                answer = input("請輸入正確答案: ")
                new_id = max([q['id'] for q in self.data], default=0) + 1
                self.data.append({
                    "id": new_id,
                    "content": content,
                    "answer": answer,
                    "wrong_count": 0
                })
                self.save_data()
                print("題目已成功添加！")
            
            elif choice == '3':
                try:
                    target_id = int(input("請輸入要刪除的題目 ID: "))
                    original_len = len(self.data)
                    self.data = [q for q in self.data if q['id'] != target_id]
                    if len(self.data) < original_len:
                        self.save_data()
                        print(f"ID {target_id} 的題目已刪除。")
                    else:
                        print("找不到該 ID。")
                except ValueError:
                    print("請輸入有效的數字 ID。")
            
            elif choice == '4':
                break
            else:
                print("無效選擇。")

    def main_menu(self):
        """主程式入口"""
        while True:
            print("\n========================")
            print("    學習與錯題管理系統")
            print("========================")
            print("1. 隨機測驗 (全部題目)")
            print("2. 錯題本 (查看/新增/刪除)")
            print("3. 隨機錯題本測驗 (僅限錯過的題)")
            print("4. 退出系統")
            
            choice = input("請選擇模式 (1-4): ")
            
            if choice == '1':
                self.run_quiz(self.data, "隨機測驗")
            elif choice == '2':
                self.wrong_book_management()
            elif choice == '3':
                # 篩選錯誤次數 > 0 的題目
                wrong_pool = [q for q in self.data if q['wrong_count'] > 0]
                self.run_quiz(wrong_pool, "隨機錯題本測驗")
            elif choice == '4':
                print("系統已退出，再見！")
                break
            else:
                print("無效選擇，請重新輸入。")

if __name__ == "__main__":
    system = StudySystem()
    system.main_menu()
