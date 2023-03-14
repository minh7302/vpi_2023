from sqlalchemy import create_engine, Table, MetaData
from db_connect import engine, Session, get_db, metadata, Base
# Tạo đối tượng engine kết nối đến cơ sở dữ liệu
engine = create_engine("postgresql://postgres:huy31072002@127.0.0.1/vpi1")

# Tạo đối tượng metadata để tải thông tin bảng
metadata = MetaData(bind=engine)

# Tải thông tin bảng vào đối tượng Table
my_table = Table('cal_curve_value', metadata, autoload=True)

# Tạo đối tượng session để thực hiện các thao tác truy vấn
session = Session()

# Lấy các hàng từ bảng my_table trong khoảng từ hàng 10 đến hàng 20
rows = session.query(my_table).slice(10, 20).all()

# In các hàng được lấy
for row in rows:
    print(row)
