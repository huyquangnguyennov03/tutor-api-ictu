"""
Helper functions
"""

def classify_student(gpa):
    """
    Phân loại sinh viên dựa trên GPA
    
    Args:
        gpa (float): Điểm GPA của sinh viên
        
    Returns:
        str: Phân loại sinh viên
    """
    if gpa >= 3.5:
        return 'ĐẠT CHỈ TIÊU'
    elif gpa >= 3.0:
        return 'KHÁ'
    elif gpa >= 2.0:
        return 'CẦN CẢI THIỆN'
    else:
        return 'NGUY HIỂM'