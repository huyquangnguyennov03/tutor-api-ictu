"""
LLM Service - Tích hợp OpenAI với logic giống hệt file app.py gốc
"""
import logging
import re
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load biến môi trường
load_dotenv()

logger = logging.getLogger(__name__)

class LLMService:
    """Service tích hợp OpenAI LLM"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def generate_intervention_recommendation(self, student_data, error_messages, common_error_types):
        """
        Tạo đề xuất can thiệp bằng OpenAI - GIỐNG HỆT LOGIC FILE GỐC
        
        Args:
            student_data (dict): Dữ liệu sinh viên
            error_messages (list): Danh sách lỗi
            common_error_types (list): Loại lỗi phổ biến
            
        Returns:
            str: Đề xuất can thiệp
        """
        # GIỐNG HỆT PROMPT TRONG FILE GỐC
        prompt = f"""
        Bạn là một trợ lý AI hỗ trợ giáo dục, chuyên cung cấp phân tích lỗi và đề xuất cải thiện chi tiết, ngắn gọn, dễ hiểu bằng tiếng Việt, dành cho sinh viên học lập trình.

        Dưới đây là thông tin sinh viên:
        - GPA: {student_data.get('gpa', 'N/A')}
        - Tiến độ học tập: {student_data.get('progressrate', 'N/A')}%
        - Điểm Bloom: {student_data.get('bloomscore', 'N/A')}
        - Số lần nộp bài: {student_data.get('num_submissions', 'N/A')}

        ## Danh sách tất cả lỗi và cảnh báo của sinh viên (cần phân tích):
        {chr(10).join([f'- {error}' for error in error_messages]) if error_messages else 'Không có lỗi hoặc cảnh báo cụ thể'}

        ## Các lỗi phổ biến trong khóa học (chỉ tham khảo để liên hệ nếu có liên quan):
        {', '.join(common_error_types) if common_error_types else 'Không có lỗi chung'}

        ---

        ### 🎯 Yêu cầu phản hồi:
        1. **Phân tích chi tiết từng lỗi và cảnh báo của sinh viên** (dựa trên danh sách trên), **không được bỏ sót bất kỳ mục nào**.
        2. Mỗi lỗi hãy sử dụng định dạng markdown sau:

        ---

        ## Lỗi [số thứ tự]: [Tên lỗi]  
        ### 1. Phân tích lỗi  
        - Mô tả lỗi: [Mô tả ngắn gọn lỗi xảy ra trong hoàn cảnh nào, biểu hiện ra sao – tối đa 2-3 câu].  
        - Nguyên nhân: [Lý do sinh viên mắc lỗi, ví dụ: thiếu hiểu biết về cú pháp, nhầm lẫn logic – tối đa 2 câu].  

        ### 2. Đề xuất cải thiện  
        - Cách khắc phục: [Hướng dẫn cụ thể, ngắn gọn, từng bước nếu cần – tối đa 3-4 câu].  
        - Ví dụ minh họa (nếu áp dụng):  
        ```c
        [Đoạn mã minh họa cách sửa lỗi. Ưu tiên dùng C/C++ trừ khi lỗi thuộc ngôn ngữ khác. Nếu không có ví dụ mã, giải thích lý do.]
        ```

        ---

        3. Nếu không có lỗi hoặc cảnh báo cụ thể, cung cấp đề xuất chung để cải thiện hiệu suất học tập, tập trung vào kỹ năng lập trình, với định dạng:  
        ## Đề xuất cải thiện chung  
        - Mô tả: [Mô tả ngắn gọn tình trạng học tập hiện tại dựa trên GPA, tiến độ, điểm Bloom].  
        - Đề xuất: [Hướng dẫn cụ thể, ví dụ: cải thiện kỹ năng debug, đọc tài liệu – tối đa 3-4 câu].  

        **Ví dụ phản hồi**:
        ## Lỗi 1: Lỗi hàm: Truyền tham số không đúng kiểu  
        ### 1. Phân tích lỗi  
        - Mô tả lỗi: Lỗi xảy ra khi truyền tham số kiểu chuỗi vào hàm yêu cầu kiểu số nguyên, gây lỗi biên dịch.  
        - Nguyên nhân: Sinh viên chưa nắm rõ cách khai báo và sử dụng kiểu dữ liệu trong C/C++.  

        ### 2. Đề xuất cải thiện  
        - Cách khắc phục: Kiểm tra kiểu dữ liệu của tham số trước khi truyền vào hàm, đảm bảo khớp với định nghĩa hàm.  
        - Ví dụ minh họa:  
        ```c
        // Sai:
        void tinhTong(int a, int b) {{ printf("%d", a + b); }}
        tinhTong("10", 20); // Lỗi kiểu dữ liệu
        // Đúng:
        tinhTong(10, 20);
        ```

        ## Đề xuất cải thiện chung  
        - Mô tả: Sinh viên có GPA cao và tiến độ tốt, nhưng cần cải thiện kỹ năng debug.  
        - Đề xuất: Thực hành debug bằng cách sử dụng công cụ như gdb và đọc tài liệu về cú pháp C/C++.

        Đảm bảo trả lời bằng tiếng Việt, ngắn gọn, rõ ràng, và sử dụng ngôn ngữ lập trình C/C++ cho ví dụ minh họa trừ khi lỗi yêu cầu ngôn ngữ khác. Phản hồi phải bao gồm tất cả lỗi được liệt kê và tuân thủ nghiêm ngặt định dạng markdown.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Bạn là một trợ lý AI hỗ trợ giáo dục, chuyên cung cấp phân tích lỗi và đề xuất cải thiện chi tiết và dễ hiểu bằng tiếng Việt."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Lỗi khi gọi OpenAI API: {str(e)}")
            return "Không thể tạo đề xuất can thiệp do lỗi hệ thống."
    
    def parse_intervention_suggestions(self, recommendation, studentid, error_messages):
        """
        Phân tích đề xuất thành suggestions - GIỐNG HỆT LOGIC FILE GỐC
        
        Args:
            recommendation (str): Đề xuất từ LLM
            studentid (str): ID sinh viên
            error_messages (list): Danh sách lỗi
            
        Returns:
            list: Danh sách suggestions đã phân tích
        """
        error_sections = re.split(r'## Lỗi \d+:', recommendation)[1:]
        parsed_suggestions = []

        for i, section in enumerate(error_sections, 1):
            name_match = re.match(r'([^\n]+)\n', section)
            error_name = name_match.group(1).strip() if name_match else f"Lỗi {i}"
            
            parts = re.split(r'### \d+\.', section)
            error_analysis = parts[1].strip() if len(parts) > 1 else "Không có phân tích chi tiết"
            improvement_suggestion = parts[2].strip() if len(parts) > 2 else "Không có đề xuất chi tiết"

            parsed_suggestions.append({
                'id': f"error_{i}_{studentid}",
                'title': f"Đề xuất cải thiện cho {error_name}",
                'content': f"## {error_name}\n{error_analysis}\n### Đề xuất cải thiện\n{improvement_suggestion}",
                'type': 'info'
            })

        if not error_messages:
            general_section = re.search(r'## Đề xuất cải thiện chung.*?$(.*?)(?=(##|$))', recommendation, re.DOTALL)
            general_content = general_section.group(1).strip() if general_section else recommendation
            parsed_suggestions.append({
                'id': f"general_{studentid}",
                'title': "Đề xuất cải thiện chung",
                'content': f"## Đề xuất cải thiện chung\n{general_content}",
                'type': 'info'
            })

        return parsed_suggestions
    
    def evaluate_llm_scenarios(self, scenarios):
        """
        Đánh giá LLM với các kịch bản khác nhau
        
        Args:
            scenarios (list): Danh sách kịch bản test
            
        Returns:
            list: Kết quả đánh giá
        """
        results = []
        
        for scenario in scenarios:
            try:
                recommendation = self.generate_intervention_recommendation(
                    {
                        'gpa': scenario['gpa'],
                        'progressrate': scenario['progressrate'],
                        'bloomscore': scenario['bloomscore'],
                        'num_submissions': scenario['num_submissions']
                    },
                    scenario['errors'],
                    []
                )
                
                results.append({
                    'scenario': scenario['name'],
                    'recommendation': recommendation
                })
            except Exception as e:
                logger.error(f"Lỗi khi đánh giá kịch bản {scenario['name']}: {str(e)}")
                results.append({
                    'scenario': scenario['name'],
                    'recommendation': f"Lỗi: {str(e)}"
                })
        
        return results