"""学生账号查看本人数据：登录名未必等于学籍学号，优先按绑定的 students.id 过滤。"""

from app.models.student import Student
from app.models.user import User


def student_own_student_clause(current_user: User):
    """在已 JOIN Student 的查询上，限定为当前学生本人。"""
    if current_user.linked_student_id is not None:
        return Student.id == current_user.linked_student_id
    return Student.student_id == current_user.username
